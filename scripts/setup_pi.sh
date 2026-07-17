#!/bin/bash

echo "Updating package lists..."
sudo apt update

echo "Upgrading installed packages..."
sudo apt full-upgrade -y

echo "Installing development tools..."
sudo apt install -y \
git \
vim \
htop \
curl \
wget \
tree \
build-essential \
python3-pip

echo "Setup complete!"
