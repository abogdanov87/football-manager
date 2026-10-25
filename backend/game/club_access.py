"""Resolve the authenticated user's club in the shared league."""

from django.contrib.auth.models import AbstractBaseUser

from .models import Club


def owned_club_for_user(user: AbstractBaseUser | None) -> Club | None:
    if user is None or not user.is_authenticated:
        return None
    return Club.objects.filter(owner=user, is_player_controlled=True).first()


def player_club_for_user(user: AbstractBaseUser) -> Club:
    club = owned_club_for_user(user)
    if club is None:
        raise Club.DoesNotExist("User has no claimed club")
    return club
