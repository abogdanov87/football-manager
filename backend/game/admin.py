from django.contrib import admin

from .models import Club, Fixture, Match, MatchdayRun, Player, Season, Standing


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "is_player_controlled", "formation")


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "position", "overall")
    list_filter = ("position", "club")


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "is_active",
        "current_matchday",
        "total_matchdays",
        "next_simulation_at",
        "last_simulation_at",
    )


@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ("season", "matchday", "home_club", "away_club", "is_played")
    list_filter = ("season", "matchday", "is_played")


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("fixture", "home_score", "away_score")


@admin.register(Standing)
class StandingAdmin(admin.ModelAdmin):
    list_display = ("season", "club", "points", "played")


@admin.register(MatchdayRun)
class MatchdayRunAdmin(admin.ModelAdmin):
    list_display = ("season", "run_date", "matchday", "created_at")
