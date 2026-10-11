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

## Test

Con Postgres e Redis gia' su (`docker compose up -d postgres redis`):

```bash
pip install -r requirements.txt
alembic upgrade head
pytest
```

## Screenshot

<!-- TODO: aggiungere uno screenshot o una demo (curl/HTTPie) dell'API in uso -->
