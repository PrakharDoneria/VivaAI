# VivaAI

VivaAI is an AI-powered interview platform for real-time candidate conversations and automated assessment. It combines WebRTC and Socket.IO for low-latency interview sessions and uses AI services for question generation, transcription, and final reporting.

## Tech Stack
- Python 3.11+
- Flask 3.x
- Flask-SocketIO 5.x
- Pydantic 2.x
- SQLite 3

## Prerequisites
- Python 3.11+
- Node.js 20 (for frontend tooling if added later; pinned via `.nvmrc`)
- `pip`

## Local Setup
1. Clone repo and enter it.
2. Create virtual environment.
3. Install dependencies.
4. Copy `.env.example` to `.env` and set secrets.
5. Run app.

```bash
python -m venv .venv
source .venv/bin/activate
make install
cp .env.example .env
make dev
```

## One-command Dev Run
```bash
make dev
```

## Common Tasks
```bash
make install
make dev
make test
make lint
```

## Environment Variables
| Name | Required | Default | Description |
|---|---|---|---|
| SECRET_KEY | Yes | - | Flask secret key |
| ENVIRONMENT | No | development | Runtime mode: development/staging/production |
| DEBUG | No | True | Flask debug mode |
| HOST | No | 0.0.0.0 | Server bind host |
| PORT | No | 5000 | Server port |
| DATABASE_PATH | No | database/vivaai.db | SQLite file path |
| AUDIO_FOLDER | No | static/audio/questions | Generated question audio path |
| ANSWERS_FOLDER | No | static/audio/answers | Candidate answer audio path |
| STUN_SERVER | No | stun:stun.l.google.com:19302 | WebRTC STUN server |
| CORS_ALLOWED_ORIGINS | No | * | Socket CORS allowed origins |
| SARVAM_API_KEY | No | empty | AI provider key |
| AI_PROVIDER | No | sarvam | AI provider selection |
| SARVAM_CHAT_MODEL | No | sarvam-m | Chat model |
| SARVAM_STT_MODEL | No | saarika:v2.5 | STT model |
| SARVAM_STT_LANGUAGE | No | en-IN | STT language |
| SARVAM_STT_CODEC | No | webm | STT input codec |
| AI_TEMPERATURE | No | 0.7 | Generation temperature |
| INTERVIEW_DURATION_MINUTES | No | 10 | Interview timer |
| MAX_QUESTIONS | No | 6 | Max generated questions |
| RATE_LIMIT_WINDOW_SECONDS | No | 60 | Window size for API throttling |
| RATE_LIMIT_AUTH_PER_WINDOW | No | 10 | Interview/create rate limit |
| RATE_LIMIT_AI_PER_WINDOW | No | 30 | AI endpoint rate limit |

## Running Tests
```bash
make test
```

## Contributing
- Branch from `main` using `feature/<name>` or `fix/<name>`.
- Keep commits atomic and scoped.
- Open PR with summary, tests, and rollback notes.
- Do not break API routes; add compatible aliases if needed.
