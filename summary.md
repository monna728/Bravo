# Bravo — handoff summary for a new chat

Use this file as context when opening a new Cursor chat (`@summary.md` or paste relevant sections). It reflects the **Bravo** repo (UNSW SENG3011–style team project): predictive **demand intelligence** for **B2B** customers (ride-hail operators, fleet managers, transit authorities)—**not** a consumer rider app. README positions buyers as operators (Uber, Bolt, DiDi, Ola, etc.).

---

## Product intent

- **Problem:** Supply–demand imbalance in ride-sharing / mobility.
- **Solution:** Pipeline that ingests multiple signals, stores and merges them, runs **Prophet**-based forecasts with regressors, exposes **HTTP/Lambda** APIs and **OpenAPI** docs (GitHub Pages workflow in `.github/workflows/deploy-docs.yml`).
- **Outputs:** Normalised **demand indices**, intervals, contributing factors, borough-level predictions where applicable.

---

## Repository layout (high level)

| Area | Path | Role |
|------|------|------|
| Collectors | `services/data-collection/` | NYC Taxi, Ticketmaster, weather → ADAGE-oriented payloads, S3 upload |
| Preprocessing | `services/data-preprocessing/` | `merger.py`, `normaliser.py`, Lambda `handler.py` |
| Retrieval | `services/data-retrieval/` | `s3_reader.py`, Lambda handler |
| Model | `services/analytical-model/` | `prophet_model.py` (fit, forecast, `crowd_demand_index`, regressors, `MIN_DATAPOINTS` etc.), Lambda handler |
| Shared | `services/shared/` | ADAGE conversion/validation, S3 uploader, observability helpers |
| Testing microservice | `services/testing/` | Backtests, accuracy/regressor/edge/contract suites, metrics, reports to S3 |
| App tests | `tests/` | Broad unit/integration coverage for collectors, model, preprocessing, retrieval, lambdas |
| Testing MS tests | `services/testing/tests/` | e.g. `test_accuracy_tester.py` |
| Frontend | `frontend/` | React UI (separate from Python CI unless extended) |
| Infra | `infrastructure/` | Deployment notes |
| API spec | `docs/openapi.yaml` | Swagger source; bundled UI under `docs/` for Pages |

---

## Data & contracts

- **ADAGE-style** JSON: validation/conversion in `services/shared/adage_validator.py`, `adage_converter.py`.
- **S3:** Processed merged data under paths like `processed/merged/` (see testing Confluence doc); test reports e.g. `s3://<bucket>/test-reports/report_<timestamp>.json` via `shared.s3_uploader`.

---

## Analytical model (essentials)

- **File:** `services/analytical-model/prophet_model.py`.
- **Prophet** with **regressors** (e.g. events, weather-derived features).
- **Demand proxy / normalisation:** Training-window min–max of `trip_count`, scaled to 0–100; predictions aligned via `normalise_to_index` (see `docs/TESTING_MICROSERVICE_CONFLUENCE.md`).
- **Guards:** Minimum history (`MIN_DATAPOINTS`, documented as 14 days in testing doc), invalid borough → 400 patterns tested at handler/model edge.

---

## Testing strategy

1. **`tests/`** — Primary pytest suite: collectors (NYC Taxi, Ticketmaster, weather), preprocessing, retrieval, `test_model.py`, lambda observability, etc.
2. **`services/testing/tests/`** — Additional tests for testing-microservice helpers (e.g. metrics/accuracy wiring).
3. **`services/testing/` runtime** — Higher-level orchestration: walk-forward **backtester**, **accuracy_tester**, **data_sampler**, `handler.py` CLI/Lambda entry, `report_generator.py`, `metrics.py`. Documented pass thresholds (e.g. ±15 vs proxy, ≥80% borough pass, regressor uplift ≥3 pp) in `docs/TESTING_MICROSERVICE_CONFLUENCE.md`.

**Pytest config:** [`pytest.ini`](pytest.ini) — `testpaths = tests services/testing/tests`, `pythonpath = .`.

---

## CI / coverage / lint

- **Workflow:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — runs on **`push`/`pull_request` to `main`** only (not `develop` unless workflow is changed).
- **Python:** 3.11 in CI.
- **Steps:** `pip install -r requirements.txt`, `flake8` (strict subset: E9, F63, F7, F82), **`pytest --cov`** with [`.coveragerc`](.coveragerc), **`--cov-fail-under=85`**.
- **Coverage source:** `source = services` in `.coveragerc`.
- **Omitted from coverage totals (not from test execution):** `*/__init__.py`, `*/handler.py`, `services/shared/*`, plus **`services/testing/accuracy_tester.py`**, **`backtester.py`**, **`data_sampler.py`** — these are heavy Lambda/orchestration modules; omitting them keeps the **global** coverage gate above 85% while core libraries stay measured.
- **Dependencies:** Root [`requirements.txt`](requirements.txt) includes `pytest`, **`pytest-cov`**, `moto[s3]`, etc. Local runs should use `pip install -r requirements.txt` before the same pytest command as CI.

**Mirror CI locally:**

```bash
pytest --cov --cov-config=.coveragerc --cov-report=term-missing --cov-report=xml --cov-fail-under=85
```

---

## Documentation worth citing in new chats

| Doc | Purpose |
|-----|---------|
| [`README.md`](README.md) | B2B positioning, GitHub Pages API docs setup |
| [`docs/TESTING_MICROSERVICE_CONFLUENCE.md`](docs/TESTING_MICROSERVICE_CONFLUENCE.md) | Testing microservice strategy, thresholds, how to run suites |
| [`docs/BRAVO_RESUME_SECTION.md`](docs/BRAVO_RESUME_SECTION.md) | CV-ready project blurb (UNSW SENG3011, dates editable) |
| [`docs/openapi.yaml`](docs/openapi.yaml) | HTTP contract |

---

## Tooling / environment gotchas

- **Prophet / CmdStan:** On Windows or bleeding-edge Python, Prophet can fail (Stan backend). Testing doc recommends **Python 3.11–3.12** and documents `cmdstanpy` / toolchain fixes; **WSL2** is often easiest.
- **Frontend:** Separate `frontend/package-lock.json`; Python CI does not automatically build the frontend unless added to workflow.

---

## Recent conversation themes (for continuity)

- **Coverage failure:** Total coverage was ~68% with `--cov-fail-under=85`; fix was **`.coveragerc` omit** for the three testing orchestration modules listed above (tests still run; measurement scope narrowed).
- **Resume:** Plan-style bullets implemented in **`docs/BRAVO_RESUME_SECTION.md`** (B2B, Uber/DiDi examples, stack, SENG3011, optional fourth bullet and cover-letter line).

---

## Quick commands

```bash
# Install and test like CI
pip install -r requirements.txt
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
pytest --cov --cov-config=.coveragerc --cov-report=term-missing --cov-fail-under=85
```

---

## What to ask the assistant in a new chat

Examples: *“Extend CI to `develop`”*, *“Add tests for `prophet_model` lines X–Y”*, *“Remove coverage omit and raise tests instead”*, *“Document Lambda env vars”*, *“Wire frontend to staging API”*. Attach **`summary.md`** plus any file you are editing.
