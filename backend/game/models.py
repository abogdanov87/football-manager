from django.conf import settings
from django.db import models


class Formation(models.TextChoices):
    F442 = "4-4-2", "4-4-2"
    F433 = "4-3-3", "4-3-3"


class Position(models.TextChoices):
    GK = "GK", "Вратарь"
    DEF = "DEF", "Защита"
    MID = "MID", "Полузащита"
    FWD = "FWD", "Нападение"


class Competition(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=64, unique=True)
    logo_url = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Club(models.Model):
    name = models.CharField(max_length=120)
    short_name = models.CharField(max_length=3)
    crest_url = models.CharField(max_length=255, blank=True)
    budget = models.PositiveIntegerField(default=5_000_000)
    stadium_capacity = models.PositiveIntegerField(default=15_000)
    is_player_controlled = models.BooleanField(default=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clubs",
    )
    formation = models.CharField(
        max_length=10, choices=Formation.choices, default=Formation.F442
    )
    lineup_player_ids = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Player(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="players")
    name = models.CharField(max_length=120)
    position = models.CharField(max_length=3, choices=Position.choices)
    age = models.PositiveSmallIntegerField(default=25)
    overall = models.PositiveSmallIntegerField(default=70)
    form = models.FloatField(default=1.0)

    class Meta:
        ordering = ["-overall", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.overall})"


class Season(models.Model):
    name = models.CharField(max_length=120)
    competition = models.ForeignKey(
        Competition,
        on_delete=models.PROTECT,
        related_name="seasons",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    current_matchday = models.PositiveSmallIntegerField(default=1)
    total_matchdays = models.PositiveSmallIntegerField(default=1)
    next_simulation_at = models.DateTimeField(null=True, blank=True)
    last_simulation_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    @property
    def is_complete(self) -> bool:
        if self.current_matchday > self.total_matchdays:
            return True
        if self.current_matchday == self.total_matchdays:
            return not self.fixtures.filter(
                matchday=self.current_matchday, is_played=False
            ).exists()
        return False

    def __str__(self) -> str:
        return self.name


class MatchdayRun(models.Model):
    """One row per calendar day when the league cron simulated a matchday."""

    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="matchday_runs")
    run_date = models.DateField()
    matchday = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-run_date"]
        unique_together = [("season", "run_date")]


class Fixture(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="fixtures")
    matchday = models.PositiveSmallIntegerField()
    home_club = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name="home_fixtures"
    )
    away_club = models.ForeignKey(
        Club, on_delete=models.CASCADE, related_name="away_fixtures"
    )
    is_played = models.BooleanField(default=False)

    class Meta:
        ordering = ["matchday", "id"]
        unique_together = [("season", "home_club", "away_club", "matchday")]

    def __str__(self) -> str:
        return f"{self.home_club.short_name} vs {self.away_club.short_name} (тур {self.matchday})"


class Match(models.Model):
    fixture = models.OneToOneField(
        Fixture, on_delete=models.CASCADE, related_name="match_result"
    )
    home_score = models.PositiveSmallIntegerField()
    away_score = models.PositiveSmallIntegerField()
    events = models.JSONField(default=list)
    engine_version = models.CharField(max_length=20, default="0.1")
    seed = models.CharField(max_length=64, blank=True)

    def __str__(self) -> str:
        return f"{self.home_score}:{self.away_score}"


class Standing(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="standings")
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name="standings")
    played = models.PositiveSmallIntegerField(default=0)
    won = models.PositiveSmallIntegerField(default=0)
    drawn = models.PositiveSmallIntegerField(default=0)
    lost = models.PositiveSmallIntegerField(default=0)
    goals_for = models.PositiveSmallIntegerField(default=0)
    goals_against = models.PositiveSmallIntegerField(default=0)
    points = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-points", "-goals_for", "club__name"]
        unique_together = [("season", "club")]

    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against

    def __str__(self) -> str:
        return f"{self.club.short_name}: {self.points} очков"
