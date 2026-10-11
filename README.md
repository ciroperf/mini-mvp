# mini-mvp

API REST per gestire delle note (CRUD), con Postgres come fonte di verita'
e Redis come cache read-through (pattern cache-aside). Pensato come case
study end-to-end: container, CI, manifest Kubernetes e osservabilita' di
base. Per chi vuole un esempio minimo ma completo di backend cloud-native,
non per uso in produzione.

## Stack

- Python 3.12, FastAPI, Uvicorn
- SQLAlchemy (async) + asyncpg, migrazioni con Alembic
- Postgres 16 (dati), Redis 7 (cache)
- Docker multi-stage, Docker Compose per lo sviluppo locale
- Manifest Kubernetes (Deployment, Service, ConfigMap, Secret di esempio, HPA)
- Metriche Prometheus e log JSON strutturati
- Test: pytest

## Avvio in locale

```bash
cp .env.example .env
docker compose up --build
```

L'API risponde su `http://localhost:8000`. Verifica lo stato con:

```bash
curl http://localhost:8000/health
```

Le migrazioni Alembic vanno applicate manualmente dopo il primo avvio:

```bash
docker compose exec api alembic upgrade head
```

## API

CRUD sulle note, con sessione SQLAlchemy async su Postgres:

- `POST /notes` — crea una nota (`title`, `content`)
- `GET /notes` — elenca le note
- `GET /notes/{id}` — dettaglio di una nota (404 se non esiste)
- `PUT /notes/{id}` — aggiorna `title` e `content` di una nota (404 se non esiste)
- `DELETE /notes/{id}` — elimina una nota (404 se non esiste)

```bash
curl -X POST http://localhost:8000/notes \
  -H 'Content-Type: application/json' \
  -d '{"title": "Spesa", "content": "Latte e pane"}'
```

## Caching

`GET /notes` e `GET /notes/{id}` sono cache-aside su Redis (TTL 120s): in
caso di miss si legge da Postgres e si scrive in cache, altrimenti si
risponde direttamente dalla cache. Le scritture (`POST`/`PUT`/`DELETE`)
vanno sempre su Postgres per prime e poi invalidano le chiavi coinvolte,
cosi' la cache non diventa mai fonte di verita'. Se `REDIS_URL` non e'
impostata (es. nei test) si usa un fallback in-memory di processo.

## Osservabilita'

- `GET /metrics` espone le metriche in formato Prometheus (`text/plain`):
  numero di richieste HTTP (`http_requests_total`, per metodo/path/status),
  latenza delle richieste (`http_request_duration_seconds`) e accessi alla
  cache (`cache_requests_total`, per esito hit/miss).
- Ogni richiesta produce su stdout una riga di log JSON con timestamp,
  livello, path, status e durata in millisecondi (`duration_ms`).

## Test

Con Postgres e Redis gia' su (`docker compose up -d postgres redis`):

```bash
pip install -r requirements.txt
alembic upgrade head
pytest
```

## Screenshot

<!-- TODO: aggiungere uno screenshot o una demo (curl/HTTPie) dell'API in uso -->
