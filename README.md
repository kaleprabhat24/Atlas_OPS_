# ATLAS-OPS

**Autonomous AI-Driven Payment Operations Platform**

ATLAS-OPS is a modern, production-grade Python platform for building resilient, scalable, AI-enabled payment operations and intelligent fraud/routing simulations. It combines real-time fraud detection, circuit-breaking, outage simulation, and LLM-powered payment failure explanations with robust logging and API-first design.

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [API Endpoints](#api-endpoints)
- [Machine Learning Integration](#machine-learning-integration)
- [Resilience & Reliability](#resilience--reliability)
- [Getting Started](#getting-started)
- [Environment Variables & Configuration](#environment-variables--configuration)
- [Development & Local Setup](#development--local-setup)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- 📈 **Real-Time Fraud Detection:** AI/ML models (custom or stub) score transactions for fraud risk.
- 🤖 **Intelligent Routing:** Selects optimal payment gateways via learned routing models.
- 🔄 **Resilient Architecture:** Uses circuit breakers around gateways, async Redis cache, and idempotent POST handling.
- 💥 **Outage Simulation:** Administrators can simulate gateway degradations and observe routing adaptation.
- 🧠 **Failure Explanation:** RAG/LLM-driven merchant explanations for failed transactions (openai/LangChain integration).
- 🏥 **Comprehensive Health Checks:** API endpoints for gateway/model/service health.
- 📑 **Structured Logging:** All logs formatted as JSON; designed for DevOps observability.
- 🧪 **Fully API-First:** Clean OpenAPI docs, consistent versioned routes, Python type annotations.

---

## Architecture Overview

Simplified flow:

1. **Client** submits a transaction to `/v1/transaction/process` (FastAPI).
2. **Fraud Detection (ML)**: Features extracted → ML model scores risk.
3. **Intelligent Routing:** System scores gateways (Stripe, Paypal, Razorpay, etc.) by health and ML model.
4. **Circuit Breakers:** Payments to unstable gateways are blocked.
5. **Payment Execution:** Success/failure recorded.
6. **Failure Diagnosis:** Root cause and ML SHAP values saved.
7. **LLM/RAG Explanation:** Merchant sees a natural language failure explanation.
8. **Idempotency:** Repeat POSTs with same key return cached response.

![](docs/atlas-ops-architecture.png) <!-- Placeholder for an architecture diagram if you have one -->

---

## API Endpoints

All endpoints are versioned under `/v1`:
- `POST /v1/transaction/process` — Process payment (fraud check, route, execute)
- `GET  /v1/transaction/{txn_id}` — Fetch transaction status
- `POST /v1/simulate/outage` — Admin: Simulate gateway outage/failure rate
- `DELETE /v1/simulate/outage/{gateway}` — Admin: Clear simulated outage
- `GET  /v1/gateways/health` — List detailed health metrics for all gateways
- `GET  /v1/transaction/{txn_id}/explain` — LLM-generated merchant explanations on failures
- `GET  /v1/ml/status` — ML model health/fallback status
- `GET  /health` — Service health

For interactive Docs, use:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Machine Learning Integration

- **Fraud/Failure/Routing Models:** Place your trained models as `fraud_model.pkl`, `failure_model.pkl`, `routing_model.pkl` in `app/ml_models/`.
- **Fallback:** If not present, dummy classifiers are auto-used so the API always works.
- **Model Features:** Feature schemas defined for fraud, failure, and routing. SHAP explainers auto-computed for transparency.

---

## Resilience & Reliability

- **Circuit Breakers:** (Powered by PyBreaker w/ Redis storage) — auto-isolates unhealthy gateways.
- **Idempotency:** All POST endpoints are idempotent (enforced via async Redis).
- **Gateway Outage Simulation:** Simulate/force open or close circuits or failure rates for dev/testing.
- **Async/Non-blocking:** All major subsystems are async for performance.

---

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL (running locally at `localhost:5432`)
- Redis (running locally at `localhost:6379`)

### Local Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/tailormst/Atlas_OPS.git
   cd Atlas_OPS
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database and Redis:**
   - Ensure PostgreSQL is running, and create the `atlas_ops` database.
   - Ensure Redis server is up.

4. **Prepare environment file:**
   ```
   cp .env.local.example .env
   # Edit the .env file and set your secrets (DB, Redis, OpenAI key, etc.)
   ```

5. **Check local setup:**
   ```
   python check_setup.py
   # Validates DB/Redis connection and model presence
   ```

6. **Run locally (dev mode):**
   ```bash
   python run_local.py
   # or directly:
   uvicorn app.main:app --reload
   ```

App will be available at `http://127.0.0.1:8000`.

---

## Environment Variables & Configuration

All config is loaded via `.env`. Main settings include:

- `DATABASE_URL` — Postgres connection string
- `REDIS_URL` — Redis connection string
- `FRAUD_MODEL_PATH`, `FAILURE_MODEL_PATH`, `ROUTING_MODEL_PATH` — ML model locations
- `OPENAI_API_KEY` — For LLM explanations (optional)
- `SECRET_KEY` — Admin API protection

See `.env.local.example` for full list of supported variables.

---

## Contributing

1. Fork and clone this repository.
2. Create a new branch for your feature or bugfix.
3. Follow PEP8 guidelines, and ensure proper typing/annotations.
4. All API/logic changes should include/update docstrings!
5. Submit a PR, explaining the context and purpose.

---

## License

This project is open-source and available under the MIT License.

---

## Acknowledgements

- Built using [FastAPI](https://fastapi.tiangolo.com/), [PostgreSQL](https://www.postgresql.org/), [Redis](https://redis.io/), [PyBreaker](https://pybreaker.readthedocs.io/), [scikit-learn](https://scikit-learn.org/), [SHAP](https://shap.readthedocs.io/), [LangChain](https://langchain.com/).
- LLM explanations powered by optional OpenAI API (via LangChain).
- Structured logging via [structlog](https://www.structlog.org/).

---

## Support

For any questions, open an issue in [GitHub Issues](https://github.com/tailormst/Atlas_OPS/issues).
