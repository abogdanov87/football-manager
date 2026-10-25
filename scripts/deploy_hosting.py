#!/usr/bin/env python3
"""
Deploy Football Manager to Reg.ru hosting (see .cursor/skills/hosting.env).

Default site: mr-manager.ru
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOSTING_ENV = ROOT / ".cursor/skills/hosting.env"
REPO_URL = "https://github.com/abogdanov87/football-manager.git"
DEFAULT_DOMAIN = "mr-manager.ru"

DOMAIN_TO_DEPLOY_DIR = {
    "mr-manager.ru": "mr-manager",
    "qolibri.ru": "qolibri",
}

SMTP_ENV_VARS = {
    "EMAIL_BACKEND": "django.core.mail.backends.smtp.EmailBackend",
    "EMAIL_HOST": "mail.hosting.reg.ru",
    "EMAIL_PORT": "587",
    "EMAIL_USE_TLS": "true",
    "EMAIL_USE_SSL": "false",
}


def load_hosting() -> tuple[str, str, str, str, str, str, str, str, str]:
    text = HOSTING_ENV.read_text(encoding="utf-8")
    ssh_user = re.search(r"Логин:\s*(\S+)", text).group(1)
    ssh_pass = re.search(r"Пароль:\s*(\S+)", text).group(1)
    host = re.search(r"IP-адрес сервера:\s*(\S+)", text).group(1)
    db_user = re.search(r"Доступ к MySQL[\s\S]*?Логин:\s*(\S+)", text).group(1)
    db_pass = re.search(r"Доступ к MySQL[\s\S]*?Пароль:\s*(\S+)", text).group(1)
    db_name = re.search(r"Имя базы:\s*(\S+)", text).group(1)
    mail_user = re.search(r"Почтовый клиент:[\s\S]*?Логин:\s*(\S+)", text).group(1)
    mail_pass = re.search(r"Почтовый клиент:[\s\S]*?Пароль:\s*(\S+)", text).group(1)
    return ssh_user, ssh_pass, host, db_user, db_pass, db_name, mail_user, mail_pass


def site_root(ssh_user: str, domain: str) -> str:
    return f"/var/www/{ssh_user}/data/www/{domain}"


def env_file_name() -> str:
    return "site.env"


def _merge_env_lines(lines: list[str], updates: dict[str, str]) -> list[str]:
    keys = set(updates)
    out: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in keys:
                out.append(f"{key}={updates[key]}")
                seen.add(key)
                continue
        out.append(line)
    for key, value in updates.items():
        if key not in seen:
            out.append(f"{key}={value}")
    return out


def build_frontend() -> Path:
    dist = ROOT / "frontend/dist"
    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (dist / "index.html").is_file():
        raise SystemExit("frontend/dist/index.html missing after build")
    return dist


def ssh_connect(host: str, user: str, password: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=60)
    return client


def run(client: paramiko.SSHClient, cmd: str) -> str:
    _, stdout, stderr = client.exec_command(cmd, timeout=600)
    out = stdout.read().decode()
    err = stderr.read().decode()
    code = stdout.channel.recv_exit_status()
    if code != 0:
        raise RuntimeError(f"Command failed ({code}): {cmd}\n{err}\n{out}")
    return out


def sftp_upload_dir(sftp: paramiko.SFTPClient, local: Path, remote: str) -> None:
    try:
        sftp.mkdir(remote)
    except OSError:
        pass
    for path in local.rglob("*"):
        rel = path.relative_to(local)
        remote_path = f"{remote}/{rel.as_posix()}"
        if path.is_dir():
            try:
                sftp.mkdir(remote_path)
            except OSError:
                pass
        else:
            parent = remote_path.rsplit("/", 1)[0]
            parts = parent.split("/")
            acc = ""
            for part in parts:
                if not part:
                    continue
                acc = f"{acc}/{part}" if acc else part
                try:
                    sftp.mkdir(acc)
                except OSError:
                    pass
            sftp.put(str(path), remote_path)


def sync_smtp_env_on_server(
    client: paramiko.SSHClient, root: str, mail_user: str, mail_pass: str
) -> None:
    env_path = f"{root}/{env_file_name()}"
    sftp = client.open_sftp()
    try:
        with sftp.file(env_path, "r") as remote:
            lines = remote.read().decode("utf-8").splitlines()
    except OSError:
        sftp.close()
        return
    updates = {
        **SMTP_ENV_VARS,
        "EMAIL_HOST_USER": mail_user,
        "EMAIL_HOST_PASSWORD": mail_pass,
        "DEFAULT_FROM_EMAIL": mail_user,
    }
    merged = _merge_env_lines(lines, updates)
    with sftp.file(env_path, "w") as remote:
        remote.write("\n".join(merged) + "\n")
    sftp.chmod(env_path, 0o600)
    sftp.close()


def ensure_env_on_server(
    client: paramiko.SSHClient,
    root: str,
    domain: str,
    db_user: str,
    db_pass: str,
    db_name: str,
    mail_user: str,
    mail_pass: str,
) -> None:
    env_path = f"{root}/{env_file_name()}"
    check = run(client, f"test -f {env_path} && echo yes || echo no").strip()
    if check == "yes":
        return
    secret = run(
        client,
        f"{root}/venv/bin/python -c \"import secrets; print(secrets.token_urlsafe(48))\" "
        f"2>/dev/null || /opt/python/python-3.12/bin/python3 -c "
        f"\"import secrets; print(secrets.token_urlsafe(48))\"",
    ).strip()
    hosts = f"{domain},www.{domain}"
    body = f"""DJANGO_DEBUG=false
