from rest_framework import serializers

from .formations import FORMATION_CHOICES
from .models import (
    Club,
    Competition,
    Fixture,
    Match,
    Player,
    PlayerCareerEntry,
    PlayerSeasonStat,
    Season,
    Standing,
)
from .player_contract import compute_contract_meta
from .player_stats import bootstrap_position_minutes, favorite_positions_top3


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = [
            "id",
            "name",
            "position",
            "age",
            "date_of_birth",
            "nationality_countries",
            "contract_end_date",
            "overall",
            "form",
            "transfermarkt_id",
            "transfermarkt_slug",
            "photo_url",
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
            "captain_player_id",
            "penalty_taker_player_id",
            "free_kick_taker_player_id",
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
        from .club_access import owned_club_for_user

        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return None
        club = owned_club_for_user(request.user)
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


class PlayerCareerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerCareerEntry
        fields = ["club_name", "from_date", "to_date", "source"]


class PlayerSeasonStatSerializer(serializers.ModelSerializer):
    season_name = serializers.CharField(source="season.name", read_only=True)

    class Meta:
        model = PlayerSeasonStat
        fields = [
            "season_name",
            "appearances",
            "minutes",
            "goals",
            "assists",
            "yellow_cards",
            "red_cards",
            "injury_days",
        ]


class PlayerDetailSerializer(PlayerSerializer):
    club = ClubSerializer(read_only=True)
    favorite_positions = serializers.SerializerMethodField()
    contract = serializers.SerializerMethodField()
    career = serializers.SerializerMethodField()
    season_stats = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    can_edit_roles = serializers.SerializerMethodField()

    class Meta(PlayerSerializer.Meta):
        fields = PlayerSerializer.Meta.fields + [
            "club",
            "favorite_positions",
            "contract",
            "career",
            "season_stats",
            "roles",
            "can_edit_roles",
        ]

    def get_favorite_positions(self, obj: Player) -> list:
        bootstrap_position_minutes(obj)
        return favorite_positions_top3(obj.id)

    def get_contract(self, obj: Player) -> dict:
        season = self.context.get("season")
        season_goals = season_assists = 0
        if season:
            stat = PlayerSeasonStat.objects.filter(season=season, player=obj).first()
            if stat:
                season_goals = stat.goals
                season_assists = stat.assists
        meta = compute_contract_meta(
            obj, season_goals=season_goals, season_assists=season_assists
        )
        return {
            "contract_end_date": meta["contract_end_date"],
            "years_remaining": meta["years_remaining"],
            "months_remaining": meta["months_remaining"],
            "renewal_status": meta["renewal_status"],
            "weekly_wage_usd": meta["weekly_wage_usd"],
            "yearly_wage_usd": meta["yearly_wage_usd"],
        }

    def get_career(self, obj: Player) -> list:
        qs = obj.career_entries.all()
        if not qs.exists() and obj.club_id:
            return [
                {
                    "club_name": obj.club.name,
                    "from_date": None,
                    "to_date": None,
                    "source": "game",
                }
            ]
        return PlayerCareerEntrySerializer(qs, many=True).data

    def get_season_stats(self, obj: Player) -> list:
        return PlayerSeasonStatSerializer(
            obj.season_stats.select_related("season").order_by("-season_id"), many=True
        ).data

    def get_roles(self, obj: Player) -> dict:
        club = obj.club
        return {
            "is_captain": club.captain_player_id == obj.id,
            "is_penalty_taker": club.penalty_taker_player_id == obj.id,
            "is_free_kick_taker": club.free_kick_taker_player_id == obj.id,
        }

    def get_can_edit_roles(self, obj: Player) -> bool:
        player_club_id = self.context.get("player_club_id")
        return bool(player_club_id and obj.club_id == player_club_id)


class ClubPlayerRolesSerializer(serializers.Serializer):
    captain_player_id = serializers.IntegerField(required=False, allow_null=True)
    penalty_taker_player_id = serializers.IntegerField(required=False, allow_null=True)
    free_kick_taker_player_id = serializers.IntegerField(required=False, allow_null=True)


class TacticsUpdateSerializer(serializers.Serializer):
    formation = serializers.ChoiceField(choices=[c[0] for c in FORMATION_CHOICES])
    lineup_player_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False, max_length=11
    )
