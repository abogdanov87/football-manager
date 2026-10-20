from rest_framework import serializers

from .models import Club, Competition, Fixture, Match, Player, Season, Standing


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = [
            "id",
            "name",
            "position",
            "age",
            "overall",
            "form",
            "transfermarkt_id",
            "transfermarkt_slug",
            "tm_position",
            "market_value_usd",
            "pac",
            "sho",
            "pas",
            "dri",
            "defending",
            "phy",
            "aerial",
            "mentality",
            "injury_resistance",
        ]


class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = ["id", "name", "slug", "logo_url"]


class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = [
            "id",
            "name",
            "short_name",
            "crest_url",
            "budget",
            "stadium_capacity",
            "is_player_controlled",
            "formation",
            "lineup_player_ids",
        ]


class StandingSerializer(serializers.ModelSerializer):
    club = ClubSerializer(read_only=True)
    goal_difference = serializers.IntegerField(read_only=True)

    class Meta:
        model = Standing
        fields = [
            "club",
            "played",
            "won",
            "drawn",
            "lost",
            "goals_for",
            "goals_against",
            "goal_difference",
            "points",
        ]


class MatchSerializer(serializers.ModelSerializer):
    home_club = serializers.CharField(source="fixture.home_club.name", read_only=True)
    away_club = serializers.CharField(source="fixture.away_club.name", read_only=True)
    home_short = serializers.CharField(source="fixture.home_club.short_name", read_only=True)
    away_short = serializers.CharField(source="fixture.away_club.short_name", read_only=True)
    matchday = serializers.IntegerField(source="fixture.matchday", read_only=True)

    class Meta:
        model = Match
        fields = [
            "id",
            "matchday",
            "home_club",
            "away_club",
            "home_short",
            "away_short",
            "home_score",
            "away_score",
            "events",
        ]


class FixtureSerializer(serializers.ModelSerializer):
    home_club = ClubSerializer(read_only=True)
    away_club = ClubSerializer(read_only=True)

    class Meta:
        model = Fixture
        fields = [
            "id",
            "matchday",
            "home_club",
            "away_club",
            "is_played",
        ]


class SeasonOverviewSerializer(serializers.ModelSerializer):
    competition = CompetitionSerializer(read_only=True)
    standings = StandingSerializer(many=True, read_only=True)
    player_club_id = serializers.SerializerMethodField()
    recent_matches = serializers.SerializerMethodField()
    upcoming_fixtures = serializers.SerializerMethodField()
    manual_simulation_allowed = serializers.SerializerMethodField()

    class Meta:
        model = Season
        fields = [
            "id",
            "name",
            "competition",
            "is_active",
            "is_complete",
            "current_matchday",
            "total_matchdays",
            "next_simulation_at",
            "last_simulation_at",
            "standings",
            "player_club_id",
            "recent_matches",
            "upcoming_fixtures",
            "manual_simulation_allowed",
        ]

    def get_player_club_id(self, obj: Season) -> int | None:
        club = Club.objects.filter(is_player_controlled=True).first()
        return club.id if club else None

    def get_recent_matches(self, obj: Season) -> list:
        matches = (
            Match.objects.filter(fixture__season=obj, fixture__is_played=True)
            .select_related("fixture__home_club", "fixture__away_club")
            .order_by("-fixture__matchday", "-id")[:12]
        )
        return MatchSerializer(matches, many=True).data

    def get_upcoming_fixtures(self, obj: Season) -> list:
        fixtures = (
            Fixture.objects.filter(season=obj, matchday=obj.current_matchday, is_played=False)
            .select_related("home_club", "away_club")
            .order_by("id")
        )
        return FixtureSerializer(fixtures, many=True).data

    def get_manual_simulation_allowed(self, _obj: Season) -> bool:
        from django.conf import settings

        return bool(settings.ALLOW_MANUAL_MATCHDAY_SIMULATION)


class TacticsUpdateSerializer(serializers.Serializer):
    formation = serializers.ChoiceField(choices=["4-4-2", "4-3-3"])
    lineup_player_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False, max_length=11
    )
