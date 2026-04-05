# Google Drive Integration Setup - Next Steps

Your scripts have been updated to automatically sync reports to Google Drive and read them from the cloud. Follow these steps to complete the setup.

## Phase 1: Google Cloud Project Setup (Done Offline)

Complete these steps from the GOOGLE_DRIVE_SETUP.md file:

1. Create a Google Cloud project
2. Enable Google Drive API
3. Create a service account
4. Download credentials as JSON file
5. Share a folder on Google Drive with the service account email
6. Place `google_drive_credentials.json` in your project folder

**Expected Result**: You should have `google_drive_credentials.json` in `C:\Users\Pavlos Elpidorou\Documents\AI_Project\`

---

## Phase 2: Test Local Synchronization (5-10 minutes)

### Step 1: Verify Script Updates

The following files have been updated:

- **automated_report.py**
  - Now automatically uploads reports to Google Drive after generation
  - Falls back gracefully if credentials not found
  - Logs upload success/failure to `reports/generation.log`

- **dashboard.py**
  - Now tries to read from Google Drive first
  - Falls back to local reports if Drive unavailable
  - Shows report source (Google Drive or Local)
  - Displays helpful setup instructions if no reports found

- **drive_utils.py**
  - Helper module for Google Drive operations
  - Already supports authentication and report management

### Step 2: Test With Local Credentials

1. Ensure `google_drive_credentials.json` is in your project folder
2. Run the local dashboard:
   ```powershell
   streamlit run dashboard.py
   ```
3. You should see helpful error messages if anything is missing

### Step 3: Manually Trigger a Report Generation

Run the report generation script manually to test the upload:

```powershell
cd "C:\Users\Pavlos Elpidorou\Documents\AI_Project"
python automated_report.py
```

**Expected Output**:
```
Report generated successfully.
Uploading report to Google Drive...
Report uploaded to Google Drive successfully (ID: xxxxx)
```

Check your Google Drive to see if the report appeared in the shared folder.

---

## Phase 3: Configure Streamlit Cloud Secrets

### Step 1: Prepare Your Credentials

1. Open `google_drive_credentials.json` in your text editor
2. Copy the entire JSON content

### Step 2: Add to Streamlit Secrets

1. Go to: https://share.streamlit.io/settings/secrets
2. In the "Secrets" section, add:

```yaml
GOOGLE_DRIVE_CREDENTIALS = {
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "your-x509-cert-url"
}
```

**Important**: Keep the JSON formatted exactly as shown (no extra quotes around the dict)

### Step 3: Test the Cloud App

1. Redeploy your app (push to GitHub)
2. Visit: https://pavlise-prudentsigma-dashboard.streamlit.app
3. Enter credentials: admin / admin123 (or trader / trader123)
4. The dashboard should now try to load reports from Google Drive

---

## Phase 4: Verify Automatic Daily Sync

### Check Local Generation

1. Windows Task Scheduler already runs `generate_daily_report.bat` at 6:00 AM
2. Check `reports/generation.log` to see upload status:
   ```
   2025-01-25 - Report generated successfully.
   2025-01-25 - Uploaded to Google Drive (ID: file123)
   ```

### Check Cloud Dashboard

1. Visit the online dashboard: https://pavlise-prudentsigma-dashboard.streamlit.app
2. Log in with your credentials
3. You should see the latest report from Google Drive

---

## Troubleshooting

### "Google Drive credentials not found"
- Solution: Place `google_drive_credentials.json` in project folder

### "Google Drive connection unavailable"
- Solution: Check that `GOOGLE_DRIVE_CREDENTIALS` is configured in Streamlit Secrets

### "Permission denied" errors
- Solution: Ensure the service account email is shared with the Google Drive folder (with Editor access)

### "Report uploaded but not visible on cloud dashboard"
- Solution: Click "Refresh Dashboard" button on the web app
- Or wait a few seconds for Streamlit to update

### Reports showing "Local" source instead of "Google Drive"
- Solution: Check that credentials are correctly configured and the Drive folder has the reports

---

## How It Works (Technical Overview)

### Local System (Your PC)
```
6:00 AM → Task Scheduler runs generate_daily_report.bat
   ↓
Report generated: reports/report_2025-01-25.md
   ↓
automated_report.py calls GoogleDriveManager.upload_report()
   ↓
Report synced to Google Drive in shared folder
   ↓
generation.log updated with upload status
```

### Cloud Dashboard
```
User visits: https://pavlise-prudentsigma-dashboard.streamlit.app
   ↓
dashboard.py runs get_drive_manager()
   ↓
Connects to Google Drive using Streamlit Secrets
   ↓
Retrieves latest report from Drive
   ↓
Displays with source: "Google Drive"
```

### Fallback Logic
```
If Google Drive unavailable → Try local reports folder
If local folder unavailable → Show setup instructions
```

---

## Verification Checklist

- [ ] google_drive_credentials.json placed in project folder
- [ ] GOOGLE_DRIVE_CREDENTIALS added to Streamlit Cloud Secrets
- [ ] automated_report.py tested and uploads successfully (see generation.log)
- [ ] dashboard.py displays reports with "Google Drive" source
- [ ] Cloud dashboard loads reports when you log in
- [ ] Next scheduled report (tomorrow 6:00 AM) syncs automatically

---

## Support

If you run into issues:

1. Check the **generation.log** file in the reports folder for local errors
2. Check the **Streamlit Cloud logs** at: https://share.streamlit.io/projects/pavlise-prudentsigma-dashboard for cloud errors
3. Verify Google Drive folder permissions (service account email must have Editor access)
4. Test locally first before diagnosing cloud issues
