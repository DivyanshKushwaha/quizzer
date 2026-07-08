# QuizArena — Real-Time Multiplayer Quiz Platform

A full-stack live quiz application where an organizer creates timed quizzes, players register and compete in real time, and a server-driven leaderboard updates as answers are submitted. Results and prizes are revealed after the overall quiz ends.

---

## Features

### Admin (Quiz Organizer)
- Register and authenticate with an admin role
- Create, edit, and delete quizzes while in **draft**
- Add questions with multiple-choice options and a marked correct answer
- Configure per-question timer, overall quiz timer, and prize tiers (top 3 / top 10)
- Schedule a quiz start time — it auto-goes **live** at the scheduled moment
- View quiz status, created/started/ends times (displayed in IST)
- Real-time dashboard updates via WebSocket (status changes without refresh)
- Top 3 players with scores per live/finished quiz

### Player (Participant)
- Register and authenticate with a player role
- Browse upcoming and live quizzes
- Enter lobby, register with a display name, and wait for the quiz to start
- Answer questions one-by-one with **Next** / **Final Submit**
- See running score during play (correctness is **not** revealed mid-quiz)
- Live side panel: players currently playing, completed count, per-question progress
- Live leaderboard centered around the current player (±5 ranks) plus top 10 view
- Result screen with tier-based celebration (top 3, top 10, or finished) after the quiz ends

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | React 18, Vite, Tailwind CSS | Fast SPA with component-based UI |
| Backend | FastAPI (Python) | Async-friendly, clear routing, OpenAPI docs |
| Database | PostgreSQL | Source of truth for quizzes, attempts, answers |
| Cache / Real-time | Redis | Leaderboard ZSET, presence, pub/sub, per-question deadlines |
| Transport | WebSockets | Push notifications to refetch live data |
| Auth | JWT (access + refresh tokens) | Stateless role-based access (admin vs player) |
| Containers | Docker + Docker Compose | Reproducible local and deployment setup |

---

## Architecture

```
┌─────────────┐     REST + WS      ┌──────────────┐
│   React     │ ◄────────────────► │   FastAPI    │
│  (Browser)  │                    │   Backend    │
└─────────────┘                    └──────┬───────┘
                                          │
                         ┌────────────────┼────────────────┐
                         ▼                ▼                ▼
                   PostgreSQL           Redis          Background
                   (persistent)    (leaderboard,       scheduler
                                    pub/sub,           (auto start /
                                    deadlines)         auto finish)
```

### Data flow during play

1. Player clicks **Next** → `POST /play/quizzes/{id}/answer`
2. Backend validates server-side deadline, scores the answer, writes to Postgres
3. Redis leaderboard ZSET is updated
4. Redis pub/sub publishes `{ "type": "leaderboard" }` and `{ "type": "presence" }`
5. WebSocket manager broadcasts the signal to all clients in that quiz room
6. Frontend refetches leaderboard/presence via REST (WS carries signals, not full data)

### Real-time consistency

- **Leaderboard** lives in a Redis sorted set (`ZADD` / `ZREVRANGE`) — atomic under concurrency
- **Idempotency** guard (`SETNX`) prevents double-scoring the same question
- **Per-question deadlines** are set once in Redis with `NX` so refetching state cannot reset the timer
- **Presence counts** for the side panel are read from Postgres attempt rows for accuracy

### Server-authoritative timing

- Per-question timer: Redis key with TTL; server grants points only if the answer arrives before expiry
- Overall quiz timer: `ends_at` stored in UTC; background scheduler flips status to **finished** when time passes
- Client timers are display-only — they countdown to server-provided ISO deadlines

### Quiz lifecycle

```
draft → lobby → live → finished
```

| Status | Meaning |
|--------|---------|
| `draft` | Created by admin; visible to players if scheduled |
| `lobby` | At least one player registered; waiting for start |
| `live` | Quiz is running; players can join and answer |
| `finished` | Overall timer ended or all transitions complete; results available |

