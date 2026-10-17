from django.urls import path

from . import views

urlpatterns = [
    path("season/current/", views.SeasonCurrentView.as_view(), name="season-current"),
    path("standings/", views.StandingsView.as_view(), name="standings"),
    path("clubs/<int:club_id>/squad/", views.SquadView.as_view(), name="squad"),
    path("clubs/<int:club_id>/tactics/", views.TacticsView.as_view(), name="tactics"),
    path("matchday/simulate/", views.MatchdaySimulateView.as_view(), name="matchday-simulate"),
]
