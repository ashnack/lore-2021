import glob, os

from django.core.management.base import BaseCommand

from lore2021.models import Game, Donation
from lore2021.utils import process_odf


class Command(BaseCommand):
    help = 'Import then export lists'

    def handle(self, *args, **options):
        os.chdir('files')
        Game.objects.all().delete()
        Donation.objects.all().delete()
        for file in glob.glob("*.ods"):
            process_odf(file)

        lore_choice = ""
        streaminations = ""

        for game in Game.games_for_list():
            string = '[wppb progress="' + str(int(game.percentage)) + '/100" funders="' + str(game.funders) + \
                     '" fullwidth=true text="' + game.name + ': $' + str(int(game.total)) + '" time_in_list=' + \
                     str(game.hours)
            if game.favorite:
                string += ' highlight="true"'
                lore_choice += string + "]\n"
            elif game.streamination:
                streaminations += string + "]\n"
            else:
                with open(game.game_length + "s.txt", 'a') as f:
                    f.write(string + "]\n")

        if lore_choice:
            with open("lore_choice.txt", 'a') as f:
                f.write(lore_choice)

        if streaminations:
            with open("streaminations.txt", 'a') as f:
                f.write(streaminations)
