variable "aws_region" {
  default = "us-east-2"
}

variable "postgres_password" {
  description = "Postgres password"
  sensitive   = true
}

variable "openai_api_key" {
  description = "API key for OpenAI"
  sensitive   = true
}