DJANGO_SECRET_KEY={secret}
DJANGO_ALLOWED_HOSTS={hosts}
DJANGO_TIME_ZONE=Europe/Moscow
DB_ENGINE=mysql
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_pass}
DB_HOST=localhost
DB_PORT=3306
CORS_ALLOWED_ORIGINS=https://{domain},https://www.{domain}
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=mail.hosting.reg.ru
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_USE_SSL=false
EMAIL_HOST_USER={mail_user}
EMAIL_HOST_PASSWORD={mail_pass}
DEFAULT_FROM_EMAIL={mail_user}
ALLOW_MANUAL_MATCHDAY_SIMULATION=false
HOSTING_LEGACY_MYSQL=1
"""
    sftp = client.open_sftp()
    with sftp.file(env_path, "w") as f:
        f.write(body)
    sftp.chmod(env_path, 0o600)
    sftp.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default=DEFAULT_DOMAIN)
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--github-token", help="PAT or set GITHUB_TOKEN")
    parser.add_argument(
        "--sync-email-only",
        action="store_true",
        help="Update site.env SMTP from hosting.env and restart Passenger",
    )
    args = parser.parse_args()

    if not HOSTING_ENV.is_file():
        raise SystemExit(f"Missing {HOSTING_ENV}")

    domain = args.domain
    deploy_dir = DOMAIN_TO_DEPLOY_DIR.get(domain)
    if not deploy_dir:
        raise SystemExit(f"No deploy config for {domain}")

    ssh_user, ssh_pass, host, db_user, db_pass, db_name, mail_user, mail_pass = (
        load_hosting()
    )
    root = site_root(ssh_user, domain)

    if args.sync_email_only:
        client = ssh_connect(host, ssh_user, ssh_pass)
        sync_smtp_env_on_server(client, root, mail_user, mail_pass)
        run(client, f"mkdir -p {root}/tmp && touch {root}/tmp/restart.txt")
        client.close()
        print(f"SMTP synced to {root}/{env_file_name()}")
        return

    dist = ROOT / "frontend/dist" if args.skip_build else build_frontend()

    token = args.github_token or os.environ.get("GITHUB_TOKEN", "")
    clone_url = REPO_URL
    if token:
        clone_url = (
            f"https://x-access-token:{token}@github.com/abogdanov87/football-manager.git"
        )

    client = ssh_connect(host, ssh_user, ssh_pass)
    run(client, f"mkdir -p {root}/football-manager {root}/tmp")

    has_git = (
        run(
            client,
            f"test -d {root}/football-manager/.git && echo yes || echo no",
        ).strip()
        == "yes"
    )
    if not has_git:
        run(
            client,
            f"rm -rf {root}/football-manager && git clone {clone_url} {root}/football-manager",
        )
    else:
        if token:
            run(
                client,
                f"cd {root}/football-manager && git remote set-url origin {clone_url}",
            )
        try:
            run(
                client,
                f"cd {root}/football-manager && git fetch origin main && git reset --hard origin/main",
            )
        except RuntimeError:
            print("git fetch failed; uploading archive", file=sys.stderr)
            archive = subprocess.check_output(
                ["git", "archive", "--format=tar", "HEAD"],
                cwd=ROOT,
            )
            sftp = client.open_sftp()
            remote_tar = f"{root}/football-manager-sync.tar"
            with sftp.file(remote_tar, "wb") as remote:
                remote.write(archive)
            sftp.close()
            run(
                client,
                f"mkdir -p {root}/football-manager && "
                f"tar -xf {root}/football-manager-sync.tar -C {root}/football-manager && "
                f"rm -f {root}/football-manager-sync.tar",
            )

    deploy_path = f"{root}/football-manager/deploy/{deploy_dir}"
    run(client, f"cp {deploy_path}/passenger_wsgi.py {root}/passenger_wsgi.py")
    run(client, f"cp {deploy_path}/htaccess {root}/.htaccess")
    run(
        client,
        f"cp {deploy_path}/remote-update.sh {root}/remote-update.sh && chmod +x {root}/remote-update.sh",
    )

    run(
        client,
        f"grep -q '^DB_ENGINE=' {root}/{env_file_name()} 2>/dev/null || rm -f {root}/{env_file_name()}",
    )
    ensure_env_on_server(
        client, root, domain, db_user, db_pass, db_name, mail_user, mail_pass
    )
    sync_smtp_env_on_server(client, root, mail_user, mail_pass)
    run(
        client,
        f"grep -q '^HOSTING_LEGACY_MYSQL=' {root}/{env_file_name()} || "
        f"echo 'HOSTING_LEGACY_MYSQL=1' >> {root}/{env_file_name()}",
    )
    run(client, f"bash {root}/remote-update.sh")

    sftp = client.open_sftp()
    sftp.put(str(dist / "index.html"), f"{root}/index.html")
    sftp_upload_dir(sftp, dist / "assets", f"{root}/assets")
    public = ROOT / "frontend/public"
    for rel in ("favicon.svg", "icons.svg", "crests", "players"):
        local = public / rel
        if local.is_file():
            sftp.put(str(local), f"{root}/{rel}")
        elif local.is_dir():
            sftp_upload_dir(sftp, local, f"{root}/{rel}")
    sftp.close()

    run(client, f"mkdir -p {root}/tmp && touch {root}/tmp/restart.txt")
    client.close()
    print(f"Deploy complete: https://{domain}/")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc
