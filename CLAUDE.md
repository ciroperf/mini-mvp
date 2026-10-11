# mini-mvp

API FastAPI per note, con Postgres come fonte di verita' e Redis come
cache cache-aside, containerizzata.

Questo file viene letto a ogni run dell'agente. Tienilo sotto le 40 righe.

## Stack

- Python 3.12, FastAPI, SQLAlchemy async + asyncpg, Alembic
- Postgres 16, Redis 7
- Test: `pytest` (richiede Postgres e Redis su, vedi docker-compose.yml)
- Avvio locale: `docker compose up --build`

## Regole

1. Mai push su `main`. Branch, PR, stop.
2. Un compito, una PR. Niente refactor non richiesti.
3. Se il compito e' ambiguo: commenta la domanda sull'issue e fermati.
4. Leggi in modo mirato con Grep e Glob. Non aprire `__pycache__`,
   `.venv`, `dist`, `build`, `*.lock`.
5. Nessun segreto nel codice, nemmeno negli esempi. Usa `.env.example`
   per i nomi delle variabili, mai valori reali.
6. Nessuna dipendenza nuova senza scriverne il motivo nella PR: le
   dipendenze principali sono gia' in `requirements.txt`.

## Convenzioni

- Codice e identificatori in inglese, commenti in italiano.
- Commit in forma imperativa, una riga.
- Logica applicativa sotto `app/`, test sotto `tests/`, manifest
  Kubernetes sotto `k8s/`, migrazioni sotto `alembic/`.
- Scrittura: sempre su Postgres prima, poi invalida la cache Redis.
  Mai scrivere la cache come se fosse la fonte di verita'.

## Fatto quando

Una PR e' pronta se: `pytest` passa, il README riflette le novita', e
il comando indicato nel "Fatto quando" del compito da' il risultato
atteso.
