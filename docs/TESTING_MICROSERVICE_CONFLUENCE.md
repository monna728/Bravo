# Testing microservice — Confluence summary

## Strategy overview

The **testing microservice** (`services/testing/`) complements unit tests under `tests/`. It runs **higher-level** checks against the Prophet analytical model: walk-forward backtest accuracy on merged S3 data, regressor uplift, HTTP/API behaviour, and response **contract** validation. Results are written to **`s3://<bucket>/test-reports/report_<timestamp>.json`** via `shared.s3_uploader`.

**Ground truth for backtests:** `demand_proxy` is **min–max of `trip_count` on the training window only**, scaled to 0–100. Predictions use the same normalisation basis as production (`normalise_to_index` against training `y`).

---

## Test types (5 areas)

| # | Name | What it does |
|---|------|----------------|
| 1 | **Backtesting accuracy** | 80% / 20% date split per borough; Prophet with regressors; ±15 point accuracy vs `demand_proxy`; MAE/RMSE; borough pass ≥80%; **overall** = mean borough accuracy ≥80%. |
| 2 | **Metrics** | `metrics.py`: accuracy, MAE, RMSE, MAPE, directional accuracy (≥70% flag), `score_summary`. |
| 3 | **Regressor impact** | Baseline Prophet (no regressors) vs full model on the same hold-out; **pass** if mean improvement across boroughs with data is **≥ 3** percentage points. |
| 4 | **Edge cases** | Insufficient history (&lt; `MIN_DATAPOINTS`), invalid borough → 400, 50× scores in [0,100], interval order, weather multiplier (clear vs thunderstorm history), `compare_all_boroughs` → 5 boroughs. |
| 5 | **API contract** | Top-level `status`, `borough`, `predictions`; each prediction has `crowd_demand_index`, `lower_bound`, `upper_bound`, `confidence`, `contributing_factors`, etc. |

---

## Level of abstraction

| Suite | Level | Typical dependencies |
|-------|--------|----------------------|
| Metrics | **Unit** | Pure Python lists |
| Backtest / regressor | **Integration** | Prophet + merged data shape (S3 or mocks) |
| Edge + contract | **Integration / system** | `prophet_model.predict`, Lambda handler, mocks for S3/Prophet where needed |

---

## Components under test

- **`prophet_model.predict`**, **`fit_and_forecast`**, **`load_historical_data`**, **`normalise_to_index`**, weather/time multipliers.
- **`handler.lambda_handler`** (analytical model) for HTTP validation and `compare_all_boroughs`.
- **Merged ADAGE** under `processed/merged/` (via `data_sampler` + `s3_uploader`).

---

## Pass/fail thresholds

| Check | Threshold | Rationale |
|-------|-----------|-----------|
| Backtest accuracy | **≥ 80%** of days within **±15** of `demand_proxy` | Course / product bar for usable forecasts |
| Directional accuracy (in `score_summary`) | **≥ 70%** | Demand “direction” should be right often even when levels differ |
| Regressor uplift | **≥ +3 pp** mean accuracy vs baseline | Ticketmaster + weather regressors should help vs trips-only Prophet |
| `MIN_DATAPOINTS` | **14** days | ~2 weeks minimum for meaningful seasonality |

---

## How to run

**Lambda / API:** `POST /test/predict` with body:

```json
{ "borough": "Manhattan", "test_suite": "all", "bucket": "your-bucket" }
```

`suite`: `all` | `accuracy` | `edge_cases` | `contract`.

**CLI** (from repo root, with `PYTHONPATH` including `services` if needed):

```bash
python -m pip install prophet
python services/testing/handler.py --suite all --bucket your-bucket
python services/testing/handler.py --borough Manhattan --suite contract
```

Install **Prophet** in the same Python environment you use to run the script (`ModuleNotFoundError: prophet` means it is missing). Full pins are in `services/testing/requirements.txt`; on Windows, if `pip install -r` tries to compile pandas from source, install **Prophet** alone after you already have pandas/numpy wheels.

If you see **`AttributeError: ... stan_backend`**, CmdStan did not load: run `python -m pip install -U cmdstanpy` then `python -c "import cmdstanpy; cmdstanpy.install_cmdstan()"`, or use **Python 3.11–3.12** (Prophet 1.1.x is unreliable on **Python 3.14+**).

**Windows:** if `install_cmdstan` fails with **`mingw32-make` / `WinError 2`**, the C++ toolchain is missing. Install **Rtools** from CRAN and add `...\Rtools*\usr\bin` to **PATH** (new terminal), or install **MSYS2** + `mingw-w64-x86_64-toolchain` and add `C:\msys64\mingw64\bin` to PATH, then run `install_cmdstan()` again. Easiest alternative: **WSL2** Ubuntu + `sudo apt install build-essential` and run Python/tests inside WSL.

**Pytest:** `pytest` (includes `services/testing/tests` via `pytest.ini`).

---

## Reading the report

Open the JSON at `report_s3_key`. Fields include:

- `timestamp_utc`, `boroughs_tested`, `overall_pass`, `overall_accuracy`, `threshold_percent`
- `ground_truth_note` (demand_proxy definition)
- `data_points` (train/test sizes where available)
- `warnings` (e.g. borderline accuracy)
- `test_results` — nested objects per suite (`backtest`, `regressor_impact`, `api_contract`, …) with `pass` flags and diagnostics

Use **`overall_pass`** for CI gates; inspect **`borough_results`** for weak boroughs.
