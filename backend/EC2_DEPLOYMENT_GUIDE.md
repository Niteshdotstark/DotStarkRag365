# EC2 Deployment Guide - Website Crawler Backend

## 🎯 Quick Start (5 Steps)

1. Launch EC2 instance
2. Install dependencies
3. Configure environment
4. Start FastAPI
5. Test the system

---

## 📋 Prerequisites

- AWS Account with EC2 access
- AWS CLI configured locally
- SSH key pair (.pem file)
- Domain/IP for API access (optional)

---

## 🚀 Step 1: Launch EC2 Instance

### Option A: Using AWS Console

1. Go to EC2 Dashboard → Launch Instance
2. Configure:
   ```
   Name: website-crawler-backend
   AMI: Ubuntu Server 22.04 LTS
   Instance type: t3.medium (2 vCPU, 4 GB RAM)
   Key pair: Create new or select existing
   Storage: 30 GB gp3 SSD
   ```

3. Security Group (Inbound Rules):
   ```
   SSH (22)     - Your IP
   Custom (8000) - 0.0.0.0/0 (or your IP for testing)
   ```

4. Launch instance

### Option B: Using AWS CLI

```bash
# Create security group
aws ec2 create-security-group \
  --group-name website-crawler-sg \
  --description "Security group for website crawler"

# Add inbound rules
aws ec2 authorize-security-group-ingress \
  --group-name website-crawler-sg \
  --protocol tcp --port 22 --cidr your-ip/32

aws ec2 authorize-security-group-ingress \
  --group-name website-crawler-sg \
  --protocol tcp --port 8000 --cidr 0.0.0.0/0

# Launch instance
aws ec2 run-instances \
  --image-id ami-0c7217cdde317cfec \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-groups website-crawler-sg \
  --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":30}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=website-crawler-backend}]'
```

---

## 🔧 Step 2: Connect and Install Dependencies

### Connect to EC2

```bash
# Get instance public IP
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=website-crawler-backend" \
  --query "Reservations[0].Instances[0].PublicIpAddress"

# SSH into instance
ssh -i your-key.pem ubuntu@YOUR_EC2_IP
```

### Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install other dependencies
sudo apt install -y git curl wget build-essential libpq-dev
```

### Setup PostgreSQL

```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE website_crawler;
CREATE USER crawler_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE website_crawler TO crawler_user;
\q
EOF
```

---

## 📦 Step 3: Deploy Application

### Clone Repository

```bash
# Create app directory
cd /home/ubuntu
mkdir -p app
cd app

# Clone your repository (or upload files)
git clone https://github.com/your-repo/ChatBotBE.git
# OR upload via SCP:
# scp -i your-key.pem -r ChatBotBE ubuntu@YOUR_EC2_IP:/home/ubuntu/app/

cd ChatBotBE/backend
```

### Create Virtual Environment

```bash
# Create venv
python3.11 -m venv venv

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Install Python Dependencies

```bash
# Install requirements
pip install -r requirements.txt

# If requirements.txt doesn't exist, install manually:
pip install fastapi==0.104.1 \
            uvicorn==0.24.0 \
            sqlalchemy==2.0.23 \
            psycopg2-binary==2.9.9 \
            boto3==1.34.0 \
            python-dotenv==1.0.0 \
            pydantic==2.5.0 \
            python-jose==3.3.0 \
            passlib==1.7.4 \
            python-multipart==0.0.6 \
            opensearch-py==2.4.0
```

---

## ⚙️ Step 4: Configure Environment

### Create .env File

```bash
# Create env file
cat > env << 'EOF'
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id
BEDROCK_ROLE_ARN=arn:aws:iam::your-account-id:role/BedrockExecutionRole

# Database Configuration
DATABASE_URL=postgresql://crawler_user:your_secure_password@localhost/website_crawler

# S3 Configuration
S3_BUCKET_NAME=rag-chat-uploads
S3_REGION=us-east-1

# Application Configuration
SECRET_KEY=your-secret-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF

# Set permissions
chmod 600 env
```

### Configure AWS Credentials

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure
# Enter:
#   AWS Access Key ID
#   AWS Secret Access Key
#   Default region: us-east-1
#   Default output format: json
```

### Initialize Database

```bash
# Run database migrations (if using Alembic)
# alembic upgrade head

# Or create tables directly
python << EOF
from database import engine, Base
from models import User, Tenant, Agent, AgentCollection, WebsiteCrawl
Base.metadata.create_all(bind=engine)
print("✅ Database tables created")
EOF
```

---

## 🚀 Step 5: Start Application

### Option A: Run Directly (for testing)

```bash
# Activate venv
source venv/bin/activate

# Start FastAPI
uvicorn main:app --host 0.0.0.0 --port 8000

# Test in another terminal:
curl http://YOUR_EC2_IP:8000/docs
```

### Option B: Run as Systemd Service (recommended)

```bash
# Create systemd service file
sudo tee /etc/systemd/system/fastapi.service > /dev/null << 'EOF'
[Unit]
Description=FastAPI Website Crawler
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/app/ChatBotBE/backend
Environment="PATH=/home/ubuntu/app/ChatBotBE/backend/venv/bin"
ExecStart=/home/ubuntu/app/ChatBotBE/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Start service
sudo systemctl start fastapi

# Enable on boot
sudo systemctl enable fastapi

# Check status
sudo systemctl status fastapi

# View logs
sudo journalctl -u fastapi -f
```

---

## ✅ Step 6: Test Deployment

### Test API Health

```bash
# From your local machine
curl http://YOUR_EC2_IP:8000/docs

