import glob, os

from django.core.management.base import BaseCommand, CommandError

from lore2021.models import Game
from lore2021.utils import process_odf


class Command(BaseCommand):
    help = 'Import then export lists'

    def handle(self, *args, **options):
        os.chdir('files')
        for file in glob.glob("*.ods"):
            process_odf(file)

        lore_choice = ""

        for game in Game.games_for_list():
            string = '[wppb progress="' + str(int(game.percentage) )+ '/100" funders="' + str(game.funders) + \
                     '" fullwidth=true text="' + game.name + ': $' + str(int(game.total)) + ', Time In List: ' + \
                     str(game.days_since()) + '"'
            if game.favorite:
                string += 'highlight="true"'
                lore_choice += string + "]\n"
            with open(game.game_length + "s.txt", 'a') as f:
                f.write(string + "]")

        if lore_choice:
            with open("lore_choice.txt", 'a') as f:
                f.write(lore_choice)