A background scheduler runs every 3 seconds to auto-start scheduled quizzes and auto-finish expired ones, then pushes WebSocket events so all connected clients refresh.

---

## Project Structure

```
one-shop-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, scheduler, routers
│   │   ├── init_tables.py           # Postgres schema bootstrap
│   │   ├── core/                    # DB config, auth, exceptions
│   │   └── features/
│   │       ├── routers/             # auth, quiz (admin), play, ws routes
│   │       ├── data_tools/          # Postgres + Redis data access
│   │       └── utils/               # play logic, quiz logic, ws manager
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── Pages/                   # Login, Browse, Lobby, Play, Result, Admin
│   │   ├── components/              # TopBar, Timer, Leaderboard, SidePanel
│   │   ├── hooks/useQuizSocket.js   # WebSocket subscription hook
│   │   └── api.js                   # Axios client + API helpers
│   └── Dockerfile
├── backend.yml                      # Postgres + Redis + backend
├── frontend.yml                     # Frontend (nginx)
└── backend/scripts/seed_demo.py     # Demo data script
```

---

## Database Schema (Postgres — `app_data` schema)

| Table | Purpose |
|-------|---------|
| `users` | Accounts with role (`admin` / `player`) |
| `refresh_tokens` | Refresh token storage |
| `quizzes` | Quiz metadata, questions (JSONB), settings, prize, status, timers |
| `registrations` | Player sign-ups per quiz |
| `attempts` | One row per player per quiz (score, progress, status) |
| `answers` | Individual question responses |

---

## API Overview

### Auth — `/auth`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/register` | Create account (role: admin or player) |
| POST | `/login` | Get access + refresh tokens |
| POST | `/logout` | Revoke refresh token |
| GET | `/me` | Current user info |

### Admin — `/quizzes` (requires admin role)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Create quiz |
| GET | `/` | List admin's quizzes |
| GET | `/{id}` | Get quiz (with answers) |
| PUT | `/{id}` | Update draft quiz |
| DELETE | `/{id}` | Delete draft quiz |
| POST | `/{id}/start` | Manually start quiz |

### Player — `/play` (requires player role)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/quizzes` | Browse available quizzes |
| GET | `/my/attempts` | Player's finished attempts |
| POST | `/quizzes/{id}/register` | Register for quiz |
| GET | `/quizzes/{id}/lobby` | Lobby state |
| POST | `/quizzes/{id}/join` | Enter live quiz |
| GET | `/quizzes/{id}/state` | Current play state |
| POST | `/quizzes/{id}/answer` | Submit answer / advance |
| GET | `/quizzes/{id}/leaderboard` | Window around current player |
| GET | `/quizzes/{id}/leaderboard/top` | Top 10 |
| GET | `/quizzes/{id}/presence` | Live activity counts |
| GET | `/quizzes/{id}/result` | Final result (after quiz ends) |

### WebSocket
| Path | Room | Events |
|------|------|--------|
| `/ws/feed` | global | `{ type: "feed" }` — browse page refresh |
| `/ws/quiz/{id}` | quiz id | `lobby`, `started`, `leaderboard`, `presence`, `finished` |

---

## Local Setup (Docker Compose)

Everything runs locally with Docker. No manual Postgres/Redis install needed.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)
- Python 3.11+ (only for running the optional seed script on your host)

### Step 1 — Start backend (Postgres + Redis + API)

From the project root:

```bash
docker compose -f backend.yml up --build
```

Wait until you see `Application startup complete` in the logs.

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Swagger docs | http://localhost:8000/docs |

Tables are created automatically on first startup (`init_tables.py`).

### Step 2 — Start frontend

Open a **second terminal**, still from the project root:

```bash
docker compose -f frontend.yml up --build
```

| Service | URL |
|---------|-----|
| Web app | http://localhost:5173 |

The frontend is built with `VITE_API_BASE=http://localhost:8000` so it talks to the local API.

### Step 3 — (Optional) Seed demo data

With the backend running, in a third terminal:

```bash
python backend/scripts/seed_demo.py --start-now
```

