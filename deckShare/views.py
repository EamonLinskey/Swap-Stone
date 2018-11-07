from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.urls import reverse 
from django.http import (HttpResponse, HttpResponseRedirect, 
						HttpResponseNotAllowed, HttpRequest)
from django.utils.html import escape
from django.db.models import Q, Max
from requests_oauthlib import OAuth2Session
from hearthstone.deckstrings import Deck as DeckHearth
from hearthstone.enums import FormatType
from .models import Deck, Profile, Match
import re
import os
import datetime
import time
import json
import requests

# globals
DECK_SIZE = 30
API_TIMEOUT_SECS = 120
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
SCOPE = ['collection:read']
HSR_AUTHORIZATION_URL = 'https://hsreplay.net/oauth2/authorize/'
HSR_TOKEN_URL = 'https://hsreplay.net/oauth2/token/'
HSR_ACCOUNT_URL = 'https://hsreplay.net/api/v1/account/'
MAX_USER_SEARCHES = 100
#CLASSES = {heroes}


#print(Profile.objects.all())
#mostRecentActivity = Profile.objects.all().aggregate(Max('latestActivity'))
#print(mostRecentActivity)

# Used to make teh full colllection json file locally
# should only be run when new cards are added to update file
def makeFullCollFile(fileName):
	# Update to the version number corresponing to the most recent release
	version = "25770"

	dataResponse = requests.get(f"https://api.hearthstonejson.com/v1/{version}/enUS/cards.collectible.json")
	fullCollectionRaw = json.loads(dataResponse.text)
    
	with open(fileName, 'w') as outfile:
		json.dump(fullCollectionRaw, outfile)

# Builds a dictionary of all cards from the hearthstone json file with their classes and names by ids
def buildFullColl(datafile):
    
    # Read the API json file of cards
    f = open(datafile, "r")
    fullCollectionRaw = json.loads(f.read())
    
    # The API for some reason strores the Heros as cards but for my purposes they should not be included
    # so I filtered them into a differernt dict
    fullCollectionClean = {}
    heroes = {}
    for card in fullCollectionRaw:
        if card['id'][0:4] != "HERO":
            fullCollectionClean[card['dbfId']] = {'name': card['name'],'class': card['cardClass']}
        else:
            heroes[card['dbfId']] = {'name': card['name'],'class': card['cardClass']}
    return fullCollectionClean, heroes

def IsValidDeckCode(deckString):
    # Makes sure deckstring is syntactically valid
	try:
		deck = DeckHearth.from_deckstring(deckString)
		#print(deck.cards)
	except:
		#print("false 1")
		return False
    
    # Checks if deck length is equal to the Standard Hearthstone decklength
	if sum([int(cardNum) for _,cardNum in deck.cards]) != DECK_SIZE:
		#print("false 2")
		return False

    # Checks if each "card" corresponds to an actual Hearthstone card
	classes = []
	for cardId,_ in deck.cards:
		if cardId not in FULL_COLLECTION:
			#print("false 3")
			#print(cardId)
			return False
		# creates a list of classes used to make a deck
		if FULL_COLLECTION[cardId]["class"] not in classes and FULL_COLLECTION[cardId]["class"] != "NEUTRAL":
			classes += [FULL_COLLECTION[cardId]["class"]]
    
	# Makes sure only one class (and neutrals) can be in a deck (It can also be all neutrals)
	if len(classes) <= 1:
		return True
	#print("false 4")
	return False

def isMakable(deck, profile):
	try:
		deckObj = DeckHearth.from_deckstring(deck.deckString)
		for cardId,count in deckObj.cards:
			if str(cardId) in profile.collection:
				if sum(profile.collection[str(cardId)]) < count:
					return False
			else:
				return False
		return True
	except:
		return False




# Returns time diffrenece from last update in seconds
def timeDiff(request):
	return int(time.time()) - int(request.user.profile.time)

def getUserData(request, oauth):
	# Get user data
	userData = oauth.get(HSR_ACCOUNT_URL).json()
	accountInfo = userData["blizzard_accounts"][0]
	accountHi, accountLo = accountInfo["account_hi"],accountInfo["account_lo"]
	
	# Fetch collection
	collectionUrl = f"https://api.hsreplay.net/v1/collection/?account_hi={accountHi}&account_lo={accountLo}"
	collection = oauth.get(collectionUrl).json()

	# Save relevent user data
	profile = request.user.profile
	profile.blizzTag = userData["battletag"]
	profile.token = oauth.token
	profile.collection = collection["collection"]
	profile.lastUpdateCollection = str(datetime.datetime.now())
	profile.time = time.time()
	request.user.save()

def updateActivity(request):
	userActive = request.user.profile.latestActivity
	maxActive = Profile.objects.all().aggregate(Max('latestActivity'))['latestActivity__max']
	if userActive != maxActive:
		userActive = maxActive + 1
		request.user.save()

def authorizeHSRAccess(request):
	# set up OAuth2 Session
	oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
	authorization_url, state = oauth.authorization_url(HSR_AUTHORIZATION_URL)

	# Save state for validation later
	request.user.profile.state = state
	request.user.save()

	# rediredct to HSReplay for authorization
	return redirect(authorization_url)
	

