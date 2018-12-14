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
from .models import Deck, Profile
import re
import os
import datetime
import time
import json
import requests
import random
import math

from swapstone.settings_secret import BULK_USER_PASS

# globals
DECK_SIZE = 30
WISH_LIMIT = 5
API_TIMEOUT_SECS = 120
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
SCOPE = ['collection:read']
HSR_AUTHORIZATION_URL = 'https://hsreplay.net/oauth2/authorize/'
HSR_TOKEN_URL = 'https://hsreplay.net/oauth2/token/'
HSR_ACCOUNT_URL = 'https://hsreplay.net/api/v1/account/'
MAX_USER_SEARCHES = 100
MATCH_PER_PAGE = 10
MAX_GENEROUS = 10
# These are the designations used by the API for standard legal sets. I didn't pick the (poor) names
# Should be updated on release of new sets or on rotataion
STANDARD_SETS = ["CORE", "EXPERT1" "UNGORO", "ICECROWN", "LOOTAPALOOZA", "GILNEAS", "BOOMSDAY"]
#CLASSES = {heroes}


#print(Profile.objects.all())
#mostRecentActivity = Profile.objects.all().aggregate(Max('latestActivity'))
#print(mostRecentActivity)

def makeOutFile(fileName, obj):
	with open(fileName, 'w') as outfile:
		json.dump(obj, outfile)

# Used to make teh full colllection json file locally
# should only be run when new cards are added to update file
def makeFullCollFile(fileNames):
	# As of Nov 29, 18 version is 27641 but latest should automatically fetch th most recent version corresponinf to current expansion
	dataResponse = requests.get(f"https://api.hearthstonejson.com/v1/latest/enUS/cards.collectible.json")
	
	fullCollectionRaw = json.loads(dataResponse.text)
	fullCollectionEdited = {}
	hereos = {}

	for card in fullCollectionRaw:
		if "cost" in card:
			fullCollectionEdited[card["dbfId"]] = {"name": card["name"], "cost": card["cost"]}
		elif card["type"] == "HERO":
			hereos[card["dbfId"]] = card["cardClass"]

	for file, d in zip(fileNames, [fullCollectionRaw, fullCollectionEdited, hereos]):
		makeOutFile(file, d)

	


#makeFullCollFile(["FullCollection.json", "EditedCollection.json", "Hereos.json"])

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
		deckFormat = 'wild'
		if card["set"] in STANDARD_SETS:
			deckFormat = 'standard'
		if card['id'][0:4] != "HERO":
			fullCollectionClean[card['dbfId']] = {'name': card['name'],'class': card['cardClass'], 'format':deckFormat}
		else:
			heroes[card['dbfId']] = {'name': card['name'],'class': card['cardClass'], 'format':deckFormat}
	return fullCollectionClean, heroes

def IsValidDeckString(deckString):
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
		#recentActive = Profile.objects.all().aggregate(Max('latestActivity'))['latestActivity__max'] - MAX_USER_SEARCHES
		recentActOwners = Profile.objects.filter(latestActivity__gte= recentActive)
		recentActOwners = Profile.objects.all()
		for deck in request.user.profile.wishList.objects.all():
			findMatches(request, deck, recentActOwners)
		return render(request, "deckShare/updatedCollection.html", {"message": "You have sucessfully updated your collection"})
	except:
		# If access was revoked this tries to reauthorize
		return authorizeHSRAccess(request)

# More globals that require a function to be set
FULL_COLLECTION, HEROES = buildFullColl('static/deckShare/json/FullCollection.json')

# splits FULL_COLLECTION up among classes for building legal decks more easily
def cardsByClass():
	classCards = {"MAGE":{}, "ROGUE":{}, "WARLOCK":{}, "WARRIOR":{}, "PALADIN":{}, "SHAMAN":{}, "PRIEST":{}, "HUNTER":{}, "DRUID":{}, "NEUTRAL":{}}
	standardClassCards = {"MAGE":{}, "ROGUE":{}, "WARLOCK":{}, "WARRIOR":{}, "PALADIN":{}, "SHAMAN":{}, "PRIEST":{}, "HUNTER":{}, "DRUID":{}, "NEUTRAL":{}}
	
	# Seperates main dic into a dict of dicts by class
	for cardId,cardInfo in FULL_COLLECTION.items():
		classCards[cardInfo['class']][cardId] = cardInfo

		# makes a seprate dict of dicts for standard only cards
		if cardInfo["format"] == "standard":
			standardClassCards[cardInfo['class']][cardId] = cardInfo
	
	return {"allClass": classCards, "standardClass":standardClassCards}