This creates an admin, 3 players, a sample quiz, and registers everyone. Password for all accounts: `Demo@123`.

| Role | Email |
|------|-------|
| Admin | `admin@demo.local` |
| Player | `alice@demo.local`, `bob@demo.local`, `carol@demo.local` |

Or skip seeding and register manually at http://localhost:5173/register.

### Step 4 — Play

1. Open http://localhost:5173
2. Log in as **admin** → create/manage quizzes at `/admin`
3. Log in as **player** in an incognito window → browse at `/quizzes`
4. Register in lobby → wait for quiz to go live → **Join now** → answer with **Next** / **Final Submit**

### Run tests (optional)

```bash
cd backend/app
pip install -r requirements.txt
python -m pytest tests/test_quiz_logic.py -v
```

### Stop everything

```bash
# Stop backend (Ctrl+C in that terminal, or:)
docker compose -f backend.yml down

# Stop frontend
docker compose -f frontend.yml down
```

Data persists in Docker volumes (`postgres_data`, `redis_data`) until you run `docker compose -f backend.yml down -v` (removes volumes).

### Frontend dev mode (optional, without Docker)

If you prefer hot reload during UI work:

```bash
cd frontend
npm install
npm run dev
```

Ensure the backend from Step 1 is still running. Default API URL is `http://localhost:8000`.

---

## Environment Variables

### Backend

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `postgres` | Database name |
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | — | Database password |
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_SCHEMA` | `app_data` | Application schema |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database index |
| `JWT_SECRET` | `change-me-in-production` | JWT signing secret |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_BASE` | `http://localhost:8000` | Backend API URL (baked at build time) |

---

## Seed Script (demo data)

With the backend running, one command creates accounts, a sample quiz, and player registrations:

```bash
python backend/scripts/seed_demo.py
```

Options:

| Flag | Effect |
|------|--------|
| `--start-now` | Admin starts the quiz immediately (skip scheduled wait) |
| `--minutes 5` | Schedule auto-start N minutes from now (default: 2) |
| `API_BASE=...` | Point at a non-default API URL |

**What it creates:**

1. **Admin** — `admin@demo.local` / `Demo@123`
2. **Players** — `alice@demo.local`, `bob@demo.local`, `carol@demo.local` (same password)
3. **Quiz** — 3 questions, 20s per question, 5 min overall, prizes for top 3 / top 10
4. **Registrations** — all three players registered for the quiz

Re-running is safe: existing emails are skipped and the script logs in instead.

After seeding, open the frontend, log in as a player in one browser and admin in another (or incognito), and play.

---

## Quick Demo Flow

1. **Register admin** at `/register` with role `admin`
2. **Create a quiz** at `/admin/quizzes/new` — add questions, set overall timer, schedule start time
3. **Register 2–3 players** (use incognito windows for separate sessions)
4. Players browse at `/quizzes`, enter lobby, register with display names
5. When the quiz goes **live** (scheduled or manual start), players click **Join now**
6. Answer questions with **Next** → **Final Submit**
7. Wait for overall quiz timer to end → result screen with rank and prize tier

---

## Design Decisions & Trade-offs

- **WS as signal, REST as data** — keeps payloads small and avoids stale cached state in WS frames
- **Redis for live leaderboard** — O(log N) rank updates; Postgres remains the audit trail
- **Scheduler polling (3s)** — simple and reliable for scheduled start/finish; not sub-second precise
- **Results gated on quiz end** — players see a waiting screen after Final Submit; leaderboard still updates live
- **IST display times** — stored as UTC in Postgres, converted to `HH:MM:SS` IST on fetch for admin/player lists

---

## Known Limitations

- Unit tests cover core `quiz_logic` only; no integration/API test suite yet
- Reconnection preserves attempt progress but per-question Redis deadline may expire during disconnect
- Quizzes without an overall timer (`ends_at = null`) will not auto-finish via the scheduler
- Backend production Dockerfile should include a `CMD` for uvicorn when deploying the pushed image outside Compose dev setup

---

