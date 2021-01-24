# ./manage.py admin_generator lore2021
# -*- coding: utf-8 -*-
from datetime import timedelta

from django.contrib import admin, messages
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import path
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.timezone import now

from pyexcel_ods import get_data

from .forms import ImportForm, AllocateForm
from .models import Person, Game, Donation, DealerChoice, Variables


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    icon_name = 'assignment_ind'

    list_display = ('username', 'donator_since')
    list_filter = ('donator_since',)

    search_fields = ('slugname', )


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    icon_name = 'gamepad'

    list_display = (
        'name',
        'percentage',
        'glength',
        'hours',
        'total',
        'funders',
        'priority',
        'stats',
        'favorite',
        'added',
        'ready',
    )
    list_filter = ('favorite', 'ready', 'glength')
    search_fields = ('name',)

    change_list_template = "changelist_www.html"

    def stats(self, obj):
        return mark_safe('<a href="stats/?id=' + str(obj.pk) + '" target="_blank"><i '
                                                               'class="material-icons">insert_chart</i></a>')

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('website-export/', self.for_website),
            path('stats/', self.game_stats),
        ]
        return my_urls + urls

    def for_website(self, request):
        return render(
            request,
            "website.html",
            {
                'games': Game.objects.filter(ready=None)
                    .filter(to_export=True).filter(total__gt=0).order_by('glength', '-priority').all()
            }
        )

    def game_stats(self, request):
        game = get_object_or_404(Game, pk=int(request.GET.get('id', 0)))
        donations = Donation.objects.filter(interest=game).order_by('donator__slugname')
        return render(
            request,
            "stats.html",
            {
                'game': game,
                'donations': donations,
            }
        )


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    # radio_fields = {"source": admin.HORIZONTAL}
    icon_name = 'attach_money'

    list_display = (
        'interest',
        'donator',
        'amount',
        'source',
        'during',
        'when',
        'gifted',
    )
    fields = ('source', 'donator', 'amount', 'interest', 'during', 'gifted')
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
            self.message_user(request, "Your file has been imported")
            return redirect("..")
        form = ImportForm()
        payload = {"form": form}
        return render(
            request, "form.html", payload
        )


@admin.register(DealerChoice)
class DealerChoiceAdmin(admin.ModelAdmin):
    icon_name = 'accessibility_new'
    change_list_template = "changelist_choice.html"

    list_display = ('donator', 'amount', 'source', 'when', 'during')
    list_filter = ('donator', 'source', 'when', 'during')

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('allocate/', self.allocate),
        ]
        return my_urls + urls

    def allocate(self, request):
        current_pool = DealerChoice.get_current_pool()
        if request.method == "POST":
            form = AllocateForm(request.POST)
            if form.is_valid():
                print(form.cleaned_data)
                if form.cleaned_data['amount'] <= current_pool:
                    a = Donation()
                    a.donator = Person.objects.get_or_create(slugname='runner', defaults={'username': 'Runner'})[0]
                    a.amount = form.cleaned_data['amount']
                    a.source = Donation.DonationSource.DEALER
                    a.interest = form.cleaned_data['choice']
                    a.save()
                    DealerChoice.subtract_from_pool(form.cleaned_data['amount'])
                    self.message_user(request, "Your amount was allocated")
                else:
                    self.message_user(request, "Allocation amount too high, try again", level=messages.ERROR)
            else:
                self.message_user(request, "Your amount was NOT allocated, try again", level=messages.ERROR)
            return redirect("..")
        form = AllocateForm()
        payload = {
            "form": form,
            'available': current_pool,
        }
        return render(
            request, "allocate.html", payload
        )


@admin.register(Variables)
class VariablesAdmin(admin.ModelAdmin):
    icon_name = 'settings_applications'

    list_display = ('variable', 'value')
    readonly_fields = ('variable',)
    fields = ('variable', 'value')

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False