def genRandDeck(standardClassCards):
	# list of hero ids for the 9 starting heros for each class for deck construction
	HeroIds = {"MAGE":637, "ROGUE":930, "WARLOCK":893, "WARRIOR":7, "PALADIN":671, "SHAMAN":1066, "PRIEST":813, "HUNTER":31, "DRUID":274}
	deckClass = random.choice(list(HeroIds))

	cards = list(standardClassCards[deckClass])	
	# Shuffle list then sample first 30 to simulate random selection without replacement
	random.shuffle(cards)

	# zip list with number of copies of each card so that deckstring function can make deck string
	cards = list(zip(cards[0:DECK_SIZE], [1]*DECK_SIZE))

	# Create decking using Hearthsone module
	deck = DeckHearth()
	deck.heroes = [HeroIds[deckClass]]  # Garrosh Hellscream
	deck.format = FormatType.FT_STANDARD
	deck.cards = cards
	return { "deckstring": deck.as_deckstring, "class":deckClass}


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
	timer = time.time()
	print("timer has started")

	matches = []
	# Looks through all owners to see who's collections can make the new deck
	for owner in recentActOwners:
		if newDeck.owner != owner and isMakable(newDeck, owner):
			# Looks through matching owners decks to see if current user 
			# can make any of their decks with their own collections to complete the match
			for deck in owner.wishList.all():
				if isMakable(deck, newDeck.owner):
					#Match.objects.createMatch(deck, newDeck)
					matches.append(owner)
					break
	print(f"Decks Checked:{int(time.time() - timer)} seconds have passed")
	# 		matches.append(MatchList(profile=owner))

					

	# # Create new matches and associate them with the user
	# matchListObjs = MatchList.objects.bulk_create(matches)
	# for matchList, decksList in zip(matchListObjs, decksListList):
	# 	print(f"the decklists are {decksList}")
	# 	matchList.add(*decksList)

	request.user.profile.matches.add(*matches)
	print(f"Mathces added: {int(time.time() - timer)} seconds have passed")

@login_required
def wishList(request):
	context = {}

	if 'deckToDelete' in request.POST:
		return deleteFromWishlist(request)

	if ('deckName' not in request.POST or  'deckCode' not in request.POST):
			context["wishList"] = request.user.profile.wishList.all()
			return render(request, "deckShare/wishList.html", context)
	else:
		deckName, deckString = escape(request.POST.get("deckName")), escape(request.POST.get("deckCode"))
		if IsValidDeckString(deckString):
			if len(deckName) > 50 or len(deckName) <= 0:
				context["message"] = "Your deck Name must be less than 50 characters and cannot be blank"
			else:
				wishList = request.user.profile.wishList.all()
				if len(wishList.filter(deckString=deckString)) == 0:
					deckObj = DeckHearth.from_deckstring(deckString)
					heroId = deckObj.heroes[0]
					deckClass = HEROES[heroId]["class"].capitalize()
					deck = Deck(name = deckName, deckString= deckString, deckClass=deckClass, maxMatchIdChecked = 0, owner =request.user.profile)
					deck.save()	
					request.user.profile.wishList.add(deck)
					request.user.save()
					#updateActivity(request)
					#recentActive = Profile.objects.all().aggregate(Max('latestActivity'))['latestActivity__max'] - MAX_USER_SEARCHES
					#recentActOwners = Profile.objects.filter(latestActivity__gte= recentActive)
					recentActOwners = Profile.objects.all()
					findMatches(request, deck, recentActOwners)
				else:
					context["message"] = "You already have added this code"
					context["deckCode"] = deckString
					context["deckName"] = deckName
		else:
			context["message"] = "Your deck code is not valid"
			context["deckCode"] = deckString
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
	recentActOwners = Profile.objects.all()
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

def makeFriends(friendA, friendB):
	friendA.awaitingResponse.remove(friendB)
	friendA.offeredFriendship.remove(friendB)

	friendB.awaitingResponse.remove(friendA)
	friendB.offeredFriendship.remove(friendA)

	# The friends relationship is symeterical so it is only needed on one side
	friendA.friends.add(friendB)


