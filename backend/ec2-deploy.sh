#!/bin/bash

# EC2 Deployment Script for DotStarkRag365
# Run this script on your EC2 instance

set -e

echo "=========================================="
echo "DotStarkRag365 EC2 Deployment Script"
echo "=========================================="

# Update system packages
echo "Updating system packages..."
sudo apt update

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker ${USER}
    echo "Docker installed successfully!"
else
    echo "Docker is already installed."
fi

# Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed successfully!"
else
    echo "Docker Compose is already installed."
fi

# Install Git if not already installed
if ! command -v git &> /dev/null; then
    echo "Installing Git..."
    sudo apt install -y git
else
    echo "Git is already installed."
fi

# Clone the repository
REPO_URL="https://github.com/Niteshdotstark/DotStarkRag365.git"
APP_DIR="$HOME/DotStarkRag365"

if [ -d "$APP_DIR" ]; then
    echo "Repository already exists. Pulling latest changes..."
    cd "$APP_DIR/backend"
    git pull
else
    echo "Cloning repository..."
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR/backend"
fi

# Create .env file from example
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo ""
    echo "=========================================="
    echo "IMPORTANT: Please edit the .env file with your actual credentials:"
    echo "nano .env"
    echo "=========================================="
    echo ""
    read -p "Press Enter after you've configured the .env file..."
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p uploads certbot/conf certbot/www

# Build and start Docker containers
echo "Building and starting Docker containers..."
sudo docker-compose down
sudo docker-compose build
sudo docker-compose up -d

# Show container status
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
sudo docker-compose ps
echo ""
echo "Application is running on:"
echo "  - HTTP: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo ""
echo "Useful commands:"
echo "  - View logs: sudo docker-compose logs -f"
echo "  - Stop containers: sudo docker-compose down"
echo "  - Restart containers: sudo docker-compose restart"
echo "  - View backend logs: sudo docker-compose logs -f backend"
echo ""
