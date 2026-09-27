# ATLAS-OPS

**Autonomous AI-Driven Payment Operations Platform**

ATLAS-OPS is a modern, production-grade Python platform for building resilient, scalable, AI-enabled payment operations and intelligent fraud/routing simulations. It combines real-time fraud detection, circuit-breaking, outage simulation, and LLM-powered payment failure explanations with robust logging and API-first design.

---

## Table of Contents

* [Features](#features)
* [Architecture Overview](#architecture-overview)
* [API Endpoints](#api-endpoints)
* [Machine Learning Integration](#machine-learning-integration)
* [Resilience & Reliability](#resilience--reliability)
* [Getting Started](#getting-started)
* [Environment Variables & Configuration](#environment-variables--configuration)
* [Development & Local Setup](#development--local-setup)
* [Contributing](#contributing)
* [License](#license)

---

## Features

* 📈 **Real-Time Fraud Detection:** AI/ML models (custom or stub) score transactions for fraud risk.
* 🤖 **Intelligent Routing:** Selects optimal payment gateways via learned routing models.
* 🔄 **Resilient Architecture:** Uses circuit breakers around gateways, async Redis cache, and idempotent POST handling.
* 💥 **Outage Simulation:** Administrators can simulate gateway degradations and observe routing adaptation.
* 🧠 **Failure Explanation:** RAG/LLM-driven merchant explanations for failed transactions using OpenAI/LangChain integration.
* 🏥 **Comprehensive Health Checks:** API endpoints for gateway, model, and service health.
* 📑 **Structured Logging:** Logs are formatted as JSON for DevOps observability.
* 🧪 **Fully API-First:** Clean OpenAPI documentation, consistent versioned routes, and Python type annotations.

---

## Architecture Overview

Simplified flow:

1. **Client** submits a transaction to `/v1/transaction/process` through FastAPI.
2. **Fraud Detection (ML):** Features are extracted and the ML model scores the transaction risk.
3. **Intelligent Routing:** The system evaluates available gateways such as Stripe, PayPal, and Razorpay based on health and routing logic.
4. **Circuit Breakers:** Payments to unstable gateways are blocked.
5. **Payment Execution:** Transaction success or failure is recorded.
6. **Failure Diagnosis:** Root cause information and ML SHAP values are recorded.
7. **LLM/RAG Explanation:** Merchants receive a natural-language explanation for failed transactions.
8. **Idempotency:** Repeated POST requests with the same idempotency key return the cached response.

![ATLAS-OPS Architecture](docs/atlas-ops-architecture.png)

---

## API Endpoints

All endpoints are versioned under `/v1`.

| Method   | Endpoint                           | Description                                                  |
| -------- | ---------------------------------- | ------------------------------------------------------------ |
| `POST`   | `/v1/transaction/process`          | Process payment with fraud detection, routing, and execution |
| `GET`    | `/v1/transaction/{txn_id}`         | Fetch transaction status                                     |
| `POST`   | `/v1/simulate/outage`              | Simulate a gateway outage or failure rate                    |
| `DELETE` | `/v1/simulate/outage/{gateway}`    | Clear a simulated gateway outage                             |
| `GET`    | `/v1/gateways/health`              | View detailed gateway health metrics                         |
| `GET`    | `/v1/transaction/{txn_id}/explain` | Generate an LLM-based explanation for a failed transaction   |
| `GET`    | `/v1/ml/status`                    | Check ML model and fallback status                           |
| `GET`    | `/health`                          | Check service health                                         |

### Interactive API Documentation

When running locally:

* **Swagger UI:** `http://localhost:8000/docs`
* **ReDoc:** `http://localhost:8000/redoc`

---

## Machine Learning Integration

* **Fraud/Failure/Routing Models:** Place trained models as `fraud_model.pkl`, `failure_model.pkl`, and `routing_model.pkl` in `app/ml_models/`.
* **Fallback:** If trained models are unavailable, dummy classifiers are automatically used so the API can continue operating.
* **Model Features:** Feature schemas are defined for fraud, failure, and routing models.
* **Explainability:** SHAP explainers are used to provide model explanations where supported.

---

## Resilience & Reliability

* **Circuit Breakers:** Powered by PyBreaker with Redis-backed storage to isolate unhealthy gateways.
* **Idempotency:** POST operations support idempotency using asynchronous Redis storage.
* **Gateway Outage Simulation:** Simulate gateway failures and circuit state changes for development and testing.
* **Async/Non-blocking:** Major subsystems use asynchronous processing for improved performance.

---

## Getting Started

### Prerequisites

* Python 3.10+
* PostgreSQL running locally at `localhost:5432`
* Redis running locally at `localhost:6379`

### Local Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/kaleprabhat24/Atlas_OPS_.git
   cd Atlas_OPS_
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL and Redis:**

   * Ensure PostgreSQL is running.
   * Create the `atlas_ops` database.
   * Ensure the Redis server is running.

4. **Create the environment file:**

   ```bash
   cp .env.local.example .env
   ```

   Then edit `.env` and configure your database, Redis, OpenAI API key, and other required values.

5. **Check the local setup:**

   ```bash
   python check_setup.py
   ```

   This validates database/Redis connectivity and model availability.

6. **Run locally:**

   ```bash
   python run_local.py
   ```

   Or run FastAPI directly:

   ```bash
   uvicorn app.main:app --reload
   ```

The application will be available at:

`http://127.0.0.1:8000`

---

## Environment Variables & Configuration

Configuration is loaded from `.env`.

Main settings include:

* `DATABASE_URL` — PostgreSQL connection string
* `REDIS_URL` — Redis connection string
* `FRAUD_MODEL_PATH` — Fraud model location
* `FAILURE_MODEL_PATH` — Failure model location
* `ROUTING_MODEL_PATH` — Routing model location
* `OPENAI_API_KEY` — Optional API key for LLM-powered explanations
* `SECRET_KEY` — Secret used for admin/API protection

See `.env.local.example` for the complete list of supported environment variables.

> **Security:** Never commit your actual `.env` file, API keys, passwords, or other secrets to GitHub.

---

## Contributing

1. Fork and clone the repository.
2. Create a new branch for your feature or bug fix.
3. Follow PEP8 guidelines and maintain proper type annotations.
4. Add or update documentation and docstrings for API and logic changes.
5. Submit a pull request describing the changes and their purpose.

---

## License

This project is open-source and available under the MIT License.

---

## Acknowledgements

* [FastAPI](https://fastapi.tiangolo.com/)
* [PostgreSQL](https://www.postgresql.org/)
* [Redis](https://redis.io/)
* [PyBreaker](https://pybreaker.readthedocs.io/)
* [scikit-learn](https://scikit-learn.org/)
* [SHAP](https://shap.readthedocs.io/)
* [LangChain](https://langchain.com/)
* [structlog](https://www.structlog.org/)

LLM-powered explanations are optionally provided through OpenAI integrations.

---

## Support

For questions, bug reports, or feature requests, open an issue in [GitHub Issues](https://github.com/kaleprabhat24/Atlas_OPS_/issues).
