import datetime
from math import sqrt

from django.conf import settings
from django.db import models
from django.db.models import F, Sum
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now


class Person(models.Model):
    username = models.CharField(max_length=100, blank=False, null=False)
    slugname = models.SlugField(max_length=100, blank=False, null=False, unique=True)
    donator_since = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.username

    class Meta:
        ordering = ['slugname']


class GameManager(models.Manager):
    def get_queryset(self):
        return models.QuerySet(
            model=self.model,
            using=self._db,
            hints=self._hints
        ).annotate(_percentage=(F('priority') / F('priority_needed')) * 100)


class Game(models.Model):
    objects = GameManager()

    class GameLengths(models.IntegerChoices):
        SHORT = 0, _('Short game')
        MEDIUM = 1, _('Medium game')
        LONG = 2, _('Long game')

    name = models.CharField(max_length=200, blank=False, null=False, unique=True)
    glength = models.IntegerField(choices=GameLengths.choices, null=False, blank=True)
    hours = models.IntegerField(null=False, blank=True)
    favorite = models.BooleanField(null=False, blank=False, default=False)
    streamination = models.BooleanField(null=False, blank=False, default=False)
    to_export = models.BooleanField(null=False, blank=False, default=True, verbose_name="Export this game to the website")
    total = models.FloatField(null=False, blank=False, default=0.0)
    funders = models.IntegerField(null=False, blank=False, default=0)
    priority = models.IntegerField(null=False, blank=False, default=0)
    priority_needed = models.IntegerField(null=False, blank=False, default=0)
    added = models.DateField(default=now, blank=False, null=False)
    ready = models.DateField(verbose_name='Run funded', null=True, default=None, blank=True)
    started = models.DateField(verbose_name='Run started', null=True, default=None, blank=True)
    ended = models.DateField(verbose_name='Run ended', null=True, default=None, blank=True)

    @classmethod
    def games_for_list(cls):
        return cls.objects.filter(ready=None).filter(to_export=True).filter(total__gt=0).order_by(
                'glength',
                '-priority',
            ).all()

    def percentage(self):
        return self.priority / self.priority_needed * 100

    def days_since(self):
        return (datetime.datetime.today().date() - self.added).days

    percentage.admin_order_field = '_percentage'
    percentage.short_description = 'Percentage'
    percentage = property(percentage)

    @property
    def game_length(self):
        return Game.GameLengths.choices[self.glength][1]

    def update_calc(self):
        amount = 0.0
        funders = set()
        for donation in self.donations.all():
            amount += donation.amount
            funders.add(donation.donator.slugname)
        nb_funders = len(funders)
        if "prioritylistfakeuser" in funders:
            nb_funders -= 1
        priority = float(sqrt(nb_funders) * amount)
        self.total = amount
        self.funders = nb_funders
        self.priority = priority
        self.save()

    def __str__(self):
        return self.name + " [" + str(self.percentage) + "]"

    class Meta:
        ordering = ['name']


class DonationBase:
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
        DEALER = 10, _('Dealer Choice input')
        CREDIT = 11, _('Lore credits')

    @property
    def shorthand(self):
        if self.source == DonationBase.DonationSource.OTHER or self.source == DonationBase.DonationSource.PATREON:
            return 'O'
        if self.source == DonationBase.DonationSource.DIRECT:
            return 'D'
        if self.source == DonationBase.DonationSource.BITS:
            return 'B'
        return ' '

    @property
    def source_long(self):
        return DonationBase.DonationSource.choices[self.source][1]

    def save_trace(self, filename):
        if self.source != Donation.DonationSource.IMPORTATION and self.source != Donation.DonationSource.DEALER:
            with open(filename, 'w') as f:
                print(self.shorthand + " " + self.__str__() + " [" + str(datetime.datetime.now()) + "]", file=f)


class Donation(models.Model, DonationBase):

    donator = models.ForeignKey(Person, on_delete=models.CASCADE, null=False, blank=False)
    source = models.IntegerField(choices=DonationBase.DonationSource.choices)
    amount = models.FloatField(null=False, blank=False)
    interest = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True, related_name='donations')
    when = models.DateTimeField(auto_now_add=True)
    during = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True)
    gifted = models.ForeignKey(Person, on_delete=models.CASCADE, null=True, blank=True, related_name='gifted_interest')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if settings.DONATION_DUMP:
            self.save_trace(settings.DONATION_DUMP)
        if 'dnu' not in kwargs:
            self.interest.update_calc()

    def delete(self, *args, **kwargs):
        game_id = self.interest.pk
        super().delete(*args, **kwargs)
        Game.objects.get(pk=game_id).update_calc()

    def __str__(self):
        return str(self.donator) + " gave $" + str(self.amount) + " to " + str(self.interest.name)


class DealerChoice(models.Model, DonationBase):
    donator = models.ForeignKey(Person, on_delete=models.CASCADE, null=False, blank=False)
    source = models.IntegerField(choices=DonationBase.DonationSource.choices, default=DonationBase.DonationSource.OTHER)
    amount = models.FloatField(null=False, blank=False)
    during = models.ForeignKey(Game, on_delete=models.CASCADE, null=True, blank=True)
    when = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.donator) + " $" + str(self.amount)

    @classmethod
    def get_current_pool(cls):
        spent = float(Variables.objects.get_or_create(
            variable=Variables.VariableList.ALLOCATED_DC, defaults={'value': "0"})[0].value)
        return DealerChoice.objects.all().aggregate(Sum('amount'))['amount__sum'] - spent

    @classmethod
    def subtract_from_pool(cls, amount):
        var, created = Variables.objects.get_or_create(
            variable=Variables.VariableList.ALLOCATED_DC,
            defaults={'value': "0"},
        )
        var.value = str(float(var.value)+amount)
        var.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if settings.DEALER_CHOICE_DUMP:
            self.save_trace(settings.DEALER_CHOICE_DUMP)


class Variables(models.Model):
    class VariableList(models.IntegerChoices):
        ALLOCATED_DC = 0, _("Allocated dealer's choice")
        PRIORITY = 1, _("Priority multiplicator")

    variable = models.IntegerField(choices=VariableList.choices, unique=True)
    value = models.CharField(max_length=200, blank=False, null=False)

    def save(self, *args, **kwargs):
        if self.variable == self.VariableList.PRIORITY:
            PERCENTAGE_MULTIPLICATOR = float(self.value)
        super().save(*args, **kwargs)


try:
    PERCENTAGE_MULTIPLICATOR = float(Variables.objects.get_or_create(
        variable=Variables.VariableList.PRIORITY, defaults={'value': "100"})[0].value)
except:
    PERCENTAGE_MULTIPLICATOR = 100
