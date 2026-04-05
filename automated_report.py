import subprocess
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

import market_data_fetcher
import publish_to_web
from email_config import EMAIL_SENDER, EMAIL_APP_PASSWORD, EMAIL_RECIPIENTS

# Configuration
PROJECT_DIR = r"C:\Users\Pavlos Elpidorou\Documents\AI_Project"
REPORTS_DIR = os.path.join(PROJECT_DIR, "reports")
PROMPT_FILE = os.path.join(PROJECT_DIR, "daily_market_report", "docs", "DAILY_MARKET_REPORT_PROMPT.md")


def send_report_email(report_file, today):
    """Send the report as email with .md attachment."""
    log_file = os.path.join(REPORTS_DIR, "generation.log")
    try:
        with open(report_file, "r", encoding="utf-8") as f:
            report_text = f.read()

        # Strip leading preamble lines Claude sometimes adds before the report body
        lines = report_text.splitlines()
        start = 0
        for i, line in enumerate(lines):
            if "PRUDENTSIGMA" in line or "═" in line or "MACRO PULSE" in line:
                start = i
                break
        clean_body = "\n".join(lines[start:]).strip()

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"PrudentSigma Daily Market Report | {today}"
        msg["From"] = EMAIL_SENDER
        msg["To"] = ", ".join(EMAIL_RECIPIENTS)

        # Plain text body
        msg.attach(MIMEText(clean_body, "plain", "utf-8"))

        # Attach .md file
        with open(report_file, "rb") as f:
            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition",
                f"attachment; filename=PRUDENTSIGMA_{today}.md"
            )
            msg.attach(attachment)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENTS, msg.as_string())

        success_msg = f"Report emailed to {len(EMAIL_RECIPIENTS)} recipients"
        print(success_msg)
        with open(log_file, "a") as log:
            log.write(f"{today} {success_msg}\n")

    except Exception as e:
        error_msg = f"Email failed: {e}"
        print(error_msg)
        with open(log_file, "a") as log:
            log.write(f"{today} {error_msg}\n")


def generate_report():
    """Generate the daily market report using Claude CLI with pre-fetched market data."""
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = os.path.join(REPORTS_DIR, f"report_{today}.md")
    log_file = os.path.join(REPORTS_DIR, "generation.log")

    os.makedirs(REPORTS_DIR, exist_ok=True)

    # Step 1: Pre-fetch market data
    print("[1/4] Fetching market data...")
    try:
        data_block = market_data_fetcher.generate_data_block()
        print(f"[1/4] Data block ready ({len(data_block)} chars)")
    except Exception as e:
        data_block = f"[Market data fetch failed: {e}]\n\nUse WebSearch for all market data.\n"
        print(f"[1/4] Data fetch error: {e}")

    # Step 2: Load prompt template
    print("[2/4] Loading prompt template...")
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            prompt_template = f.read().strip()
    except Exception as e:
        error_msg = f"Error reading prompt file: {e}"
        print(error_msg)
        with open(log_file, "a") as log:
            log.write(f"{today} {error_msg}\n")
        return None

    prompt_with_date = prompt_template.replace("{{TODAY_DATE}}", today)
    final_prompt = data_block + "\n\n---\n\n" + prompt_with_date
    print(f"[2/4] Final prompt: {len(final_prompt)} chars")

    # Step 3: Generate with Claude
    print("[3/4] Generating report with Claude...")
    temp_file = os.path.join(PROJECT_DIR, ".temp_prompt.md")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(final_prompt)

        ps_cmd = f'Get-Content "{temp_file}" -Raw | claude --print --no-session-persistence'
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )

        print(f"[3/4] Claude exit code: {result.returncode}, output: {len(result.stdout)} chars")

        if result.returncode == 0 and result.stdout.strip():
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result.stdout)
            msg = f"Report generated successfully: {output_file}"
            print(msg)
            with open(log_file, "a") as log:
                log.write(f"{today} {msg}\n")
            return output_file
        else:
            error_msg = f"Error: returncode={result.returncode}, stderr={result.stderr[:200]}"
            print(error_msg)
            with open(log_file, "a") as log:
                log.write(f"{today} {error_msg}\n")
            return None

    except subprocess.TimeoutExpired:
        error_msg = "Report generation timed out after 10 minutes"
        print(error_msg)
        with open(log_file, "a") as log:
            log.write(f"{today} {error_msg}\n")
        return None
    except Exception as e:
        error_msg = f"Exception: {e}"
        print(error_msg)
        with open(log_file, "a") as log:
            log.write(f"{today} {error_msg}\n")
        return None
    finally:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass


if __name__ == "__main__":
    report_file = generate_report()
    if report_file:
        today = datetime.now().strftime("%Y-%m-%d")
        # Step 4: Email the report
        print("[4/4] Sending email...")
        send_report_email(report_file, today)
        # Step 5: Publish to website
        print("[5/5] Publishing to website...")
        publish_to_web.publish_report(report_file, today)
    else:
        print("Failed to generate report.")
