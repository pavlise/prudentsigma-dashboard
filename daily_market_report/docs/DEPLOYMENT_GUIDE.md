# PrudentSigma Dashboard - Online Deployment Guide

## Current Status
✓ Dashboard created with authentication  
✓ Credentials configured (see below)  
✓ Ready for online deployment

## Default Login Credentials (CHANGE AFTER FIRST LOGIN)

```
Username: admin
Password: admin123

Username: trader
Password: trader123
```

## Deployment Option 1: Streamlit Cloud (RECOMMENDED - Free & Easiest)

### Prerequisites
1. GitHub account (https://github.com)
2. This project pushed to a GitHub repository

### Step 1: Push to GitHub
```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit with authenticated dashboard"
git remote add origin https://github.com/YOUR_USERNAME/prudentsigma-dashboard.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Streamlit Cloud
1. Go to https://streamlit.io/cloud
2. Click "New app"
3. Select your GitHub repository
4. Set main file path: `dashboard.py`
5. Click "Deploy"

### Step 3: Configure Repository Secrets
In your GitHub repo settings, add the following to keep `config.yaml` secure:
- Store credentials in `.streamlit/secrets.toml` on Streamlit Cloud (see next section)

Your dashboard will be live at: `https://your-username-prudentsigma.streamlit.app`

---

## Deployment Option 2: Keep Local with Remote Access

If you prefer to keep it running on your local machine but access it remotely:

### Setup Ngrok (Free Remote Access)
```
1. Download ngrok: https://ngrok.com
2. Run: ngrok http 8501
3. Get public URL that routes to your local dashboard
4. Share that URL (it changes each restart unless you upgrade)
```

---

## Deployment Option 3: Cloud VPS (More Control, Costs $5-10/month)

Services like DigitalOcean, AWS, or Azure can host this permanently.

Example: DigitalOcean Droplet
```bash
# SSH into your server
ssh root@your_server_ip

# Install dependencies
apt update
apt install python3-pip python3-venv

# Clone your repo and deploy
git clone https://github.com/YOUR_USERNAME/prudentsigma-dashboard.git
cd prudentsigma-dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with nohup (keeps running after disconnect)
nohup streamlit run dashboard.py --server.port=80 &
```

---

## Setup Instructions for Streamlit Cloud Secrets

To keep credentials secure on Streamlit Cloud:

1. In your Streamlit Cloud app settings, add `.streamlit/secrets.toml`:
```toml
[credentials]
admin_password = "admin123"
trader_password = "trader123"
```

2. Update `dashboard.py` to read from secrets when deployed

---

## After Deployment

### Access Dashboard
- Local: http://localhost:8501
- Remote: `https://your-app-url`

### Change Passwords
1. Log in with your username
2. Contact admin to update `config.yaml`
3. Redeploy

### Verify Reports Still Generate
- Check that local Task Scheduler tasks still run daily
- Reports will be saved locally but NOT accessible from deployed dashboard
- Solution: Sync reports to cloud storage (S3, Drive) or run dashboard script remotely

---

## Recommended Next Steps

1. **Create GitHub Account** and push this repo
2. **Deploy to Streamlit Cloud** (5 minutes)
3. **Update Passwords** after first login
4. **Set up automatic report upload** to cloud storage for remote access

Would you like me to help implement any of these deployment options?
