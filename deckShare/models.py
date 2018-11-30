from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
# class DeckManager(models.Manager):
#     def createDeck(self, name, deckString, deckClass, owner):
#         deck = self.create(name=name, deckString=deckString, deckClass=deckClass, owner=owner, maxMatchIdChecked=0)
#         return deck

# class MatchManager(models.Manager):
#     def createMatch(self, deck1, deck2):
#         match = self.create(deck1=deck1, deck2=deck2)
#         return match

# class GenerousManager(models.Manager):
#     def createGenerous(self, deck):
#         Generous = self.create(deck=deck)
#         return Generous

class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	blizzTag = models.CharField(max_length=100, blank=True)
	wishList = models.ManyToManyField('Deck', blank=True)
	matches = models.ManyToManyField('self', blank=True)
	generous = models.ManyToManyField('Generous', blank=True)
	state = models.CharField(max_length=100, blank=True)
	token = JSONField(blank=True, null=True)
	lastUpdateCollection = models.CharField(max_length=100, blank=True)
	time = models.FloatField(blank=False, default = 0)
	collection = JSONField(blank=True, null=True)
	latestActivity = models.IntegerField(blank=True, null=True)
	def __str__(self):
		return f"{self.user.username}'s profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Deck(models.Model):
	owner = models.ForeignKey(Profile, on_delete=models.CASCADE)
	name = models.CharField(max_length=50)
	deckString = models.CharField(max_length=200)
	deckClass = models.CharField(max_length=20)
	maxMatchIdChecked = models.IntegerField()
	isBulkTest = models.BooleanField(default=False)
	#objects = DeckManager()
	def __str__(self):
		return f"{self.name} deck object"


class Generous(models.Model):
	deck = models.ForeignKey(Deck, on_delete=models.CASCADE)
	#objects = GenerousManager()
	def __str__(self):
		return f"{deck.name}"
