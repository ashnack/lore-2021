# Generated by Django 3.2.13 on 2022-06-15 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lore2021', '0013_game_streamination'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='days_since_change',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
