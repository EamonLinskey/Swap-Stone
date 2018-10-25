from django.db import models

# Create your models here.
class Deck(models.Model):
	name = models.CharField(max_length=50)
	deckString = models.CharField(max_length=200)
	Hero = models.CharField(max_length=20)

class Player(models.Model):
	blizzTag = models.CharField(max_length=100)
	wishList = models.ManyToManyField(Deck, blank=True)
	matches = models.ManyToManyField('Match', blank=True)

class Match(models.Model):
	player1 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="player1")
	player2 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="player2")
	deckString1 = models.CharField(max_length=200)
	deckString2 = models.CharField(max_length=200)
