from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny

from .authentication import RequireAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import BearerTokenAuthentication
from .club_access import owned_club_for_user, player_club_for_user
from .models import Club, Player, Season, Standing
from .scheduler import run_scheduled_matchday
from .serializers import (
    ClubPlayerRolesSerializer,
    ClubSerializer,
    PlayerDetailSerializer,
    PlayerSerializer,
    SeasonOverviewSerializer,
    StandingSerializer,
    TacticsUpdateSerializer,
)


def active_season() -> Season:
    season = Season.objects.filter(is_active=True).order_by("-id").first()
    if not season:
        raise Season.DoesNotExist("No active season")
    return season


class SeasonCurrentView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [RequireAuthenticated]

    def get(self, request):
        try:
            season = active_season()
        except Season.DoesNotExist:
            return Response(
                {"detail": "Нет активного сезона. Запустите seed_league."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            SeasonOverviewSerializer(season, context={"request": request}).data
        )


class StandingsView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [RequireAuthenticated]

    def get(self, request):
        season = active_season()
        standings = Standing.objects.filter(season=season).select_related("club")
        return Response(StandingSerializer(standings, many=True).data)


class SquadView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [RequireAuthenticated]

    def get(self, request, club_id: int):
        try:
            user_club = player_club_for_user(request.user)
        except Club.DoesNotExist:
            return Response(
                {"detail": "Сначала выберите клуб"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if club_id != user_club.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        club = get_object_or_404(Club, pk=club_id)
        players = Player.objects.filter(club=club)
        return Response(
            {
                "club": ClubSerializer(club).data,
                "players": PlayerSerializer(players, many=True).data,
            }
        )


class PlayerDetailView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [RequireAuthenticated]

    def get(self, request, player_id: int):
        try:
            season = active_season()
            user_club = player_club_for_user(request.user)
        except (Season.DoesNotExist, Club.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)
        player = get_object_or_404(Player.objects.select_related("club"), pk=player_id)
        if player.club_id != user_club.id:
            return Response(
                {"detail": "Профиль доступен только для игроков вашего клуба"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(
            PlayerDetailSerializer(
                player,
                context={"season": season, "player_club_id": user_club.id},
            ).data
        )


class ClubPlayerRolesView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [RequireAuthenticated]

    def patch(self, request, club_id: int):
        try:
            user_club = player_club_for_user(request.user)
        except Club.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if club_id != user_club.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        club = get_object_or_404(Club, pk=club_id)
        ser = ClubPlayerRolesSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        squad_ids = set(club.players.values_list("id", flat=True))

        def _check(pid: int | None) -> bool:
            return pid is None or pid in squad_ids

        for key in ("captain_player_id", "penalty_taker_player_id", "free_kick_taker_player_id"):
            if key in data and not _check(data[key]):
                return Response(
                    {"detail": f"Недопустимый игрок для {key}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if "captain_player_id" in data:
            club.captain_player_id = data["captain_player_id"]
        if "penalty_taker_player_id" in data:
            club.penalty_taker_player_id = data["penalty_taker_player_id"]
        if "free_kick_taker_player_id" in data:
            club.free_kick_taker_player_id = data["free_kick_taker_player_id"]
        club.save(
            update_fields=[
                "captain_player_id",
                "penalty_taker_player_id",
                "free_kick_taker_player_id",
            ]
        )
        return Response(ClubSerializer(club).data)


class TacticsView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [RequireAuthenticated]

    def put(self, request, club_id: int):
        try:
            user_club = player_club_for_user(request.user)
        except Club.DoesNotExist:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if club_id != user_club.id:
            return Response(status=status.HTTP_403_FORBIDDEN)
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

    permission_classes = [AllowAny]

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
                "season": SeasonOverviewSerializer(
                    season, context={"request": request}
                ).data,
            }
        )
