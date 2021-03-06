from datetime import timedelta

from django.utils.text import slugify
from django.utils.timezone import now

from pyexcel_ods import get_data

from .models import Person, Game, Donation


def process_odf(file):
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
            since = now() - timedelta(days=int(data[data_keys[0]][8][i]))
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
            k = 9
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