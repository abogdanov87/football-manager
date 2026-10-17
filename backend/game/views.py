from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Club, Player, Season
from .scheduler import run_scheduled_matchday
from .serializers import (
    ClubSerializer,
    PlayerSerializer,
    SeasonOverviewSerializer,
    StandingSerializer,
    TacticsUpdateSerializer,
)
from .models import Standing


def active_season() -> Season:
    season = Season.objects.filter(is_active=True).order_by("-id").first()
    if not season:
        raise Season.DoesNotExist("No active season")
    return season


def player_club() -> Club:
    club = Club.objects.filter(is_player_controlled=True).first()
    if not club:
        raise Club.DoesNotExist("No player club")
    return club


class SeasonCurrentView(APIView):
    def get(self, request):
        try:
            season = active_season()
        except Season.DoesNotExist:
            return Response(
                {"detail": "Нет активного сезона. Запустите seed_league."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(SeasonOverviewSerializer(season).data)


class StandingsView(APIView):
    def get(self, request):
        season = active_season()
        standings = Standing.objects.filter(season=season).select_related("club")
        return Response(StandingSerializer(standings, many=True).data)


class SquadView(APIView):
    def get(self, request, club_id: int):
        club = get_object_or_404(Club, pk=club_id)
        players = Player.objects.filter(club=club)
        return Response(
            {
                "club": ClubSerializer(club).data,
                "players": PlayerSerializer(players, many=True).data,
            }
        )


class TacticsView(APIView):
    def put(self, request, club_id: int):
        club = get_object_or_404(Club, pk=club_id)
        ser = TacticsUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        lineup_ids = ser.validated_data["lineup_player_ids"]
        valid_ids = set(
            Player.objects.filter(club=club, id__in=lineup_ids).values_list("id", flat=True)
        )
        if len(valid_ids) != len(lineup_ids):
            return Response(
                {"detail": "Состав содержит чужих игроков"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        club.formation = ser.validated_data["formation"]
        club.lineup_player_ids = lineup_ids
        club.save(update_fields=["formation", "lineup_player_ids"])
        return Response(ClubSerializer(club).data)


class MatchdaySimulateView(APIView):
    """Dev/admin only: manual cron trigger."""

    def post(self, request):
        if not settings.ALLOW_MANUAL_MATCHDAY_SIMULATION:
            return Response(
                {"detail": "Ручная симуляция отключена"},
                status=status.HTTP_403_FORBIDDEN,
            )
        force = request.data.get("force") is True or request.query_params.get("force") == "1"
        if not force and not (
            request.user.is_authenticated and request.user.is_staff
        ):
            # In DEBUG allow any client; in prod require staff unless force with secret - keep simple: staff or DEBUG
            if not settings.DEBUG:
                return Response(
                    {"detail": "Только для staff или включите DEBUG"},
                    status=status.HTTP_403_FORBIDDEN,
                )

        season = active_season()
        result = run_scheduled_matchday(season, force=force)
        season.refresh_from_db()
        return Response(
            {
                "status": result.status,
                "message": result.message,
                "matchday": result.matchday,
                "matches_played": result.matches_played,
                "season": SeasonOverviewSerializer(season).data,
            }
        )
