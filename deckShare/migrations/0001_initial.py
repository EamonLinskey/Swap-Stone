# Generated by Django 2.0.3 on 2018-10-25 20:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Deck',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('deckString', models.CharField(max_length=200)),
                ('Hero', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deckString1', models.CharField(max_length=200)),
                ('deckString2', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('blizzTag', models.CharField(max_length=100)),
                ('matches', models.ManyToManyField(blank=True, to='deckShare.Match')),
                ('wishList', models.ManyToManyField(blank=True, to='deckShare.Deck')),
            ],
        ),
        migrations.AddField(
            model_name='match',
            name='player1',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='player1', to='deckShare.Player'),
        ),
        migrations.AddField(
            model_name='match',
            name='player2',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='player2', to='deckShare.Player'),
        ),
    ]