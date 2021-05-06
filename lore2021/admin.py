# ./manage.py admin_generator lore2021
# -*- coding: utf-8 -*-
from urllib import request, parse

from django.contrib import admin, messages
from django.db.models import Sum
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import path
from django.utils.safestring import mark_safe

from .forms import ImportForm, AllocateForm
from .models import Person, Game, Donation, DealerChoice, Variables
from .utils import process_odf


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
            path('search-feature/', self.search_feature),
        ]
        return my_urls + urls

    def for_website(self, request):
        return render(
            request,
            "website.html",
            {
                'games': Game.games_for_list()
            }
        )

    def search_feature(self, req):
        data = []
        with request.urlopen('https://lorerunner.com/reviews') as f:
            html = f.read().decode('utf-8')
            html = html[html.index('<tbody>'):html.index('</tbody')].split('</tr>')
            for line in html:
                if line:
                    line = line[line.index('href=')+6:line.index('</a>')]
                    if line:
                        data.append({
                            'label': parse.unquote(line[line.index('>')+1:]),
                            'url': parse.unquote(line[0:line.index('"')]),
                            'category': 'Reviewed',
                        })
        with request.urlopen('https://lorerunner.com/upcoming') as f:
            html = f.read().decode('utf-8')
            html = html[html.index('<ol>'):html.index('</ol>')].split('<li>')
            for line in html:
                if line:
                    line_split = line.split('</li>')
                    if len(line_split) == 2:
                        data.append({
                            'label': parse.unquote(line_split[0]),
                            'url': 'https://lorerunner.com/upcoming',
                            'category': 'Upcoming',
                        })
        for game in Game.objects.filter(ready=None).filter(to_export=True).filter(total__gt=0):
            data.append({
                'label': game.name,
                'url': 'https://lorerunner.com/the-list',
                'category': 'Not funded - ' + str(game.game_length),
            })
        return render(
            req,
            "search.html",
            {
                'data': data,
                'games': Game.objects.filter(ready=None)
                    .filter(to_export=True).filter(total__gt=0).order_by('glength', '-priority').all()
            }
        )

    def game_stats(self, request):
        game = get_object_or_404(Game, pk=int(request.GET.get('id', 0)))
        donations = Donation.objects.filter(interest=game).order_by('donator__slugname')
        donators = [d['donator__username'] for d in Donation.objects.filter(interest=game).values('donator__username').annotate(dsum=Sum('amount'))]
        return render(
            request,
            "stats.html",
            {
                'game': game,
                'donations': donations,
                'donators': ', '.join(donators),
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
            process_odf(file)
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