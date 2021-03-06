# Generated by Django 2.0.3 on 2018-12-01 16:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('deckShare', '0003_auto_20181201_1607'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profile',
            name='awaitingResponse',
        ),
        migrations.AddField(
            model_name='profile',
            name='awaitingResponse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='friendWaiting', to='deckShare.Profile'),
        ),
        migrations.RemoveField(
            model_name='profile',
            name='offeredFriendship',
        ),
        migrations.AddField(
            model_name='profile',
            name='offeredFriendship',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='friendOffering', to='deckShare.Profile'),
        ),
    ]
