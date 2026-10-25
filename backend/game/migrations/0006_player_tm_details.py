from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0005_player_photo_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="contract_end_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="player",
            name="date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="player",
            name="nationality_countries",
            field=models.JSONField(blank=True, default=list),
        ),
    ]
