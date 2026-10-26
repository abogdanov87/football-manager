import time
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from game.authentication import hash_token_key
from game.models import AuthToken, Club, EmailOtpChallenge
from game.auth_otp import _hash_code, verify_otp

User = get_user_model()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class OtpFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_request_sends_email(self):
        res = self.client.post("/api/auth/otp/request/", {"email": "test@example.com"}, format="json")
        self.assertEqual(res.status_code, 200)
        time.sleep(0.15)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("test@example.com", mail.outbox[0].to)

    def test_verify_invalid_code(self):
        EmailOtpChallenge.objects.create(
            email="test@example.com",
            code_hash=_hash_code("123456"),
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        res = self.client.post(
            "/api/auth/otp/verify/",
            {"email": "test@example.com", "code": "000000"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_verify_returns_token(self):
        EmailOtpChallenge.objects.create(
            email="player@example.com",
            code_hash=_hash_code("654321"),
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        res = self.client.post(
            "/api/auth/otp/verify/",
            {"email": "player@example.com", "code": "654321"},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("token", res.json())
        self.assertIn("expires_at", res.json())


class TokenAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u@test.com", email="u@test.com")
        self.raw = "test-secret-token-key-12345"
        self.token = AuthToken.objects.create(
            user=self.user,
            key_hash=hash_token_key(self.raw),
            expires_at=timezone.now() + timedelta(days=7),
        )
        self.client = APIClient()

    def test_me_requires_auth(self):
        res = self.client.get("/api/auth/me/")
        self.assertEqual(res.status_code, 401)

    def test_me_with_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.raw}")
        res = self.client.get("/api/auth/me/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["email"], "u@test.com")

    def test_logout_all_revokes_tokens(self):
        raw2 = "second-token-key-abcdefgh"
        AuthToken.objects.create(
            user=self.user,
            key_hash=hash_token_key(raw2),
            expires_at=timezone.now() + timedelta(days=7),
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.raw}")
        res = self.client.post("/api/auth/logout-all/")
        self.assertEqual(res.status_code, 204)
        self.assertEqual(
            AuthToken.objects.filter(user=self.user, revoked_at__isnull=True).count(), 0
        )


class ClaimClubTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="c@test.com", email="c@test.com")
        self.club = Club.objects.create(
            name="Free FC", short_name="FFC", is_player_controlled=False
        )
        self.taken = Club.objects.create(
            name="Taken FC",
            short_name="TFC",
            is_player_controlled=True,
            owner=User.objects.create_user(username="other@test.com", email="other@test.com"),
        )
        self.raw = "claim-test-token"
        AuthToken.objects.create(
            user=self.user,
            key_hash=hash_token_key(self.raw),
            expires_at=timezone.now() + timedelta(days=7),
        )
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.raw}")

    def test_claim_available_club(self):
        res = self.client.post("/api/clubs/claim/", {"club_id": self.club.id}, format="json")
        self.assertEqual(res.status_code, 200)
        self.club.refresh_from_db()
        self.assertEqual(self.club.owner_id, self.user.id)

    def test_claim_taken_returns_409(self):
        res = self.client.post("/api/clubs/claim/", {"club_id": self.taken.id}, format="json")
        self.assertEqual(res.status_code, 409)


class EmailTemplateTests(TestCase):
    def test_otp_template_renders_code(self):
        from django.template.loader import render_to_string

        html = render_to_string("emails/otp.html", {"code": "112233", "minutes": 10})
        self.assertIn("112233", html)
        text = render_to_string("emails/otp.txt", {"code": "112233", "minutes": 10})
        self.assertIn("112233", text)
