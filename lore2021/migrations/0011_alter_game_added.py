# Generated by Django 3.2.2 on 2021-05-06 20:32

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('lore2021', '0010_auto_20210112_2050'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='added',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
