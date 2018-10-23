from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import (HttpResponse, HttpResponseRedirect, 
						HttpResponseNotAllowed)

# Create your views here.
def index(request):
	return render(request, "deckShare/index.html")

def signIn(request):
	if request.user.is_authenticated:
		return HttpResponseRedirect(reverse("index"))
	else:
		return render(request, "deckShare/signIn.html")

def signOut(request):
	if request.user.is_authenticated:
		logout(request)
	return HttpResponseRedirect(reverse("signIn"))