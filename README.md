# candidate-bot

A synthetic job candidate that joins a Daily.co room via Pipecat and answers interview questions as an LLM agent.

Used for end-to-end testing of the interview pipeline (`clone-for-online-meeting`) without a real human.

## Architecture

```
POST /join {room_url, candidate_name, resume_text, job_slug}
  → run_candidate_bot() [asyncio task]
    → DailyTransport.join(room_url)   # guest, no token needed
    → Pipecat pipeline:
        SileroVAD → Whisper STT → GPT-4o-mini → ElevenLabs TTS → Daily audio out
```

## Quick start

```bash
cp .env.example .env
# fill in DAILY_API_KEY, OPENAI_API_KEY, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID

pip install -r requirements.txt
python -m uvicorn src.main:app --reload --port 8080
```

## API

### `POST /join`

```json
{
  "room_url": "https://yourteam.daily.co/room-name",
  "candidate_name": "Alex",
  "resume_text": "Optional resume text — overrides persona file",
  "job_slug": "positive-junior"
}
```

`job_slug` maps to a file in `personas/<slug>.md`. If `resume_text` is provided, the persona file is ignored.

Returns immediately:
```json
{"status": "joining", "room_url": "...", "candidate": "Alex"}
```

### `GET /health`

```json
{"status": "ok"}
```

## Personas

| Slug | Description |
|------|-------------|
| `positive-junior` | Knows Python/OpenAI basics, wants the job, honest about gaps |
| `strong-senior` | 8 years exp, confident, no gaps |
| `weak-candidate` | Many gaps, over-claims, gets rejected |

## Docker

```bash
docker build -t candidate-bot .
docker run --env-file .env -p 8080:8080 candidate-bot
```

## Relation to interviewer-bot

`candidate-bot` is the synthetic other side of the `clone-for-online-meeting` interviewer. To run a full end-to-end test:

1. Create a Daily room (via `clone-for-online-meeting` or manually)
2. Start `clone-for-online-meeting` interviewer bot in the room
3. `POST /join` to this service with the same `room_url`
4. Watch the two bots interview each other
