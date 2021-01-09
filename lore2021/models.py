from math import sqrt

from django.db import models
from django.utils.translation import gettext_lazy as _


class Person(models.Model):
    username = models.CharField(max_length=100, blank=False, null=False)
    slugname = models.SlugField(max_length=100, blank=False, null=False, unique=True)
    donator_since = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.username


class Game(models.Model):

    class GameLengths(models.IntegerChoices):
        SHORT = 0, _('Short game')
        MEDIUM = 1, _('Medium game')
        LONG = 2, _('Long game')

    name = models.CharField(max_length=200, blank=False, null=False, unique=True)
    glength = models.IntegerField(choices=GameLengths.choices, null=False, blank=True)
    hours = models.IntegerField(null=False, blank=True)
    favorite = models.BooleanField(null=False, blank=False, default=False)
    to_export = models.BooleanField(null=False, blank=False, default=True, verbose_name="Export this game to the website")
    total = models.FloatField(null=False, blank=False, default=0.0)
    funders = models.IntegerField(null=False, blank=False, default=0)
    priority = models.IntegerField(null=False, blank=False, default=0)
    added = models.DateField(auto_now_add=True)
    ready = models.DateField(verbose_name='Run funded', null=True, default=None)
    started = models.DateField(verbose_name='Run started', null=True, default=None)
    ended = models.DateField(verbose_name='Run ended', null=True, default=None)

    @property
    def percentage(self):
        return int(self.priority*100/self.hours)/100

    @property
    def game_length(self):
        return Game.GameLengths.choices[self.glength][1]

    def update_calc(self):
        amount = 0.0
        funders = set()
        # for donation in Donation.objects.filter(interest=self).all():
        for donation in self.donations.all():
            amount += donation.amount
            funders.add(donation.donator.slugname)
        nb_funders = len(funders)
        priority = float(sqrt(nb_funders) * amount)
        self.total = amount
        self.funders = nb_funders
        self.priority = priority
        self.save()

    def __str__(self):
        return self.name + " [" + str(self.percentage) + "]"



class Donation(models.Model):

    class DonationSource(models.IntegerChoices):
        OTHER = 0, _('Other source')
        PRIME_SUB = 1, _('Prime sub')
        TIER1_SUB = 2, _('Tier 1 sub')
        TIER2_SUB = 3, _('Tier 2 sub')
        TIER3_SUB = 4, _('Tier 3 sub')
        BITS = 5, _('Bits')
        DIRECT = 6, _('Direct donation')
        PATREON = 7, _('Patreon')
        ADS = 8, _('Ad revenue')
        IMPORTATION = 9, _('Imported')

    amount = models.FloatField(null=False, blank=False)
    source = models.IntegerField(choices=DonationSource.choices)
    donator = models.ForeignKey(Person, on_delete=models.CASCADE, null=False, blank=False)
    during = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True)
    when = models.DateTimeField(auto_now_add=True)
    interest = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True, related_name='donations')
    gifted = models.ForeignKey(Person, on_delete=models.CASCADE, null=True, blank=True, related_name='gifted_interest')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if 'dnu' not in kwargs:
            self.interest.update_calc()

    def delete(self, *args, **kwargs):
        game_id = self.interest.pk
        super().delete(*args, **kwargs)
        Game.objects.get(pk=game_id).update_calc()

    def __str__(self):
        return str(self.donator) + " gave " + str(self.amount) + " " + str(self.interest.name)