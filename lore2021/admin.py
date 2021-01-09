# ./manage.py admin_generator lore2021
# -*- coding: utf-8 -*-
from django.contrib import admin
from django.forms import forms
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.text import slugify
from django.utils.timezone import now
from datetime import timedelta

from pyexcel_ods import get_data

from .models import Person, Game, Donation


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    icon_name = 'person'

    list_display = ('id', 'username', 'donator_since')
    list_filter = ('donator_since',)

    search_fields = ('slugname', )


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    icon_name = 'gamepad'

    list_display = (
        'id',
        'name',
        'percentage',
        'glength',
        'hours',
        'total',
        'funders',
        'priority',
        'favorite',
        'added',
        'ready',
    )
    list_filter = ('favorite', 'ready', 'glength')
    search_fields = ('name',)

    change_list_template = "changelist_www.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('website-export/', self.for_website),
        ]
        return my_urls + urls

    def for_website(self, request):
        return render(
            request,
            "website.html",
            {
                'games': Game.objects.filter(ready=None).filter(to_export=True).order_by('glength', '-priority').all()
            }
        )


class ImportForm(forms.Form):
    file = forms.FileField()


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    icon_name = 'attach_money'

    list_display = (
        'id',
        'amount',
        'source',
        'donator',
        'during',
        'when',
        'interest',
        'gifted',
    )
    list_filter = ('donator', 'during', 'when', 'interest', 'gifted')
    autocomplete_fields = ('donator', 'interest', 'gifted', 'during')

    change_list_template = "changelist.html"

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import/', self.importer),
        ]
        return my_urls + urls

    def importer(self, request):
        if request.method == "POST":
            file = request.FILES["file"]
            data = get_data(file)
            data_keys = list(data.keys())
            # print(data_keys)
            i = 0
            data_length = len(data[data_keys[0]][4])
            while i < data_length:
                text = str(data[data_keys[0]][6][i])
                if text:
                    sorter = int(data[data_keys[0]][3][i]) if data[data_keys[0]][3][i] else 0
                    j = 2
                    if sorter < 15:
                        j = 0
                    elif sorter < 30:
                        j = 1

                    try:
                        lore_choice = str(data[data_keys[0]][1][i]).lower()
                    except IndexError:
                        lore_choice = ''
                    since = now() - timedelta(days=int(data[data_keys[0]][7][i]))
                    game, created = Game.objects.get_or_create(
                        name=text,
                        defaults={
                            'glength': j,
                            'hours': sorter,
                            'favorite': True if lore_choice else False,
                            'added': since
                        }
                    )
                    Donation.objects.filter(interest=game).filter(source=9).delete()
                    k = 8
                    try:
                        while data[data_keys[0]][k][i]:
                            if data[data_keys[0]][k][i]:
                                label = data[data_keys[0]][k][i]
                                label_test = label.split(' ')
                                donation = 2.0
                                if len(label_test) > 1 and int(label_test[-1]) > 0:
                                    label = label[0:(len(label_test[-1])+1) * -1]
                                    donation = float(label_test[-1])

                                slug = slugify(label)
                                pers, created = Person.objects.get_or_create(slugname=slug)
                                if created:
                                    pers.username = label
                                    pers.save()
                                donation_object = Donation(
                                    amount=donation,
                                    source=9,
                                    donator=pers,
                                    during=None,
                                    interest=game,
                                )
                                donation_object.save({'dnu': True})
                            k += 1
                    except:
                        pass
                    game.update_calc()
                i += 1

            # ...
            self.message_user(request, "Your file has been imported")
            return redirect("..")
        form = ImportForm()
        payload = {"form": form}
        return render(
            request, "form.html", payload
        )
