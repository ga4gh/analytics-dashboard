output "db_endpoint" {
  description = "JDBC‑style hostname:port of the RDS instance"
  value       = aws_db_instance.postgres.endpoint
}

output "db_username" {
  description = "Master username"
  value       = var.master_username
}

output "db_password" {
  description = "Master password"
  value       = random_password.master.result
  sensitive   = true
}

output "database_url" {
  description = "Database connection URL"
  value       = "postgresql://${var.master_username}:${urlencode(random_password.master.result)}@${aws_db_instance.postgres.endpoint}/analytics?sslmode=require"
  sensitive   = true
}
