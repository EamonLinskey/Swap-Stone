# Generated by Django 2.0.3 on 2018-11-02 20:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('deckShare', '0008_profile_time'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='match',
            name='deckString1',
        ),
        migrations.RemoveField(
            model_name='match',
            name='deckString2',
        ),
        migrations.RemoveField(
            model_name='match',
            name='user1',
        ),
        migrations.RemoveField(
            model_name='match',
            name='user2',
        ),
        migrations.AddField(
            model_name='deck',
            name='owner',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='deckShare.Profile'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='match',
            name='deck1',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='deck1', to='deckShare.Profile'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='match',
            name='deck2',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='deck2', to='deckShare.Profile'),
            preserve_default=False,
        ),
    ]