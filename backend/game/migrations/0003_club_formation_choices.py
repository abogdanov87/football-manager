# Generated manually for T—Ж formation catalog.

from django.db import migrations, models

import game.formations


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0002_competition_club_crest_url_season_competition"),
    ]

    operations = [
        migrations.AlterField(
            model_name="club",
            name="formation",
            field=models.CharField(
                choices=game.formations.FORMATION_CHOICES,
                default="4-4-2",
                max_length=12,
            ),
        ),
    ]
