# Bravo
Predicative demand intelligence for ride-sharing operators: Ride-sharing supply-demand imbalance is a continuous, pervasive phenomenon. We would like to make it B2B and sell to ride-sharing service operators (Uber, Bolt, DiDi, Ola), corporate fleet management companies, and public transport authorities.

## API documentation (Swagger UI)

Hosted on **GitHub Pages** when [Deploy API docs](.github/workflows/deploy-docs.yml) has run successfully.

- **One-time setup:** Repository **Settings → Pages → Build and deployment → Source:** choose **GitHub Actions** (not “Deploy from a branch”).
- **Public URL:** `https://<github-username>.github.io/<repository>/` — for this repo, open **`https://monna728.github.io/Bravo/`** (or `/index.html`). The spec is `docs/openapi.yaml` beside the bundled Swagger UI assets.

Push changes under `docs/` to `main` or `develop` to redeploy, or run the workflow manually from the **Actions** tab (**Run workflow**).
