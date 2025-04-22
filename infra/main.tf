resource "aws_key_pair" "deployer" {
  key_name = "deployer-key"
  public_key = file("~/.ssh/id_rsa.pub")
}

resource "aws_security_group" "app_sg" {
  name        = "app_sg"
  description = "Allow SSH, HTTP(S) access"
}

resource "aws_vpc_security_group_ingress_rule" "allow_tls_ipv4" {
  security_group_id = aws_security_group.app_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "allow_http_ipv4" {
  security_group_id = aws_security_group.app_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 8000
  to_port           = 8000
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "allow_pg_ipv4" {
  security_group_id = aws_security_group.app_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 5432
  to_port           = 5432
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "allow_ssh_ipv4" {
  security_group_id = aws_security_group.app_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "allow_app_ipv4" {
  security_group_id = aws_security_group.app_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 3000
  to_port           = 3000
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "allow_all_traffic_ipv4" {
  security_group_id = aws_security_group.app_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_instance" "app_server" {
  ami                         = "ami-088b41ffb0933423f"
  instance_type               = "t2.micro"
  key_name                    = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [aws_security_group.app_sg.id]
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.app_server_profile.name

  root_block_device {
    volume_type = "gp3"
    volume_size = 30
  }

  user_data = file("./init.sh")

  tags = {
    Name = "Aicacia App Server"
  }
}

resource "aws_ebs_volume" "db_data" {
  type              = "gp3"
  availability_zone = aws_instance.app_server.availability_zone
  size              = 20
}

resource "aws_volume_attachment" "db_attach" {
  device_name = "/dev/sdf"
  volume_id   = aws_ebs_volume.db_data.id
  instance_id = aws_instance.app_server.id
}

resource "aws_eip" "app_eip" {
  domain = "vpc"
}

resource "aws_eip_association" "eip_assoc" {
  instance_id   = aws_instance.app_server.id
  allocation_id = aws_eip.app_eip.id
}

resource "aws_iam_role" "app_server_role" {
  name = "aicacia-app-server-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "app_server_policy" {
  name = "aicacia-app-server-policy"
  role = aws_iam_role.app_server_role.id
  policy = file("policy.json")
}

resource "aws_iam_instance_profile" "app_server_profile" {
  name = "aicacia-app-server-profile"
  role = aws_iam_role.app_server_role.name
}

resource "aws_ssm_parameter" "postgres_password" {
  name  = "/aicacia-app/postgres-password"
  type  = "SecureString"
  value = var.postgres_password
}

resource "aws_ssm_parameter" "openai_api_key" {
  name  = "/aicacia-app/openai-api-key"
  type  = "SecureString"
  value = var.openai_api_key
}

resource "aws_ecr_repository" "aicacia_api" {
  name                 = "aicacia-api"
  image_tag_mutability = "MUTABLE"
  tags = {
    Project = "aicacia"
  }
}

resource "aws_ecr_repository" "aicacia_webapp" {
  name                 = "aicacia-webapp"
  image_tag_mutability = "MUTABLE"
  tags = {
    Project = "aicacia"
  }
}

resource "aws_s3_bucket" "aicacia_extracted_data" {
  bucket = "aicacia-extracted-data"
  tags = {
    Name = "Aicacia Extracted Data"
  }
}
