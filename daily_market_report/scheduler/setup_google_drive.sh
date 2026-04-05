# Automated Google Drive Setup Script

This script automates parts of the Google Drive setup process.

## What This Script Does

✅ **Creates Google Cloud project** (if you provide project name)  
✅ **Enables Google Drive API**  
✅ **Creates service account**  
✅ **Generates and downloads credentials**  
✅ **Shares Google Drive folder**  
❌ **Cannot access your Google account** (you must run this)

## Prerequisites

1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. Authenticate: `gcloud auth login`
3. Set project: `gcloud config set project YOUR_PROJECT_ID`

## Usage

```bash
# Make executable
chmod +x setup_google_drive.sh

# Run with your desired project name
./setup_google_drive.sh "prudentsigma-reports"
```

## Script Content

```bash
#!/bin/bash

PROJECT_NAME=$1
SERVICE_ACCOUNT_NAME="prudentsigma-reports"
FOLDER_NAME="PrudentSigma Reports"

if [ -z "$PROJECT_NAME" ]; then
    echo "Usage: $0 <project-name>"
    exit 1
fi

echo "Setting up Google Drive integration for $PROJECT_NAME..."

# Create project
echo "Creating Google Cloud project..."
gcloud projects create $PROJECT_NAME --name="$PROJECT_NAME"

# Set as default
gcloud config set project $PROJECT_NAME

# Enable Drive API
echo "Enabling Google Drive API..."
gcloud services enable drive.googleapis.com

# Create service account
echo "Creating service account..."
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --description="Service account for PrudentSigma report uploads" \
    --display-name="PrudentSigma Reports"

# Get service account email
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_NAME.iam.gserviceaccount.com"

# Create credentials
echo "Creating credentials..."
gcloud iam service-accounts keys create google_drive_credentials.json \
    --iam-account=$SERVICE_ACCOUNT_EMAIL

echo "Credentials saved to google_drive_credentials.json"

# Create Drive folder and share (this part requires manual intervention)
echo ""
echo "NEXT STEPS (Manual):"
echo "1. Create a folder named '$FOLDER_NAME' in Google Drive"
echo "2. Share it with: $SERVICE_ACCOUNT_EMAIL"
echo "3. Give 'Editor' access"
echo ""
echo "Then copy google_drive_credentials.json to your project folder."
```

## Limitations

This script can only automate the Google Cloud Console parts. You still need to:

1. **Authenticate with Google** (manual)
2. **Share the Drive folder** (manual - requires your Google account)
3. **Upload credentials to Streamlit Cloud** (manual - requires your Streamlit account)

## Alternative: Manual Setup (Recommended)

Since the script has limitations, I recommend following the manual steps in GOOGLE_DRIVE_SETUP.md - it's actually faster and more reliable.

**Time estimate**: 10-15 minutes total