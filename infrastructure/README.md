# Observability (CloudWatch dashboard)

Terraform in this folder provisions a **CloudWatch dashboard** with:

- **Lambda:** invocations, errors, throttles, duration (p99) per function
- **Logs Insights:** error-oriented queries per function log group
- **API Gateway (optional):** count, 4XX, 5XX, latency (p99) for `ApiName` + `Stage`
- **EMF sample (optional):** recent lines containing `"_aws"` from the first listed Lambda’s log group (Embedded Metric Format / custom `Bravo` metrics)

## Usage

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your Lambda names, API name, stage, and region.

terraform init
terraform plan
terraform apply
```

After apply, open the dashboard in the CloudWatch console (see `terraform output cloudwatch_dashboard_url_hint`).

If you have **no Lambdas deployed yet**, set `lambda_function_names = []` and only fill `api_gateway_api_name` if the API exists; otherwise Terraform will create nothing (`count = 0`).

## X-Ray

To attach active tracing in Terraform when you manage Lambdas and API Gateway in code, see `xray_snippet.tf.example` (copy the blocks into your Lambda/API modules). You still need the execution role policy **`AWSXRayDaemonWriteAccess`** (or equivalent). For console steps, see [docs/DELIVERY_AND_OBSERVABILITY.md](../docs/DELIVERY_AND_OBSERVABILITY.md).

## Verification

X-Ray traces appear only after traffic hits a traced API stage and Lambda. Capture a **screenshot** of the X-Ray trace list or service map for coursework; the repo cannot automate console verification.
