from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Deck(models.Model):
	name = models.CharField(max_length=50)
	deckString = models.CharField(max_length=200)
	deckClass = models.CharField(max_length=20)

class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	blizzTag = models.CharField(max_length=100, blank=True)
	wishList = models.ManyToManyField(Deck, blank=True)
	matches = models.ManyToManyField('Match', blank=True)
	token = models.CharField(max_length=100, blank=True)
	refreshtoken = models.CharField(max_length=100, blank=True)
	collection = JSONField(blank=True, null=True)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Match(models.Model):
	user1 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="player1")
	user2 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="player2")
	deckString1 = models.CharField(max_length=200)
	deckString2 = models.CharField(max_length=200)
