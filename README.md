# PrudentSigma Daily Market Report Dashboard

A secure, automated dashboard displaying daily market analysis reports with user authentication.

## Features

- **Authenticated Access** - Username/password login for secure access
- **Automated Report Generation** - Daily market reports generated at 6:00 AM
- **Web-Based Dashboard** - View reports from anywhere via web browser
- **Responsive Design** - Works on desktop and mobile devices
- **Community-Driven** - Built with Streamlit and powered by Claude

## Quick Start

### Local Deployment

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the dashboard:**
   ```bash
   streamlit run dashboard.py
   ```

3. **Access dashboard:**
   - Open http://localhost:8501
   - Login with credentials in `config.yaml`

### Cloud Deployment (Streamlit Cloud)

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for step-by-step instructions.

## Default Credentials

| Username | Password |
|----------|----------|
| admin    | admin123 |
| trader   | trader123 |

**⚠️ Change these credentials immediately after first login!**

## Project Structure

```
├── dashboard.py                 # Main Streamlit app
├── automated_report.py          # Report generation script
├── config.yaml                  # Credentials (NOT committed to git)
├── requirements.txt             # Python dependencies
├── DEPLOYMENT_GUIDE.md          # Deployment instructions
├── .streamlit/
│   └── config.toml             # Streamlit configuration
└── reports/                     # Generated daily reports
```

## Automated Daily Reports

Reports are automatically generated daily at 6:00 AM (Windows Task Scheduler).

- **Report Generation**: 6:00 AM
- **Dashboard Start**: 5:55 AM
- **Storage**: `reports/report_YYYY-MM-DD.md`

## Configuration

Edit `config.yaml` to add/modify users:

```yaml
credentials:
  usernames:
    your_username:
      name: Your Name
      email: your@email.com
      password: hashed_password_here
```

Use `setup_credentials.py` to generate hashed passwords.

## Support

- For deployment help, see DEPLOYMENT_GUIDE.md
- Local issues: Check reports/generation.log
- Streamlit Cloud issues: Check app logs in Streamlit Cloud dashboard

## License

Private use only.