def requestFriend(userPro, friendPro):
	# Checking if frined request is valid from requesters side
	if (not userPro.friends.all().filter(id=friendPro.id).exists()
	and not userPro.awaitingResponse.all().filter(id=friendPro.id).exists()
	and not userPro.offeredFriendship.all().filter(id=friendPro.id).exists()):

		# Checks friend status on recievers side
		if friendPro.awaitingResponse.all().filter(id=userPro.id).exists():
			# finalize friendship
			makeFriends(friendPro, userPro)
		else:
			# begin friendship
			userPro.awaitingResponse.add(friendPro)
			friendPro.offeredFriendship.add(userPro)

def acceptFriend(userPro, friendPro):
	# check for valid frienship request
	if not (userPro.friends.all().filter(id=friendPro.id).exists()
	and userPro.offeredFriendship.all().filter(id=friendPro.id).exists() 
	and friendPro.awaitingResponse.all().filter(id=userPro.id).exists()):
		# finalize friendship
		makeFriends(friendPro, userPro)

# This returns a zipped object with the profiles, the decks they desire
# and the decks they can offer
def zipProfilesWithDecks(request, profiles, start, end, addFriends=False):
	index = start
	maxIndex = profiles.count() -1
	if end > maxIndex:
		end = maxIndex
	#print(f"the profiles are {profiles}")
	#print(f"the max index is {maxIndex}")
	#print(f"the end is {end}")


	desiredByUserList = []
	desiredByMatchList = []
	fiendStatusList = []
	profilesList = []
	profilesToRemove = []

	userPro = request.user.profile

	# I use a while loop instead of a for loop here because 
	# matches are tied to profiles rather then decks, when 
	# a deck is deleted it does not invalidate the match. 
	# Therefore I have to clean out old matches while looping 
	# through them. In order to keep matches per page constant 
	# I have to be able to change in index as I iterate
	while index <= end:
		#print(f"the index is {index}")
		desiredByUser = []
		desiredByMatch = []

		for deck in profiles[index].wishList.all():
			if isMakable(deck, userPro):
				desiredByUser.append({"name": deck.name, "deckString": deck.deckString} )
		

		for deck in userPro.wishList.all():
			if isMakable(deck, profiles[index]):
				desiredByMatch.append({"name": deck.name, "deckString": deck.deckString})


		if addFriends:
			friends = "notFriends"
			if userPro.friends.all().filter(id=profiles[index].id).exists():
				#print("friends")
				friends = "friends"
			elif userPro.awaitingResponse.all().filter(id=profiles[index].id).exists():
				friends = "awaiting"
				#print("awaiting")
			elif userPro.offeredFriendship.all().filter(id=profiles[index].id).exists():
				#print("offered")
				friends = "offered"

		if desiredByUser == [] or desiredByMatch == []:
			#print("made it here")
			profilesToRemove.append(profiles[index])
			if not addFriends:
				desiredByUserList.append(desiredByUser)
				desiredByMatchList.append(desiredByMatch)
				profilesList.append(profiles[index])
			if end < maxIndex:
				end += 1
		else:
			desiredByUserList.append(desiredByUser)
			desiredByMatchList.append(desiredByMatch)
			profilesList.append(profiles[index])
			if addFriends:
				fiendStatusList.append(friends)
		index += 1
	
		#print(f"profilesList is {profilesList}")
		#print(f"desiredByUserList is {desiredByUserList}")
		#print(f"desiredByMatchList is {desiredByMatchList}")
		#print(f"fiendStatusList is {fiendStatusList}")
	if addFriends:
		profiles = list(zip(profilesList, desiredByUserList, desiredByMatchList, fiendStatusList))
	else:
		profiles = list(zip(profilesList, desiredByUserList, desiredByMatchList))

	request.user.profile.matches.remove(*profilesToRemove)
	
	return profiles

@login_required
def friends(request, page=1):
	if 'deleteFriend' in request.POST and request.POST['acceptFriend'] != "":
		friendPro = Profile.objects.get(id=int(request.POST['requestFriend']))
		request.user.profile.friends.remove(friendPro)

	elif 'acceptFriend' in request.POST and request.POST['acceptFriend'] != "":
		friendId = int(request.POST['acceptFriend'].strip('"'))
		friendPro = Profile.objects.get(id=friendId)
		acceptFriend(request.user.profile, friendPro)

	#end = page * MATCH_PER_PAGE
	#start = end - MATCH_PER_PAGE 

	# Get the matches within the indexes
	userPro = request.user.profile

	friends = zipProfilesWithDecks(request, userPro.friends.all(), 0, userPro.friends.all().count() -1)
	awaiting = zipProfilesWithDecks(request, userPro.awaitingResponse.all(), 0, userPro.awaitingResponse.all().count() -1)
	offered = zipProfilesWithDecks(request, userPro.offeredFriendship.all(), 0, userPro.offeredFriendship.all().count() -1)

	
	return render(request, "deckShare/friends.html", {"friends": friends, "awaiting": awaiting, "offered": offered, "page":page})


