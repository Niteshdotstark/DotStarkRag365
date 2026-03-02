# EC2 Deployment Instructions

## Prerequisites
- EC2 instance running Ubuntu
- Security group configured to allow:
  - Port 22 (SSH)
  - Port 80 (HTTP)
  - Port 443 (HTTPS)
  - Port 8000 (FastAPI - optional for direct access)

## Quick Deployment

### Step 1: Connect to your EC2 instance
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### Step 2: Run the deployment script
```bash
# Download and run the deployment script
curl -o deploy.sh https://raw.githubusercontent.com/Niteshdotstark/DotStarkRag365/main/backend/ec2-deploy.sh
chmod +x deploy.sh
./deploy.sh
```

## Manual Deployment

### Step 1: Install Docker and Docker Compose
```bash
# Update packages
sudo apt update

# Install Docker
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add user to docker group
sudo usermod -aG docker ${USER}

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

### Step 2: Clone the repository
```bash
cd ~
git clone https://github.com/Niteshdotstark/DotStarkRag365.git
cd DotStarkRag365/backend
```

### Step 3: Configure environment variables
```bash
# Copy the example env file
cp .env.example .env

# Edit the .env file with your credentials
nano .env
```

Update the following in `.env`:
```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_actual_access_key
AWS_SECRET_ACCESS_KEY=your_actual_secret_key
AWS_REGION=ap-south-1

# Database Configuration (default is fine for Docker setup)
DATABASE_URL=postgresql://postgres:123@postgres_db:5432/multi_tenant_admin

# OpenSearch Configuration
OPENSEARCH_ENDPOINT=your_opensearch_endpoint
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=your_password
```

### Step 4: Create necessary directories
```bash
mkdir -p uploads certbot/conf certbot/www
```

### Step 5: Build and start containers
```bash
# Build the Docker images
sudo docker-compose build

# Start the containers
sudo docker-compose up -d

# Check container status
sudo docker-compose ps
```

### Step 6: Verify deployment
```bash
# Check logs
sudo docker-compose logs -f backend

# Test the API
curl http://localhost:8000/docs
```

## Container Management

### View logs
```bash
# All containers
sudo docker-compose logs -f

# Specific container
sudo docker-compose logs -f backend
sudo docker-compose logs -f postgres_db
sudo docker-compose logs -f nginx
```

### Restart containers
```bash
# Restart all
sudo docker-compose restart

# Restart specific container
sudo docker-compose restart backend
```

### Stop containers
```bash
sudo docker-compose down
```

### Rebuild after code changes
```bash
cd ~/DotStarkRag365/backend
git pull
sudo docker-compose down
sudo docker-compose build
sudo docker-compose up -d
```

## SSL/HTTPS Setup (Optional)

### Step 1: Update nginx configuration
Edit `nginx.conf` to use your domain name.

### Step 2: Obtain SSL certificate
```bash
sudo docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot -d yourdomain.com -d www.yourdomain.com
```

### Step 3: Update nginx to use HTTPS
Replace `nginx.conf` with `nginx-https.conf` and restart nginx:
```bash
cp nginx-https.conf nginx.conf
sudo docker-compose restart nginx
```

## Troubleshooting

### Check if containers are running
```bash
sudo docker ps
```

### Check container logs for errors
```bash
sudo docker-compose logs backend
```

### Restart a specific service
```bash
sudo docker-compose restart backend
```

### Access container shell
```bash
sudo docker exec -it fastapi-backend bash
```

### Check database connection
```bash
sudo docker exec -it postgres_db psql -U postgres -d multi_tenant_admin
```

### Remove all containers and volumes (fresh start)
```bash
sudo docker-compose down -v
sudo docker-compose up -d
```

## Security Recommendations

1. Change default PostgreSQL password in `docker-compose.yml`
2. Use AWS IAM roles instead of access keys when possible
3. Set up SSL/HTTPS for production
4. Configure firewall rules to restrict access
5. Regularly update Docker images and system packages
6. Use secrets management for sensitive data

## Monitoring

### Check resource usage
```bash
sudo docker stats
```

### Check disk space
```bash
df -h
sudo docker system df
```

### Clean up unused Docker resources
```bash
sudo docker system prune -a
```

## Accessing the Application

- API Documentation: `http://your-ec2-ip/docs`
- Health Check: `http://your-ec2-ip/health`
- Admin Panel: `http://your-ec2-ip/admin`

## Support

For issues or questions, check the logs first:
```bash
sudo docker-compose logs -f
```
