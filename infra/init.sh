#!/bin/bash

# Log everything to the log file
mkdir -p /var/log
exec > /var/log/user-data.log 2>&1
set -x

# Install and enable docker
dnf update -y
dnf install -y docker
systemctl enable --now docker

# Add ec2-user to docker group
usermod -aG docker ec2-user

echo "Docker setup completed successfully!"

# Install docker compose (v2.x via plugin system)
DOCKER_CONFIG=/usr/libexec/docker/cli-plugins

mkdir -p $DOCKER_CONFIG
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o $DOCKER_CONFIG/docker-compose

chmod +x $DOCKER_CONFIG/docker-compose

echo "Docker compose setup completed successfully!"

# Init postgresql volume
while [ ! -b /dev/xvdf ]; do
  echo "Waiting for /dev/xvdf to be attached..."
  sleep 1
done

mkdir -p /mnt/data/postgresql

if ! blkid /dev/xvdf; then
  mkfs -t xfs /dev/xvdf
fi

if ! grep -q "/dev/xvdf" /etc/fstab; then
  echo "/dev/xvdf /mnt/data/postgresql xfs defaults,nofail 0 2" >> /etc/fstab
fi

mount -a

echo "Postgresql volume setup completed successfully!"

# Set up github auth
dnf install -y awscli
dnf install -y git

GITHUB_KEY=$(aws ssm get-parameter --name "/aicacia-app/gh-key" --with-decryption --query "Parameter.Value" --output text)

echo "$GITHUB_KEY" > /home/ec2-user/.ssh/id_github
chmod 600 /home/ec2-user/.ssh/id_github
chown ec2-user:ec2-user /home/ec2-user/.ssh/id_github

cat <<EOF >> /home/ec2-user/.ssh/config
Host github.com
  HostName github.com
  User git
  IdentityFile /home/ec2-user/.ssh/id_github
  StrictHostKeyChecking no
EOF

chmod 600 /home/ec2-user/.ssh/config
chown ec2-user:ec2-user /home/ec2-user/.ssh/config

echo "Github setup completed successfully!"

# Fetch repo for the first time and make deploy.sh executable
runuser -l ec2-user -c "git clone git@github.com:collaborative-earth/aicacia.git"
chmod +x /home/ec2-user/aicacia/infra/deploy.sh

echo "Init completed successfully!"