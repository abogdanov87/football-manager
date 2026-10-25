from django.core.management.base import BaseCommand

from game.player_stats import bootstrap_all_players


class Command(BaseCommand):
    help = "One-time 3000-minute position bootstrap for all players."

    def handle(self, *args, **options):
        n = bootstrap_all_players()
        self.stdout.write(self.style.SUCCESS(f"Bootstrapped {n} players."))
