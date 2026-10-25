#!/usr/bin/env python3
"""
Deploy Football Manager to qolibri.ru from GitHub.

- git pull on the server (football-manager/)
- pip install, migrate, collectstatic, Passenger restart
- upload frontend dist + public assets to site root

Requires: paramiko, local frontend build (npm run build).
Reads SSH credentials from .cursor/skills/hosting.env (not committed).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
HOSTING_ENV = ROOT / ".cursor/skills/hosting.env"
SITE_ROOT = "/var/www/u2662691/data/www/qolibri.ru"
REPO_URL = "https://github.com/abogdanov87/football-manager.git"
HOST = "31.31.196.253"


def load_hosting() -> tuple[str, str, str, str, str, str]:
    text = HOSTING_ENV.read_text(encoding="utf-8")
    ssh_user = re.search(r"Логин:\s*(\S+)", text).group(1)
    ssh_pass = re.search(r"Пароль:\s*(\S+)", text).group(1)
    db_user = re.search(r"Доступ к MySQL[\s\S]*?Логин:\s*(\S+)", text).group(1)
    db_pass = re.search(r"Доступ к MySQL[\s\S]*?Пароль:\s*(\S+)", text).group(1)
    db_name = re.search(r"Имя базы:\s*(\S+)", text).group(1)
    return ssh_user, ssh_pass, db_user, db_pass, db_name


def build_frontend() -> Path:
    dist = ROOT / "frontend/dist"
    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (dist / "index.html").is_file():
        raise SystemExit("frontend/dist/index.html missing after build")
    return dist


def ssh_connect(user: str, password: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=user, password=password, timeout=60)
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


def ensure_env_on_server(
    client: paramiko.SSHClient, db_user: str, db_pass: str, db_name: str
) -> None:
    env_path = f"{SITE_ROOT}/qolibri.env"
    check = run(client, f"test -f {env_path} && echo yes || echo no").strip()
    if check == "yes":
        return
    secret = run(
        client,
        f"{SITE_ROOT}/venv/bin/python -c \"import secrets; print(secrets.token_urlsafe(48))\" "
        f"2>/dev/null || /opt/python/python-3.12/bin/python3 -c "
        f"\"import secrets; print(secrets.token_urlsafe(48))\"",
    ).strip()
    body = f"""DJANGO_DEBUG=false
DJANGO_SECRET_KEY={secret}
DJANGO_ALLOWED_HOSTS=qolibri.ru,www.qolibri.ru
DJANGO_TIME_ZONE=Europe/Moscow
DB_ENGINE=mysql
DB_NAME={db_name}
DB_USER={db_user}
DB_PASSWORD={db_pass}
DB_HOST=localhost
DB_PORT=3306
CORS_ALLOWED_ORIGINS=https://qolibri.ru,https://www.qolibri.ru
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@qolibri.ru
ALLOW_MANUAL_MATCHDAY_SIMULATION=false
"""
    sftp = client.open_sftp()
    with sftp.file(env_path, "w") as f:
        f.write(body)
    sftp.chmod(env_path, 0o600)
    sftp.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Use existing frontend/dist",
    )
    parser.add_argument(
        "--github-token",
        help="PAT for private repo clone/pull on server (or set GITHUB_TOKEN)",
    )
    args = parser.parse_args()

    if not HOSTING_ENV.is_file():
        raise SystemExit(f"Missing {HOSTING_ENV}")

    ssh_user, ssh_pass, db_user, db_pass, db_name = load_hosting()
    dist = ROOT / "frontend/dist" if args.skip_build else build_frontend()

    token = args.github_token or __import__("os").environ.get("GITHUB_TOKEN", "")
    clone_url = REPO_URL
    if token:
        clone_url = f"https://x-access-token:{token}@github.com/abogdanov87/football-manager.git"

    client = ssh_connect(ssh_user, ssh_pass)

    run(
        client,
        f"mkdir -p {SITE_ROOT}/football-manager {SITE_ROOT}/tmp",
    )
    has_git = (
        run(
            client,
            f"test -d {SITE_ROOT}/football-manager/.git && echo yes || echo no",
        ).strip()
        == "yes"
    )
    if not has_git:
        run(
            client,
            f"rm -rf {SITE_ROOT}/football-manager && git clone {clone_url} {SITE_ROOT}/football-manager",
        )
    else:
        if token:
            run(
                client,
                f"cd {SITE_ROOT}/football-manager && git remote set-url origin {clone_url}",
            )
        try:
            run(
                client,
                f"cd {SITE_ROOT}/football-manager && git fetch origin main && git reset --hard origin/main",
            )
        except RuntimeError:
            print("git fetch failed; uploading archive from local checkout", file=sys.stderr)
            archive = subprocess.check_output(
                ["git", "archive", "--format=tar", "HEAD"],
                cwd=ROOT,
            )
            sftp = client.open_sftp()
            remote_tar = f"{SITE_ROOT}/football-manager-sync.tar"
            with sftp.file(remote_tar, "wb") as remote:
                remote.write(archive)
            sftp.close()
            run(
                client,
                f"mkdir -p {SITE_ROOT}/football-manager && "
                f"tar -xf {SITE_ROOT}/football-manager-sync.tar -C {SITE_ROOT}/football-manager && "
                f"rm -f {SITE_ROOT}/football-manager-sync.tar",
            )

    # Site wiring files from repo
    run(
        client,
        f"cp {SITE_ROOT}/football-manager/deploy/qolibri/passenger_wsgi.py {SITE_ROOT}/passenger_wsgi.py",
    )
    run(
        client,
        f"cp {SITE_ROOT}/football-manager/deploy/qolibri/htaccess {SITE_ROOT}/.htaccess",
    )
    run(
        client,
        f"cp {SITE_ROOT}/football-manager/deploy/qolibri/remote-update.sh {SITE_ROOT}/remote-update.sh && chmod +x {SITE_ROOT}/remote-update.sh",
    )

    run(
        client,
        f"grep -q '^DB_ENGINE=' {SITE_ROOT}/qolibri.env 2>/dev/null || rm -f {SITE_ROOT}/qolibri.env",
    )
    ensure_env_on_server(client, db_user, db_pass, db_name)
    run(client, f"bash {SITE_ROOT}/remote-update.sh")

    sftp = client.open_sftp()
    for name in ("index.html",):
        sftp.put(str(dist / name), f"{SITE_ROOT}/{name}")
    sftp_upload_dir(sftp, dist / "assets", f"{SITE_ROOT}/assets")
    public = ROOT / "frontend/public"
    for rel in ("favicon.svg", "icons.svg", "crests", "players"):
        local = public / rel
        if local.is_file():
            sftp.put(str(local), f"{SITE_ROOT}/{rel}")
        elif local.is_dir():
            sftp_upload_dir(sftp, local, f"{SITE_ROOT}/{rel}")
    sftp.close()

    run(client, f"mkdir -p {SITE_ROOT}/tmp && touch {SITE_ROOT}/tmp/restart.txt")
    client.close()
    print("Deploy complete: https://qolibri.ru/")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc
