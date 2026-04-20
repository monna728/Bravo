# Bravo — resume section (CV-ready)

Paste under **PROJECTS** on your CV. Adjust the date range if your team’s timeline differs.

---

**Bravo — Predictive Demand Intelligence (B2B) (UNSW SENG3011)** · Python, AWS Lambda, S3, Prophet, React, pytest, GitHub Actions · T2 2025 – T1 2026

- Positioned the product for **B2B sale to mobility operators** (ride-hail platforms such as Uber and DiDi, fleet managers, transit authorities) rather than end riders, by framing outputs as **operator-grade supply–demand intelligence**—multi-source historical signals fused into a single analytical pipeline consumable via documented APIs.

- Built an **event-driven microservices architecture** spanning **data collection** (e.g. NYC taxi trips, Ticketmaster events, weather), **S3-backed storage and retrieval**, **schema validation (ADAGE-style contracts)**, and a **Prophet-based forecasting service** with external regressors and normalised **demand indices**, enabling repeatable ingestion-to-prediction workflows suitable for integration into partner ops stacks.

- Raised engineering quality through **automated testing and CI**: **pytest** suites across collectors, preprocessing, retrieval, and the analytical model; a dedicated **testing microservice** for walk-forward **backtests**, regressor uplift checks, edge cases, and **OpenAPI-documented** HTTP contracts; **GitHub Actions** for build/test gates and **coverage** policy—aligning delivery with team **Agile/Confluence** documentation norms.

**Optional fourth bullet**

- Defined **quantitative acceptance criteria** for model quality (e.g. hold-out accuracy bands, regressor uplift vs baseline, minimum history thresholds) and **JSON reporting to S3**, so forecasts are **evaluable before** operator-facing rollout.

---

**Cover letter one-liner (optional)**  
*Enterprise go-to-market targets ride-hail and mobility operators (e.g. Uber, DiDi) with API-driven demand intelligence—not a consumer rider app.*
