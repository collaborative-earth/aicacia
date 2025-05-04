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

variable "qdrant_url" {
  description = "URL of qdrant endpoint"
  sensitive   = true
}

variable "qdrant_api_key" {
  description = "API key for qdrant endpoint"
  sensitive   = true
}

variable "secret_key" {
  description = "Aicacia secret key"
  sensitive   = true
}