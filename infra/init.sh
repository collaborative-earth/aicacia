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