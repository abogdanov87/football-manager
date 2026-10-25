from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0009_release_unowned_clubs"),
    ]

    operations = [
        migrations.AddField(
            model_name="playermatchappearance",
            name="injury_days",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="playermatchappearance",
            name="red_cards",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="playermatchappearance",
            name="yellow_cards",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="playerseasonstat",
            name="injury_days",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="playerseasonstat",
            name="red_cards",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="playerseasonstat",
            name="yellow_cards",
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
