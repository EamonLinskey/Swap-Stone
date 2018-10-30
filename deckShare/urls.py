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
    path("profile/updateCollection", views.updateCollection, name="updateCollection"),
    path("wishList", views.wishList, name="wishList"),
]