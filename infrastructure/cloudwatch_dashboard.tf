locals {
  lambda_widgets = flatten([
    for idx, fn in var.lambda_function_names : [
      {
        type   = "metric"
        x      = 0
        y      = idx * 12
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", fn],
            [".", "Errors", ".", "."],
            [".", "Throttles", ".", "."],
            [".", "Duration", ".", ".", { stat = "p99" }],
          ]
          period  = 300
          stat    = "Sum"
          region  = data.aws_region.current.name
          title   = "${fn} — Lambda"
          view    = "timeSeries"
          stacked = false
        }
      },
      {
        type   = "log"
        x      = 0
        y      = idx * 12 + 6
        width  = 12
        height = 6
        properties = {
          query = <<-EOT
            SOURCE '/aws/lambda/${fn}'
            | fields @timestamp, @message
            | filter @message like /ERROR/ or @message like /"level": "ERROR"/
            | sort @timestamp desc
            | limit 50
          EOT
          region    = data.aws_region.current.name
          title     = "${fn} — error logs"
          logGroups = ["/aws/lambda/${fn}"]
        }
      },
    ]
  ])

  api_widgets = var.api_gateway_api_name == "" ? [] : [
    {
      type   = "metric"
      x      = 0
      y      = length(var.lambda_function_names) * 12
      width  = 12
      height = 6
      properties = {
        metrics = [
          ["AWS/ApiGateway", "Count", "ApiName", var.api_gateway_api_name, "Stage", var.api_gateway_stage_name],
          [".", "5XXError", ".", ".", ".", "."],
          [".", "4XXError", ".", ".", ".", "."],
          [".", "Latency", ".", ".", ".", ".", { stat = "p99" }],
        ]
        period  = 300
        stat    = "Sum"
        region  = data.aws_region.current.name
        title   = "API ${var.api_gateway_api_name} (${var.api_gateway_stage_name})"
        view    = "timeSeries"
        stacked = false
      }
    },
  ]

  bravo_emf_y = length(var.lambda_function_names) * 12 + (var.api_gateway_api_name == "" ? 0 : 6)

  bravo_emf_widgets = !var.bravo_custom_metric_queries || length(var.lambda_function_names) == 0 ? [] : [
    {
      type   = "log"
      x      = 0
      y      = local.bravo_emf_y
      width  = 12
      height = 6
      properties = {
        query = <<-EOT
            SOURCE '/aws/lambda/${var.lambda_function_names[0]}'
            | fields @timestamp, @message
            | filter @message like /"_aws"/
            | sort @timestamp desc
            | limit 30
          EOT
        region    = data.aws_region.current.name
        title     = "Sample — EMF / custom metrics (first Lambda log group)"
        logGroups = ["/aws/lambda/${var.lambda_function_names[0]}"]
      }
    },
  ]

  dashboard_widgets = concat(local.lambda_widgets, local.api_widgets, local.bravo_emf_widgets)
}

resource "aws_cloudwatch_dashboard" "bravo" {
  count = (
    length(var.lambda_function_names) > 0 || var.api_gateway_api_name != ""
  ) ? 1 : 0

  dashboard_name = var.dashboard_name
  dashboard_body = jsonencode({ widgets = local.dashboard_widgets })
}
