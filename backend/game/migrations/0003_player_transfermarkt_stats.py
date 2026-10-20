# Generated manually for Transfermarkt squad import

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0002_competition_club_crest_url_season_competition"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="aerial",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="player",
            name="defending",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="player",
            name="dri",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="player",
            name="injury_resistance",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="player",
            name="market_value_usd",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="player",
            name="mentality",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="player",
            name="pac",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="player",
            name="pas",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="player",
            name="phy",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="player",
            name="sho",
            field=models.PositiveSmallIntegerField(default=50),
        ),
        migrations.AddField(
            model_name="player",
            name="tm_position",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="player",
            name="transfermarkt_id",
            field=models.PositiveIntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="player",
            name="transfermarkt_slug",
            field=models.SlugField(blank=True, max_length=120),
        ),
    ]
