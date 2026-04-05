# Google Drive Integration Setup

This guide walks you through setting up automatic report uploads to Google Drive.

## Step 1: Create a Google Cloud Project

1. Go to https://console.cloud.google.com/
2. Create a new project (name it "PrudentSigma")
3. Enable the Google Drive API:
   - Search for "Google Drive API"
   - Click it and press "Enable"

## Step 2: Create a Service Account

1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click "Create Service Account"
3. Fill in details:
   - Service account name: `prudentsigma-reports`
   - Click "Create"
4. Skip optional steps and click "Done"

## Step 3: Create and Download Credentials

1. Click on your service account (prudentsigma-reports)
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose "JSON" 
5. Click "Create"
6. The JSON file will download automatically
7. Rename it to `google_drive_credentials.json`
8. Move it to your project folder: `C:\Users\Pavlos Elpidorou\Documents\AI_Project\`

## Step 4: Share Google Drive Folder with Service Account

1. Create a folder in Google Drive named "PrudentSigma Reports" (or let the script create it)
2. Get the service account email from your JSON credentials file (looks like `xxxxx@xxxxx.iam.gserviceaccount.com`)
3. Go to that folder in Google Drive
4. Click Share
5. Paste the service account email
6. Give it "Editor" access
7. Send

## Step 5: Configure Dashboard

Upload your `google_drive_credentials.json` to Streamlit Cloud:

1. Go to https://streamlit.io/cloud
2. Find your app, click the **...** menu
3. Click **Settings**
4. Click **Secrets**
5. Create a secret named `GOOGLE_DRIVE_CREDENTIALS` and paste the entire contents of your `google_drive_credentials.json` file

## Step 6: Test Configuration

After setup, run this in PowerShell:
```powershell
cd "C:\Users\Pavlos Elpidorou\Documents\AI_Project"
.venv\Scripts\python.exe -c "from drive_utils import GoogleDriveManager; gm = GoogleDriveManager('google_drive_credentials.json'); gm.create_reports_folder(); print('Setup successful!')"
```

If it prints "Setup successful!", you're ready to go!

## What Happens Next

- Local reports will auto-upload to Google Drive after generation (6:00 AM daily)
- Cloud dashboard will display latest reports from Google Drive
- Reports accessible from anywhere via online dashboard

## Troubleshooting

**"Failed to authenticate"**: Check that credentials JSON is in the right folder

**"Permission denied"**: Make sure service account email has access to the Google Drive folder

**"Folder not found"**: The script will create the folder automatically on first run

---

After completing these steps, reports will automatically sync to the cloud!