def refreshHSRAccess(request):
	# set up OAuth2 Session
	token = request.user.profile.token
	oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE, 
							token=token)
	authorization_url, state = oauth.authorization_url(HSR_AUTHORIZATION_URL)
	clientInfo = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET}
	
	try:
		# Update collection with new token
		token = oauth.refresh_token(HSR_TOKEN_URL, **clientInfo)
		getUserData(request, oauth)
		clearMatches(request.user)
		recentActive = Profile.objects.all().aggregate(Max('latestActivity'))['latestActivity__max'] - MAX_USER_SEARCHES
		recentActOwners = Profile.objects.filter(latestActivity__gte= recentActive)
		for deck in request.user.profile.wishList.objects.all():
			findMatches(request, deck, recentActOwners)
		return render(request, "deckShare/updatedCollection.html", {"message": "You have sucessfully updated your collection"})
	except:
		# If access was revoked this tries to reauthorize
		return authorizeHSRAccess(request)

# More globals that require a function to be set
FULL_COLLECTION, HEROES = buildFullColl('static/deckShare/json/FullCollection.json')
#print(FULL_COLLECTION)

# Create your views here.
def index(request):
	return render(request, "deckShare/index.html")

@login_required
def profile(request):
	#deleteAllMatches()
	#clearMatches(request.user)
	# matchInfo = Match.objects.all()
	# print(f"the matchs are {matchInfo}")
	# print(f"the match is {matchInfo[0]}")
	# print(f"the match info is {matchInfo[0].deck1.id}")
	return render(request, "deckShare/profile.html", {"numDecks": len(request.user.profile.wishList.all())})

def signIn(request):
	if request.user.is_authenticated:
		updateActivity(request)
		return HttpResponseRedirect(reverse("profile"))
	else:
		return render(request, "deckShare/signIn.html")

def signOut(request):
	if request.user.is_authenticated:
		logout(request)
	return HttpResponseRedirect(reverse("signIn"))

def signedIn(request):
	if (request.method == "POST"):
		password, username = "", ""

		if request.POST["password"]:
			password = request.POST["password"]
		if request.POST["username"]:
			username= request.POST["username"]
		try:
			user = authenticate(request, username=username, password=password)
			login(request, user)
			updateActivity(request)
			return HttpResponseRedirect(reverse("profile"))
		except:
			return render(request, "deckShare/signIn.html", 
							{"message": "Invalid Credentials",
							 "username": username})
	else:
		return HttpResponseRedirect(reverse("profile"))


def register(request):
	if request.user.is_authenticated:
		updateActivity(request)
		return HttpResponseRedirect(reverse("profile"))
	else:
		# This temporarily disables new accounts so I can test online 
		# without anyone being able to make an account
		return HttpResponseRedirect(reverse("index"))
		#return render(request, "deckShare/register.html")

def registered(request):
	if (request.method == "POST"):
		# Set variables from form
		email = request.POST["email"]
		username = request.POST["username"]
		confirmPassword = request.POST["confirmPassword"]
		password = request.POST["password"]
		
		# Validate inputs
		if (email == "" or username == "" or password == "" or 
		confirmPassword == ""):
			return render(request, "deckShare/register.html", 
						{"message": "Fields cannot be blank",
						"email": email, "username": username})
		if (len(User.objects.filter(username=username)) > 0):
			return render(request, "deckShare/register.html", 
						{"message": "That username is taken",
						"email": email, "username": username})
		if (len(User.objects.filter(email=email))>0):
			return render(request, "deckShare/register.html", 
						{"message": "That email is taken",
						"email": email, "username": username})
		if (not re.match(r"[^@]+@[^@]+\.[^@]+", email)):
			return render(request, "deckShare/register.html", 
						{"message": "You must input valid email",
						"email": email, "username": username})
		if (confirmPassword != password):
			return render(request, "deckShare/register.html", 
						{"message": "Passwords did not match",
						"email": email, "username": username})
		else:
			try: 
				# Create new user
				user = User.objects.create_user(username=username, email=email, 
												password=password)
				login(request, user)
				updateActivity(request)
				return HttpResponseRedirect(reverse("profile"))
			except:
				return render(request, "deckShare/register.html", 
							{"message": "An unknown error occured",
							"email": email, "username": username})	
	else:
		return HttpResponseRedirect(reverse("index"))

def findMatches(request, newDeck, recentActOwners):
	matches = []
	# Looks through all owners to see who's collections can make the new deck
	for owner in recentActOwners:
		if newDeck.owner != owner and isMakable(newDeck, owner):
			# Looks through matching owners decks to see if current user 
			# can make any of their decks with their own collections to complete the match
			for deck in owner.wishList.all():
				if isMakable(deck, newDeck.owner):
					#Match.objects.createMatch(deck, newDeck)
					matches.append(Match(deck1=deck, deck2=newDeck))
	
	# Create new matches and associate them with the user
	matchObjs = Match.objects.bulk_create(matches)
	request.user.profile.matches.add(*matchObjs)

