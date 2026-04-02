# Delivery strategy and observability (AWS serverless)

This document describes how Bravo releases to **staging** vs **production** and how **logging, metrics, and tracing** are implemented on AWS.

## 1. Staging vs production

| Concern | Staging | Production |
|--------|---------|------------|
| **API Gateway** | Stage name `staging` (or dedicated API) | Stage name `prod` |
| **Lambda** | Alias `staging` → tested version or `$LATEST` | Alias `prod` → **pinned version** after sign-off |
| **S3** | Prefix `staging/` on shared bucket, or separate bucket if allowed | Prefix `prod/` or production bucket |
| **Configuration** | Environment variables via Lambda config (`ENV=staging`, `S3_BUCKET_NAME`, keys) | Same keys, production values |
| **IaC** | `terraform.tfvars` or workspace `staging` | `prod.tfvars` or workspace `prod` |

### Promotion flow

1. Merge feature branches into **`develop`** → CI runs tests → deploy artifact to **staging**.
2. Run smoke tests and demos against the **staging** invoke URL.
3. After approval, merge **`develop`** → **`main`** (or tag `v1.x.x`) → deploy **same build** to **production** with production variables.
4. **Rollback:** Point the production Lambda **alias** at the previous **version** (no code change).

Document each production deploy in your team’s changelog or Confluence with version, date, and approver.

## 2. Observability platform

**Amazon CloudWatch** is the primary platform:

| Pillar | Mechanism |
|--------|-----------|
| **Logs** | Lambda → CloudWatch Logs (`/aws/lambda/<function-name>`). Handlers emit **JSON** lines via `shared.lambda_observability.log_event`. |
| **Metrics** | Built-in **AWS/Lambda** and **AWS/API Gateway** metrics in dashboards. **Custom metrics** via **Embedded Metric Format (EMF)** in logs (`emit_embedded_metric`). |
| **Tracing (optional)** | **AWS X-Ray** — enable **active tracing** on each Lambda and on the API Gateway stage. Attach **`AWSXRayDaemonWriteAccess`** (or equivalent) to the Lambda execution role. View traces in **X-Ray** or **CloudWatch ServiceLens**. |

### Structured log fields

Each log line is a JSON object including:

- `service` — e.g. `data-retrieval`, `data-preprocessing`, `analytical-model`, `collect-ticketmaster`
- `level` — `INFO`, `ERROR`, …
- `message` — human-readable summary
- `correlation_id` — API Gateway `requestContext.requestId` or Lambda `aws_request_id`
- `env` — from `ENV` or `ENVIRONMENT` (default `dev`)
- Domain fields (e.g. `source`, `borough`, `record_count`) — no secrets or full request bodies

### Custom metrics (namespace `Bravo`)

| Metric | Service | Dimensions |
|--------|---------|------------|
| `MergedRecordCount` | Preprocessing | `Environment` |
| `PredictionsGenerated` | Analytical | `Environment`, `Borough` |
| `RecordsCollected` | Collection (Ticketmaster, TLC, weather) | `Service`, `Environment` |
| `RecordsRetrieved` | Data retrieval | `Service`, `Environment` |

EMF lines are picked up by CloudWatch when Lambda has the default log group configuration.

## 3. CloudWatch dashboard (Terraform)

See [infrastructure/README.md](../infrastructure/README.md). Apply `infrastructure/` with your **Lambda function names** and **Region** so the dashboard shows invocations, errors, and duration per function.

Create **Logs Insights** saved queries** in the console for error text search, or add **log widgets** to the dashboard using the same log groups.

## 4. Enabling X-Ray (console or Terraform)

1. **Lambda** → each function → **Configuration** → **Monitoring and operations tools** → enable **Active tracing**.
2. **API Gateway** → stage → **Logs/tracing** → enable **X-Ray tracing**.
3. **IAM** → Lambda execution role → add managed policy **`AWSXRayDaemonWriteAccess`** (or inline `xray:PutTraceSegments`, `PutTelemetryRecords`).

No application code change is strictly required for basic traces; the X-Ray daemon captures segment data for the invocation. For subsegments inside Python, add `aws-xray-sdk` later.

## 5. Course submission checklist

- [ ] Written **delivery strategy** (this doc + any Confluence page).
- [ ] **Screenshot or link** to CloudWatch **dashboard** after deploy.
- [ ] List of **log** event types and **metrics** (built-in + `Bravo/*` custom).
- [ ] **Tracing:** X-Ray screenshot or short note if not enabled (e.g. teaching bucket only).