# Should return Swagger UI
```

### Test Crawl Endpoint

```bash
# Initiate crawl
curl -X POST http://YOUR_EC2_IP:8000/tenants/999/websites/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "max_pages": 5,
    "crawl_scope": "HOST_ONLY"
  }'

# Response:
# {
#   "website_id": "uuid",
#   "knowledge_base_id": "KB123",
#   "status": "STARTING",
#   "message": "..."
# }
```

### Test Status Endpoint

```bash
# Check status (replace {website_id} with actual ID)
curl http://YOUR_EC2_IP:8000/tenants/999/websites/{website_id}/status

# Response:
# {
#   "status": "COMPLETE",
#   "pages_crawled": 5,
#   ...
# }
```

### Test Chat Endpoint

```bash
# Chat with crawled data
curl -X POST http://YOUR_EC2_IP:8000/tenants/999/websites/{website_id}/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this website about?"
  }'

# Response:
# {
#   "answer": "This website is about...",
#   "sources": [...]
# }
```

---

## 🛡️ Security Best Practices

### 1. Restrict Security Group

```bash
# Only allow your IP for testing
aws ec2 authorize-security-group-ingress \
  --group-name website-crawler-sg \
  --protocol tcp --port 8000 --cidr YOUR_IP/32
```

### 2. Use IAM Role (instead of AWS credentials)

```bash
# Create IAM role for EC2
aws iam create-role \
  --role-name EC2-WebsiteCrawler-Role \
  --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name EC2-WebsiteCrawler-Role \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# Attach role to EC2 instance
aws ec2 associate-iam-instance-profile \
  --instance-id i-xxxxx \
  --iam-instance-profile Name=EC2-WebsiteCrawler-Role
```

### 3. Enable HTTPS (optional)

```bash
# Install Nginx
sudo apt install -y nginx certbot python3-certbot-nginx

# Configure Nginx as reverse proxy
sudo tee /etc/nginx/sites-available/fastapi > /dev/null << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

---

## 📊 Monitoring and Logs

### View Application Logs

```bash
# Real-time logs
sudo journalctl -u fastapi -f

# Last 100 lines
sudo journalctl -u fastapi -n 100

# Logs from today
sudo journalctl -u fastapi --since today
```

### Monitor System Resources

```bash
# CPU and Memory
htop

# Disk usage
df -h

# Network connections
sudo netstat -tulpn | grep 8000
```

### Check AWS Costs

```bash
# List OpenSearch collections
aws opensearchserverless list-collections --region us-east-1

# List Knowledge Bases
aws bedrock-agent list-knowledge-bases --region us-east-1

# Check if any are running (costing money)
```

---

## 🧹 Cleanup After Testing

### CRITICAL: Delete OpenSearch Collections

```bash
# Run cleanup script
cd /home/ubuntu/app/ChatBotBE/backend
source venv/bin/activate
python IMMEDIATE_CLEANUP.py

# Type: DELETE NOW
```

### Stop EC2 Instance (if not needed)

```bash
# From your local machine
aws ec2 stop-instances --instance-ids i-xxxxx

# Or terminate completely
aws ec2 terminate-instances --instance-ids i-xxxxx
```

---

## 🔧 Troubleshooting

### Issue: Can't connect to EC2

```bash
# Check security group allows your IP
aws ec2 describe-security-groups --group-names website-crawler-sg

# Check instance is running
aws ec2 describe-instances --instance-ids i-xxxxx
```

### Issue: FastAPI won't start

```bash
# Check logs
sudo journalctl -u fastapi -n 50

# Check if port 8000 is in use
sudo lsof -i :8000

# Test manually
cd /home/ubuntu/app/ChatBotBE/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Issue: Database connection error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U crawler_user -d website_crawler -h localhost

# Check env file
cat env | grep DATABASE_URL
```

### Issue: AWS permissions error

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check IAM role (if using)
aws iam get-role --role-name EC2-WebsiteCrawler-Role

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

---

## 💰 Cost Monitoring

### Hourly Costs:
- EC2 t3.medium: ~$0.04/hour
- OpenSearch (if created): ~$0.96/hour ⚠️
- Bedrock API: Pay-per-use

### Daily Costs:
- EC2: ~$1/day
- OpenSearch: ~$23/day ⚠️

### **IMPORTANT**: Run `IMMEDIATE_CLEANUP.py` after testing!

---

## 📝 Quick Reference

### Start/Stop Service
```bash
sudo systemctl start fastapi
sudo systemctl stop fastapi
sudo systemctl restart fastapi
sudo systemctl status fastapi
```

### View Logs
```bash
sudo journalctl -u fastapi -f
```

### Update Code
```bash
cd /home/ubuntu/app/ChatBotBE/backend
git pull
sudo systemctl restart fastapi
```

### Cleanup Resources
```bash
python IMMEDIATE_CLEANUP.py
```

---

## ✅ Deployment Checklist

- [ ] EC2 instance launched
- [ ] Security group configured
- [ ] Dependencies installed
- [ ] PostgreSQL setup
- [ ] Environment configured
- [ ] AWS credentials configured
- [ ] FastAPI service running
- [ ] API endpoints tested
- [ ] Crawl tested successfully
- [ ] Chat tested successfully
- [ ] **Cleanup script ready** (IMMEDIATE_CLEANUP.py)
- [ ] Monitoring setup
- [ ] Backup strategy planned

---

## 🎉 Success!

Your website crawler backend is now deployed on EC2!

**Next Steps:**
1. Test with a small website (5-10 pages)
2. Monitor AWS costs
3. **Run cleanup script after testing**
4. Consider cost optimization (ChromaDB solution)

**Remember**: OpenSearch Serverless costs $700/month per collection. Delete immediately after testing!
