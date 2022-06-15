from datetime import timedelta, date

from django.utils.text import slugify
from django.utils.timezone import now

from pyexcel_ods3 import get_data

from .models import Person, Game, Donation


def process_odf(file):
    data = get_data(file)
    data_keys = list(data.keys())
    i = 0
    data_length = len(data[data_keys[0]][4])
    priority_list_user = Person.objects.get_or_create(slugname="prioritylistfakeuser", username="Priority List (fake user)")[0]
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
            if isinstance(data[data_keys[0]][8][i], date):
                since = data[data_keys[0]][8][i]
            else:
                since = now() - timedelta(days=int(data[data_keys[0]][8][i]))
            game, created = Game.objects.get_or_create(
                name=text,
                defaults={
                    'glength': j,
                    'hours': sorter,
                    'favorite': True if lore_choice == 'x' else False,
                    'streamination': True if lore_choice == 'z' else False,
                    'added': since,
                    'priority_needed': data[data_keys[0]][2][i],
                    'days_since_change': data[data_keys[0]][10][i],
                }
            )
            if not created:
                game.added = since
                game.priority_needed = data[data_keys[0]][2][i]
                game.save()
                Donation.objects.filter(interest=game).filter(source=9).delete()
            k = 11
            if data[data_keys[0]][k][i]:
                try:
                    while data[data_keys[0]][k][i]:
                        if data[data_keys[0]][k][i]:
                            label = data[data_keys[0]][k][i]
                            label_test = label.split(' ')
                            donation = 2.0
                            if len(label_test) > 1 and label_test[-1] and label_test[-1].isnumeric() and int(label_test[-1]) > 0:
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
                except IndexError:
                    pass

            if game.total < data[data_keys[0]][4][i]:
                missing_money = data[data_keys[0]][4][i] - game.total
                donation_object = Donation(
                    amount=missing_money,
                    source=9,
                    donator=priority_list_user,
                    during=None,
                    interest=game,
                )
                donation_object.save({'dnu': True})

            game.update_calc()
        i += 1
