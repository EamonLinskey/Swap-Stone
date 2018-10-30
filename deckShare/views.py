from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.urls import reverse 
from django.http import (HttpResponse, HttpResponseRedirect, 
						HttpResponseNotAllowed)
from django.utils.html import escape
from requests_oauthlib import OAuth2Session
from .models import Deck, Profile, Match
import re
import os

# globals
DECK_SIZE = 30
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
SCOPE = ['collection:read']
HSR_AUTHORIZATION_URL = 'https://hsreplay.net/oauth2/authorize/'
HSR_TOKEN_URL = 'https://hsreplay.net/oauth2/token/'
HSR_ACCOUNT_URL = 'https://hsreplay.net/api/v1/account/'

def validate_deck_code(deckString, FULL_COLLECTION):
    # Makes sure deckstring is syntactically valid
    try:
        deck = Deck.from_deckstring(deckString)
    except:
        return False
    
    # Checks if deck length is equal to the Standard Hearthstone decklength
    if sum([int(cardNum) for _,cardNum in deck.cards]) != DECK_SIZE:
        return False

    # Checks if each "card" corresponds to an actual Hearthstone card
    classes = []
    for cardId,_ in deck.cards:
        if cardId not in FULL_COLLECTION:
            return False
        # creates a list of classes used to make a deck
        if FULL_COLLECTION[cardId]["class"] not in classes and FULL_COLLECTION[cardId]["class"] != "NEUTRAL":
            classes += [COLLECTION_CLASSES[cardId]]
    
    # Makes sure only one class (and neutrals) can be in a deck (It can also be all neutrals)
    if len(classes) <= 1:
        return True
    return False




# Create your views here.
def index(request):
	return render(request, "deckShare/index.html")

@login_required
def profile(request):
	return render(request, "deckShare/profile.html")

def signIn(request):
	if request.user.is_authenticated:
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
			return HttpResponseRedirect(reverse("profile"))
		except:
			return render(request, "deckShare/signIn.html", 
							{"message": "Invalid Credentials",
							 "username": username})
	else:
		return HttpResponseRedirect(reverse("profile"))


def register(request):
	if request.user.is_authenticated:
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
				return HttpResponseRedirect(reverse("profile"))
			except:
				return render(request, "deckShare/register.html", 
							{"message": "An unknown error occured",
							"email": email, "username": username})	
	else:
		return HttpResponseRedirect(reverse("index"))

@login_required
def wishList(request):
	wishList = Player.objects.get(blizzTag="Linsk#123").wishList.all()
	return render(request, "deckShare/wishList.html", {"wishList": wishList})

@login_required
def updatedCollection(request):
	# May be overkill to escape here but potentially prevents malicious injections
	#print(f'Escaped code is {escape(request.GET["code"])}')
	#print(f'Escaped code is {escape(request.GET["state"])}')
	#print(request.build_absolute_uri())
	
	if request.user.profile.refreshToken == "":
		print("no refreshToken")
		state = request.user.profile.state
		oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE, state=state)
		authorization_response = request.build_absolute_uri()
		token = oauth.fetch_token(
	        	HSR_TOKEN_URL,
	        	authorization_response=authorization_response)
		getUserData(request, oauth)
	else:
		refreshHSRAccess(request)
	return render(request, "deckShare/updatedCollection.html")


def getUserData(request, oauth):
	# Get user data
	userData = oauth.get(HSR_ACCOUNT_URL).json()
	accountHi, accountLo = userData["blizzard_accounts"][0]["account_hi"],userData["blizzard_accounts"][0]["account_lo"]
	
	# Fetch collection
	collectionUrl = f"https://api.hsreplay.net/v1/collection/?account_hi={accountHi}&account_lo={accountLo}"
	collection = oauth.get(collectionUrl).json()

	# Save relevent user data
	profile = request.user.profile
	profile.blizzTag = userData["battletag"]
	profile.token = oauth.token
	profile.collection = collection
	request.user.save()

def authorizeHSRAccess(request):
	# set up OAuth2 Session
	oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
	authorization_url, state = oauth.authorization_url(HSR_AUTHORIZATION_URL)

	# redirect to HSreplay for authorization
	return authorization_url, state

def refreshHSRAccess(request):
	# set up OAuth2 Session
	token = request.user.profile.token
	oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE, token=token)
	authorization_url, state = oauth.authorization_url(HSR_AUTHORIZATION_URL)
	clientInfo = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET}
	token = oauth.refresh_token(HSR_TOKEN_URL, **clientInfo)
	getUserData(request, oauth)


@login_required
def updateCollection(request):
	print(f'the token is: {request.user.profile.refreshToken == None}')
	if request.user.profile.token is None:
		authorization_url, state = authorizeHSRAccess(request)
		request.user.profile.state = state
		request.user.save()
		return redirect(authorization_url)
	return render(request, "deckShare/updatedCollection.html")
	

