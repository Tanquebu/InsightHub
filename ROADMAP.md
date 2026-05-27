# InsightHub – Development Roadmap

## 🎯 Vision

InsightHub è una piattaforma backend per la gestione e analisi di dataset, con focus su:

* ingestion dati
* profiling
* metriche e insight
* pipeline scalabili

---

## ✅ Milestone 1 – Core Backend (IN PROGRESS)

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

* [ ] Validazione `status` dataset (enum)
* [ ] Error handling più strutturato
* [ ] Logging base
* [ ] Test base con pytest (min 2–3 test)
* [ ] README iniziale progetto

---

## 🚀 Milestone 2 – Data Processing

### Obiettivo

Gestire ingestion e processing asincrono dei dataset

### Task

* [ ] Setup Celery + Redis
* [ ] Worker async
* [ ] Job ingestion dataset
* [ ] Stato dataset (pending → processing → completed)
* [ ] Retry e gestione errori

---

## 🧠 Milestone 3 – Data Profiling

### Obiettivo

Generare insight automatici sui dataset

### Task

* [ ] Integrazione Pandas
* [ ] Profiling base:

  * [ ] numero righe
  * [ ] colonne
  * [ ] missing values
  * [ ] tipi dati
* [ ] Salvataggio metriche DB
* [ ] Endpoint API per risultati profiling

---

## 📊 Milestone 4 – Insight Engine

### Obiettivo

Costruire valore reale sui dati

### Task

* [ ] Metriche custom
* [ ] Regole di qualità dati
* [ ] Alert (es. anomalie)
* [ ] Prime feature ML (opzionale)

---

## ⚙️ Milestone 5 – Hardening

### Obiettivo

Rendere il progetto “production-ready”

### Task

* [ ] Autenticazione (JWT)
* [ ] Rate limiting
* [ ] Logging strutturato
* [ ] Monitoring
* [ ] CI/CD (GitHub Actions)
* [ ] Docker production-ready

---

## 🧪 Milestone 6 – Testing & Quality

* [ ] Test API (pytest)
* [ ] Test DB
* [ ] Coverage > 70%
* [ ] Linting pipeline CI

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
