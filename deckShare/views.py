from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.urls import reverse 
from django.http import (HttpResponse, HttpResponseRedirect, 
						HttpResponseNotAllowed)
import re

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