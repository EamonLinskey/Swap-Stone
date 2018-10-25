from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.urls import reverse 
from django.http import (HttpResponse, HttpResponseRedirect, 
						HttpResponseNotAllowed)
import re

# globals
DECK_SIZE = 30

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

def profile(request):
	if request.user.is_authenticated:
		return render(request, "deckShare/profile.html")
	else:
		return HttpResponseRedirect(reverse("signIn"))

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


def wishList(request):
	if request.user.is_authenticated:
		return render(request, "deckShare/wishList.html")
	else:
		return HttpResponseRedirect(reverse("index"))