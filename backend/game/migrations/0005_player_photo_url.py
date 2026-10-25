from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0004_player_transfermarkt_stats"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="photo_url",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
