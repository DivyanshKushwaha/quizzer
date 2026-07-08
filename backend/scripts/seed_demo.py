#!/usr/bin/env python3
"""
Seed demo data for QuizArena via the REST API.

Concept:
  1. Create one admin + several player accounts (or log in if they already exist)
  2. Admin creates a sample quiz with questions, timers, and prizes
  3. Each player registers for that quiz in the lobby
  4. Optionally start the quiz immediately (--start-now)

Requirements:
  - Backend running (default http://localhost:8000)
  - Postgres + Redis up

Usage:
  python backend/scripts/seed_demo.py
  python backend/scripts/seed_demo.py --start-now
  API_BASE=http://localhost:8000 python backend/scripts/seed_demo.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_BASE = os.getenv("API_BASE", "http://localhost:8000").rstrip("/")
PASSWORD = "Demo@123"

ADMIN = {
    "username": "demo_admin",
    "email": "admin@demo.local",
    "first_name": "Demo",
    "last_name": "Admin",
    "password": PASSWORD,
    "role": "admin",
}

PLAYERS = [
    {"username": "alice", "email": "alice@demo.local", "first_name": "Alice", "last_name": "K", "display_name": "Alice"},
    {"username": "bob", "email": "bob@demo.local", "first_name": "Bob", "last_name": "M", "display_name": "Bob"},
    {"username": "carol", "email": "carol@demo.local", "first_name": "Carol", "last_name": "R", "display_name": "Carol"},
]


def api_call(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        detail = exc.read().decode()
        try:
            detail = json.loads(detail).get("detail", detail)
        except Exception:
            pass
        raise RuntimeError(f"{method} {path} -> {exc.code}: {detail}") from exc


def register_or_login(user: dict) -> str:
    payload = {k: user[k] for k in ("username", "email", "first_name", "last_name", "password")}
    payload["role"] = user.get("role", "player")
    try:
        api_call("POST", "/auth/register", payload)
        print(f"  registered {user['email']}")
    except RuntimeError as err:
        if "already registered" not in str(err).lower():
            raise
        print(f"  exists, logging in: {user['email']}")
    tokens = api_call("POST", "/auth/login", {"email": user["email"], "password": user["password"]})
    return tokens["access_token"]


def build_quiz_body(start_at: str | None) -> dict:
    return {
        "title": "Demo Live Quiz",
        "description": "Seeded sample quiz — register, wait for start, compete live.",
        "settings": {
            "per_question_timer_sec": 20,
            "overall_timer_sec": 300,
            "win_condition": "score",
        },
        "prize": {"top3": "Gold badge", "top10": "Silver badge"},
        "start_at": start_at,
        "questions": [
            {
                "text": "What is 2 + 2?",
                "options": ["3", "4", "5", "22"],
                "correct_index": 1,
                "timer_sec": 15,
            },
            {
                "text": "Which planet is known as the Red Planet?",
                "options": ["Venus", "Mars", "Jupiter", "Saturn"],
                "correct_index": 1,
                "timer_sec": 20,
            },
            {
                "text": "What does HTTP stand for?",
                "options": [
                    "HyperText Transfer Protocol",
                    "High Transfer Text Program",
                    "Hyperlink Transmission Process",
                    "Host Transfer Terminal Protocol",
                ],
                "correct_index": 0,
                "timer_sec": 25,
            },
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Seed QuizArena demo data")
    parser.add_argument("--start-now", action="store_true", help="Start quiz immediately after seeding")
    parser.add_argument("--minutes", type=int, default=2, help="Schedule start N minutes from now (default: 2)")
    args = parser.parse_args()

    print(f"API: {API_BASE}\n")

    print("[1/4] Accounts")
    admin_token = register_or_login(ADMIN)
    player_tokens = []
    for p in PLAYERS:
        token = register_or_login({**p, "password": PASSWORD, "role": "player"})
        player_tokens.append((p, token))

    start_at = None if args.start_now else (datetime.now(timezone.utc) + timedelta(minutes=args.minutes)).isoformat()

    print("\n[2/4] Quiz")
    quiz = api_call("POST", "/quizzes", build_quiz_body(start_at), admin_token)
    quiz_id = quiz["id"]
    print(f"  created quiz id={quiz_id} status={quiz.get('status')}")
    if start_at:
        print(f"  scheduled start (UTC): {start_at}")
    else:
        print("  no schedule — use --start-now or POST /quizzes/{id}/start")

    if args.start_now:
        quiz = api_call("POST", f"/quizzes/{quiz_id}/start", {}, admin_token)
        print(f"  started quiz -> status={quiz.get('status')}")

    print("\n[3/4] Player registrations")
    for p, token in player_tokens:
        api_call("POST", f"/play/quizzes/{quiz_id}/register", {"display_name": p["display_name"]}, token)
        print(f"  {p['display_name']} registered")

    print("\n[4/4] Done\n")
    print("=" * 52)
    print("  DEMO CREDENTIALS (password for all: Demo@123)")
    print("=" * 52)
    print(f"  Admin : {ADMIN['email']}")
    for p in PLAYERS:
        print(f"  Player: {p['email']}  (display: {p['display_name']})")
    print()
    print(f"  Quiz ID : {quiz_id}")
    print(f"  Frontend: open /quizzes (players) or /admin (admin)")
    print(f"  Play URL: /quizzes/{quiz_id}/lobby")
    if not args.start_now and start_at:
        print(f"  Quiz goes live automatically ~{args.minutes} min after seed (scheduler).")
    print("=" * 52)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as err:
        print(f"\nSeed failed: {err}", file=sys.stderr)
        print("Is the backend running? Try: docker compose -f backend.yml up", file=sys.stderr)
        sys.exit(1)
