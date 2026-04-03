output "cloudwatch_dashboard_name" {
  description = "Name of the CloudWatch dashboard (empty if no widgets were configured)."
  value       = try(aws_cloudwatch_dashboard.bravo[0].dashboard_name, null)
}

output "cloudwatch_dashboard_url_hint" {
  description = "Console URL pattern; replace REGION and encode dashboard name if needed."
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${var.dashboard_name}"
}
