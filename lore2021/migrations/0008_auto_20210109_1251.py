# Generated by Django 3.1.5 on 2021-01-09 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lore2021', '0007_auto_20210109_1556'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='funders',
            field=models.IntegerField(default=0),
        ),
    ]