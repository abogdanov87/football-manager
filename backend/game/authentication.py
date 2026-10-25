from __future__ import annotations

import hashlib

from django.utils import timezone
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import BasePermission

from .models import AuthToken


def hash_token_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class BearerTokenAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate_header(self, request):
        return self.keyword

    def authenticate(self, request):
        auth = request.headers.get("Authorization", "")
        if not auth:
            return None
        parts = auth.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None
        raw = parts[1].strip()
        if not raw:
            return None
        key_hash = hash_token_key(raw)
        token = (
            AuthToken.objects.select_related("user")
            .filter(key_hash=key_hash, revoked_at__isnull=True)
            .first()
        )
        if token is None or not token.is_active:
            raise exceptions.AuthenticationFailed("Недействительный или просроченный токен")
        AuthToken.objects.filter(pk=token.pk).update(last_used_at=timezone.now())
        return (token.user, token)


class RequireAuthenticated(BasePermission):
    """Missing or anonymous session → 401 (not DRF default 403)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated()
        return True
