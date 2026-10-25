from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .authentication import hash_token_key
from .models import AuthToken, EmailOtpChallenge

User = get_user_model()

OTP_TTL_MINUTES = 10
TOKEN_TTL_DAYS = 7
OTP_MAX_ATTEMPTS = 5
EMAIL_RATE_LIMIT = 3
EMAIL_RATE_WINDOW = timedelta(minutes=15)
IP_RATE_LIMIT = 10


class OtpRateLimited(Exception):
    pass


class OtpInvalid(Exception):
    pass


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _check_rate_limits(email: str, ip: str | None) -> None:
    since = timezone.now() - EMAIL_RATE_WINDOW
    email_count = EmailOtpChallenge.objects.filter(
        email=email, created_at__gte=since
    ).count()
    if email_count >= EMAIL_RATE_LIMIT:
        raise OtpRateLimited()
    if ip:
        ip_count = EmailOtpChallenge.objects.filter(
            request_ip=ip, created_at__gte=since
        ).count()
        if ip_count >= IP_RATE_LIMIT:
            raise OtpRateLimited()


def request_otp(email: str, *, ip: str | None = None) -> None:
    email = _normalize_email(email)
    _check_rate_limits(email, ip)
    code = _generate_code()
    expires = timezone.now() + timedelta(minutes=OTP_TTL_MINUTES)
    EmailOtpChallenge.objects.filter(email=email, used_at__isnull=True).update(
        used_at=timezone.now()
    )
    EmailOtpChallenge.objects.create(
        email=email,
        code_hash=_hash_code(code),
        expires_at=expires,
        request_ip=ip,
    )
    html = render_to_string(
        "emails/otp.html",
        {"code": code, "minutes": OTP_TTL_MINUTES},
    )
    text = render_to_string(
        "emails/otp.txt",
        {"code": code, "minutes": OTP_TTL_MINUTES},
    )
    send_mail(
        subject="Код входа — Football Manager",
        message=text,
        from_email=None,
        recipient_list=[email],
        html_message=html,
    )


def verify_otp(email: str, code: str) -> tuple[User, AuthToken, str]:
    email = _normalize_email(email)
    challenge = (
        EmailOtpChallenge.objects.filter(email=email, used_at__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if challenge is None:
        raise OtpInvalid()
    if challenge.expires_at < timezone.now():
        raise OtpInvalid()
    if challenge.attempts >= OTP_MAX_ATTEMPTS:
        raise OtpInvalid()
    if _hash_code(code.strip()) != challenge.code_hash:
        challenge.attempts += 1
        challenge.save(update_fields=["attempts"])
        raise OtpInvalid()
    challenge.used_at = timezone.now()
    challenge.save(update_fields=["used_at"])

    user, _ = User.objects.get_or_create(
        username=email,
        defaults={"email": email},
    )
    if user.email != email:
        user.email = email
        user.save(update_fields=["email"])

    raw_token = secrets.token_urlsafe(32)
    token = AuthToken.objects.create(
        user=user,
        key_hash=hash_token_key(raw_token),
        expires_at=timezone.now() + timedelta(days=TOKEN_TTL_DAYS),
    )
    return user, token, raw_token


def revoke_token(token: AuthToken) -> None:
    token.revoked_at = timezone.now()
    token.save(update_fields=["revoked_at"])


def revoke_all_tokens(user: User) -> None:
    AuthToken.objects.filter(user=user, revoked_at__isnull=True).update(
        revoked_at=timezone.now()
    )
