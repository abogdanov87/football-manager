from django.db import migrations


def release_unowned(apps, schema_editor):
    Club = apps.get_model("game", "Club")
    Club.objects.filter(owner__isnull=True).update(is_player_controlled=False)


class Migration(migrations.Migration):
    dependencies = [
        ("game", "0008_auth_otp"),
    ]

    operations = [
        migrations.RunPython(release_unowned, migrations.RunPython.noop),
    ]
