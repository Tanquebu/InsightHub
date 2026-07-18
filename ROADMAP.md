# InsightHub – Development Roadmap

## 🎯 Vision

InsightHub è una piattaforma backend per la gestione e analisi di dataset, con focus su:

* ingestion dati
* profiling
* metriche e insight
* pipeline scalabili

---

## ✅ Milestone 1 – Core Backend (COMPLETE)

### ✔️ Ambiente e Setup

* [x] DevContainer (Docker + VS Code)
* [x] Python 3.11 + Poetry
* [x] FastAPI setup
* [x] PostgreSQL + Redis
* [x] Ruff + Black + Pylance

---

### ✔️ Database & Persistence

* [x] Setup SQLAlchemy (sync)
* [x] Setup Alembic
* [x] Prima migration
* [x] Modello `Project`
* [x] Modello `Dataset`

---

### ✔️ Projects API

* [x] Create Project
* [x] List Projects
* [x] Get Project
* [x] Delete Project
* [x] Service layer separato

---

### ✔️ Datasets API

* [x] Create Dataset
* [x] List Datasets by Project
* [x] Get Dataset
* [x] Update Dataset
* [x] Delete Dataset

---

### 🔜 Da completare (Milestone 1)

* [x] Validazione `status` dataset (Literal type)
* [x] Error handling più strutturato (global exception handler)
* [x] Logging base (structlog)
* [x] Test base con pytest (10 test: 5 projects + 5 datasets)
* [x] README iniziale progetto

---

## 🚀 Milestone 2 – Data Processing (COMPLETE)

### Obiettivo

Gestire ingestion e processing asincrono dei dataset

### Task

* [x] Setup Celery + Redis
* [x] Worker async
* [x] Job ingestion dataset (endpoint `POST /datasets/{id}/ingest`)
* [x] Stato dataset (pending → processing → completed/failed)
* [x] Retry e gestione errori (`self.retry` con max retries e countdown configurabili)

---

## 🧠 Milestone 3 – Data Profiling (COMPLETE)

### Obiettivo

Generare insight automatici sui dataset

### Task

* [x] Integrazione Pandas
* [x] Profiling base:

  * [x] numero righe
  * [x] colonne
  * [x] missing values
  * [x] tipi dati
* [x] Salvataggio metriche DB
* [x] Endpoint API per risultati profiling

---

## 📊 Milestone 4 – Insight Engine

### Obiettivo

Costruire valore reale sui dati

### Task

* [x] Metriche custom
* [x] Regole di qualità dati
* [x] Alert (es. anomalie)
* [ ] Prime feature ML (opzionale) — esplicitamente opzionale, non implementata in questa milestone

---

## ⚙️ Milestone 5 – Hardening (COMPLETE)

### Obiettivo

Rendere il progetto “production-ready”

### Task

* [x] Autenticazione (JWT)
* [x] Rate limiting
* [x] Logging strutturato
* [x] Monitoring
* [x] CI/CD (GitHub Actions)
* [x] Docker production-ready

---

## 🧪 Milestone 6 – Testing & Quality (COMPLETE)

* [x] Test API (pytest)
* [x] Test DB
* [x] Coverage > 70%
* [x] Linting pipeline CI

---

## 🌐 Milestone 7 – Frontend (opzionale)

* [ ] Dashboard React
* [ ] Visualizzazione dataset
* [ ] Insight UI

---

## 🧭 Note Tecniche

### Stack attuale

* FastAPI
* SQLAlchemy
* Alembic
* PostgreSQL
* Redis
* Poetry
* Docker / DevContainer

### Architettura

* `api/` → routing
* `services/` → business logic
* `schemas/` → Pydantic
* `db/` → models + session

---

## 📌 Regole del progetto

* Commit semantici (feat, fix, chore)
* Service layer obbligatorio
* No logica nei router
* Tipizzazione dove possibile
* Codice leggibile > codice “furbo”

---

## 🔥 Obiettivo finale

Costruire un progetto:

* riusabile come portfolio
* scalabile
* base per SaaS futuro

---
