output "public_ip" {
  value = aws_eip.app_eip.public_ip
}