@login_required
def wishList(request):
	context = {}

	if 'deckToDelete' in request.POST:
		return deleteFromWishlist(request)

	if ('deckName' not in request.POST or  'deckCode' not in request.POST):
			context["wishList"] = request.user.profile.wishList.all()
			return render(request, "deckShare/wishList.html", context)
	else:
		deckName, deckCode = escape(request.POST.get("deckName")), escape(request.POST.get("deckCode"))
		if IsValidDeckCode(deckCode):
			if len(deckName) > 50 or len(deckName) <= 0:
				context["message"] = "Your deck Name must be less than 50 characters and cannot be blank"
			else:
				wishList = request.user.profile.wishList.all()
				if len(wishList.filter(deckString=deckCode)) == 0:
					deckObj = DeckHearth.from_deckstring(deckCode)
					heroId = deckObj.heroes[0]
					deckClass = HEROES[heroId]["class"].capitalize()
					deck = Deck.objects.createDeck(deckName, deckCode, deckClass, request.user.profile)
					deck.save()	
					request.user.profile.wishList.add(deck)
					request.user.save()
					updateActivity(request)
					recentActive = Profile.objects.all().aggregate(Max('latestActivity'))['latestActivity__max'] - MAX_USER_SEARCHES
					recentActOwners = Profile.objects.filter(latestActivity__gte= recentActive)
					findMatches(request, deck, recentActOwners)
				else:
					context["message"] = "You already have added this code"
					context["deckCode"] = deckCode
					context["deckName"] = deckName
		else:
			context["message"] = "Your deck code is not valid"
			context["deckCode"] = deckCode
			context["deckName"] = deckName
	
	context["wishList"] = request.user.profile.wishList.all()
	return render(request, "deckShare/wishList.html", context)

@login_required
def deleteFromWishlist(request):
	try:
		deckId = escape(request.POST.get("deckToDelete"))
		wishList = request.user.profile.wishList.all()
		wishList.get(id=deckId).delete()
		updateActivity(request)
		return render(request, "deckShare/wishList.html", {"wishList": wishList})
	except:
		message = "An error occured"
		return render(request, "deckShare/wishList.html", {"wishList": wishList, "message": message})

@login_required
def updatedCollection(request):
	if timeDiff(request) > API_TIMEOUT_SECS:
		updateActivity(request)
		return refreshHSRAccess(request)
	else:
		return render(request, "deckShare/updatedCollection.html", 
						{"message": f"You recently updated your collection. Please wait {API_TIMEOUT_SECS - timeDiff(request)} seconds before trying again"})

@login_required
def loadedCollection(request):

	state = request.user.profile.state
	oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE, state=state)
	authorization_response = request.build_absolute_uri()
	token = oauth.fetch_token(
	        	HSR_TOKEN_URL,
	        	authorization_response=authorization_response)
	getUserData(request, oauth)
	clearMatches(request.user)
	updateActivity(request)
	recentActive = Profile.objects.all().aggregate(Max('latestActivity'))['latestActivity__max'] - MAX_USER_SEARCHES
	recentActOwners = Profile.objects.filter(latestActivity__gte= recentActive)
	for deck in request.user.profile.wishList.all():
		findMatches(request, deck, recentActOwners)
	return render(request, "deckShare/updatedCollection.html", {"message": "You have sucessfully updated your collection"})
	

@login_required
def updateCollection(request):
	if timeDiff(request) > API_TIMEOUT_SECS:
		updateActivity(request)
		if request.user.profile.token is None:
			return authorizeHSRAccess(request)
		else:
			return refreshHSRAccess(request)
	else:
		return render(request, "deckShare/updatedCollection.html", {"message": f"You recently updated your collection. Please wait {API_TIMEOUT_SECS - timeDiff(request)} seconds before trying again"})
	
# Deletes all matches a user has
def clearMatches(user):
	print(user)
	print(user.profile)
	print(user.profile.matches)
	print(user.profile.matches.all())
	for match in user.profile.matches.all():
		match.delete()
	user.save()

def deleteAllMatches():
	for match in Match.objects.all():
		match.delete()


@login_required
def matches(request):
	# potentialMatches = []
	# matches = []
	# profile = request.user.profile
	# for deck in Deck.objects.all():
	# 	if deck.owner != profile and deck.owner not in potentialMatches:
	# 		if isMakable(deck, request.user.profile):
	# 			potentialMatches.append(deck.owner)
	# print(f"Potmatches: {potentialMatches}")

	# for owner in potentialMatches:
	# 	print(f"owner is {owner}")
	# 	for deck in profile.wishList.all():
	# 		if isMakable(deck, owner):
	# 			matches.append(deck)
	# print(f"matches: {matches}")
	

	return render(request, "deckShare/matches.html", {"matches": Match.objects.filter(Q(deck1__owner=request.user.profile) | Q(deck2__owner=request.user.profile))})

@login_required
def generous(request):
	generous = []
	for deck in Deck.objects.all():
		profile = request.user.profile
		if deck.owner != profile:
			if isMakable(deck, request.user.profile):
				generous.append(deck)
	return render(request, "deckShare/generous.html", {"generous": generous})


