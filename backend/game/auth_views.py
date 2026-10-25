from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny

from .authentication import RequireAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .auth_otp import (
    OtpInvalid,
    OtpRateLimited,
    request_otp,
    revoke_all_tokens,
    revoke_token,
    verify_otp,
)
from .authentication import BearerTokenAuthentication
from .club_access import owned_club_for_user
from .models import Club
from .serializers import ClubSerializer


def _client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class OtpRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        if not email or "@" not in email:
            return Response(
                {"detail": "Укажите корректный email"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            request_otp(email, ip=_client_ip(request))
        except OtpRateLimited:
            return Response(
                {"detail": "Слишком много запросов. Попробуйте позже."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        return Response({"detail": "Если адрес корректен, мы отправили код на почту."})


class OtpVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        code = (request.data.get("code") or "").strip()
        if not email or not code:
            return Response(
                {"detail": "Нужны email и код"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user, token, raw = verify_otp(email, code)
        except OtpInvalid:
            return Response(
                {"detail": "Неверный или просроченный код"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        club = owned_club_for_user(user)
        return Response(
            {
                "token": raw,
                "expires_at": token.expires_at.isoformat(),
                "user": {"id": user.id, "email": user.email},
                "club_id": club.id if club else None,
            }
        )


class AuthMeView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [RequireAuthenticated]

    def get(self, request):
        club = owned_club_for_user(request.user)
        return Response(
            {
                "id": request.user.id,
                "email": request.user.email,
                "club_id": club.id if club else None,
            }
        )


class LogoutView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [RequireAuthenticated]

    def post(self, request):
        token = request.auth
        if token is not None:
            revoke_token(token)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutAllView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [RequireAuthenticated]

    def post(self, request):
        revoke_all_tokens(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AvailableClubsView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [RequireAuthenticated]

    def get(self, request):
        if owned_club_for_user(request.user):
            return Response([])
        clubs = Club.objects.filter(owner__isnull=True, is_player_controlled=False).order_by(
            "name"
        )
        return Response(ClubSerializer(clubs, many=True).data)


class ClaimClubView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [RequireAuthenticated]

    @transaction.atomic
    def post(self, request):
        if owned_club_for_user(request.user):
            return Response(
                {"detail": "У вас уже есть клуб"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        club_id = request.data.get("club_id")
        if not club_id:
            return Response(
                {"detail": "Укажите club_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        club = get_object_or_404(Club, pk=club_id)
        if club.owner_id is not None or club.is_player_controlled:
            return Response(
                {"detail": "Клуб уже занят"},
                status=status.HTTP_409_CONFLICT,
            )
        club.owner = request.user
        club.is_player_controlled = True
        club.save(update_fields=["owner", "is_player_controlled"])
        return Response(ClubSerializer(club).data)
