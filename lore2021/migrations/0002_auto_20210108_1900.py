# Generated by Django 3.1.5 on 2021-01-08 19:00

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('lore2021', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='added',
            field=models.DateField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='game',
            name='funders',
            field=models.IntegerField(default=0),
        ),
    ]