@login_required
def matches(request, page=1):
	if 'requestFriend' in request.POST and request.POST['requestFriend'] != "":
		friendPro = Profile.objects.get(id=int(request.POST['requestFriend']))
		requestFriend(request.user.profile, friendPro)

	elif 'acceptFriend' in request.POST and request.POST['acceptFriend'] != "":
		friendId = int(request.POST['acceptFriend'].strip('"'))
		friendPro = Profile.objects.get(id=friendId)
		acceptFriend(request.user.profile, friendPro)
	
	end = page * MATCH_PER_PAGE
	start = end - MATCH_PER_PAGE


	# Get the matches within the indexes
	userPro = request.user.profile
	matchCount = userPro.matches.count()
	pageMax =  math.ceil(matchCount / MATCH_PER_PAGE)
	print(userPro.matches)
	
	desiredByUserList = []
	desiredByMatchList = []
	fiendStatus = []

	matches = zipProfilesWithDecks(request, userPro.matches.all(), start, end -1, True)
	print(f"user pro is {userPro.matches.all()}")
	print(f"matches is {matches}")
	return render(request, "deckShare/matches.html", {"matches": matches, "page":page, "pageMax":pageMax})#, "desiredByUser": desiredByUserList, "desiredByMatch": desiredByMatchList})#, "owners": list(owners)})

@login_required
def generous(request):
	generous = []
	decks = Deck.objects.all()
	numDecks = decks.count()
	randomIndexes = random.sample(range(0, numDecks), 50)

	# I use random indexes here because it would be too time intensive 
	# to check all possible matches and too space intensive to store all 
	# matches so the compromise is to randomly sample decks until either 
	# their are 10 matches or too many tries have occured. Randomly sampling 
	# indexes allows for us to get items from teh quey set without fully
	# evaluating it saving time
	for index in randomIndexes:
		deck = decks[index]
		profile = request.user.profile
		if deck.owner != profile:
			if isMakable(deck, request.user.profile):
				generous.append(deck)
		if len(generous) >= MAX_GENEROUS:
			break
	return render(request, "deckShare/generous.html", {"generous": generous})

@login_required
def tests(request):

	bulkTestUsers = User.objects.filter(first_name="bulktest")
	bulkTestUsers.delete()

	bulkTestDecks = Deck.objects.filter(isBulkTest=True)
	bulkTestDecks.delete()


	testUsers = []
	for i in range(500):
		username = 'bulktest' + str(i)
		email = username + '@email.com'
		tmpUser = User(username=username, email=email, first_name="bulktest")
		tmpUser.set_password(BULK_USER_PASS)
		testUsers.append(tmpUser)
	User.objects.bulk_create(testUsers)
	
	exampleUser = User.objects.get(username="EamonLinskey")
	exampleProfile = Profile.objects.get(user=exampleUser)
	collection = exampleProfile.collection

	testProfiles = []
	for i, user in enumerate(testUsers):
		blizzTag = 'bulktest' + str(i)
		testProfiles.append(Profile(user=user, blizzTag=blizzTag, collection=collection, latestActivity=i))

	profiles = Profile.objects.bulk_create(testProfiles)


	classCards = cardsByClass()
	standardClassCards = classCards["standardClass"]

	for profile in profiles:
		deckObjs = []
		for i in range(WISH_LIMIT):
			randDeck = genRandDeck(standardClassCards)
			name = profile.blizzTag+ "'s " + str(i)
			deckObj = Deck(owner = profile, name = name, deckString = randDeck["deckstring"], deckClass = randDeck["class"].capitalize(), maxMatchIdChecked = 0, isBulkTest = True)
			deckObjs.append(deckObj)
		Deck.objects.bulk_create(deckObjs)
		profile.wishList.add(*deckObjs)

	return render(request, "deckShare/tests.html")

	
