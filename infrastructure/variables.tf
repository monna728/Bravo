variable "aws_region" {
  type        = string
  description = "AWS region where Lambdas and API Gateway are deployed."
  default     = "us-east-1"
}

variable "dashboard_name" {
  type        = string
  description = "CloudWatch dashboard name (e.g. Bravo-Staging or Bravo-Prod)."
  default     = "Bravo-Observability"
}

variable "lambda_function_names" {
  type        = list(string)
  description = "Deployed Lambda names; log groups must be /aws/lambda/<name>."
  default     = []
}

variable "api_gateway_api_name" {
  type        = string
  description = "REST API name as shown in API Gateway (AWS/ApiGateway dimension ApiName). Leave empty to skip API widgets."
  default     = ""
}

variable "api_gateway_stage_name" {
  type        = string
  description = "API Gateway stage name (e.g. staging, prod)."
  default     = "prod"
}

variable "bravo_custom_metric_queries" {
  type        = bool
  description = "Add a Logs Insights widget that surfaces recent EMF/custom metric JSON lines (namespace Bravo)."
  default     = true
}
