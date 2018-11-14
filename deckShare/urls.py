from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("signIn", views.signIn, name="signIn"),
    path("signedIn", views.signedIn, name="signedIn"),
    path("signOut", views.signOut, name="signOut"),
    path("register", views.register, name="register"),
    path("registered", views.registered, name="registered"),
    path("profile", views.profile, name="profile"),
    path("profile/updatedCollection", views.updatedCollection, name="updatedCollection"),
    path("profile/updateCollection", views.updateCollection, name="updateCollection"),
    path("profile/loadedCollection", views.loadedCollection, name="loadedCollection"),
    path("profile/wishList", views.wishList, name="wishList"),
    path("profile/matches", views.matches, name="matches"),
    path("profile/generous", views.generous, name="generous"),
    path("tests", views.tests, name="tests"),
    
]