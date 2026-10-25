from django.urls import path

from . import auth_views, views

urlpatterns = [
    path("auth/otp/request/", auth_views.OtpRequestView.as_view(), name="auth-otp-request"),
    path("auth/otp/verify/", auth_views.OtpVerifyView.as_view(), name="auth-otp-verify"),
    path("auth/me/", auth_views.AuthMeView.as_view(), name="auth-me"),
    path("auth/logout/", auth_views.LogoutView.as_view(), name="auth-logout"),
    path("auth/logout-all/", auth_views.LogoutAllView.as_view(), name="auth-logout-all"),
    path("clubs/available/", auth_views.AvailableClubsView.as_view(), name="clubs-available"),
    path("clubs/claim/", auth_views.ClaimClubView.as_view(), name="clubs-claim"),
    path("season/current/", views.SeasonCurrentView.as_view(), name="season-current"),
    path("standings/", views.StandingsView.as_view(), name="standings"),
    path("clubs/<int:club_id>/squad/", views.SquadView.as_view(), name="squad"),
    path("clubs/<int:club_id>/tactics/", views.TacticsView.as_view(), name="tactics"),
    path("players/<int:player_id>/", views.PlayerDetailView.as_view(), name="player-detail"),
    path(
        "clubs/<int:club_id>/player-roles/",
        views.ClubPlayerRolesView.as_view(),
        name="club-player-roles",
    ),
    path("matchday/simulate/", views.MatchdaySimulateView.as_view(), name="matchday-simulate"),
]
