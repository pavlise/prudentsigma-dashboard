import subprocess
import os
from datetime import datetime

# Configuration
PROJECT_DIR = r"C:\Users\Pavlos Elpidorou\Documents\AI_Project"
REPORTS_DIR = os.path.join(PROJECT_DIR, "reports")
PROMPT_FILE = os.path.join(PROJECT_DIR, "DAILY_MARKET_REPORT_PROMPT.md")

import subprocess
import os
from datetime import datetime

# Configuration
PROJECT_DIR = r"C:\Users\Pavlos Elpidorou\Documents\AI_Project"
REPORTS_DIR = os.path.join(PROJECT_DIR, "reports")
PROMPT_FILE = os.path.join(PROJECT_DIR, "DAILY_MARKET_REPORT_PROMPT.md")

def generate_report():
    """Generate the daily market report using Claude CLI"""
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = os.path.join(REPORTS_DIR, f"report_{today}.md")
    log_file = os.path.join(REPORTS_DIR, "generation.log")

    # Ensure reports directory exists
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # Read the prompt file
    try:
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            prompt_content = f.read().strip()
        print(f"[LOG] Prompt loaded, length: {len(prompt_content)}")
    except Exception as e:
        error_msg = f"Error reading prompt file: {e}"
        print(error_msg)
        with open(log_file, 'a') as log:
            log.write(f"{today} {error_msg}\n")
        return None

    # Write prompt to temporary file for piping
    temp_file = os.path.join(PROJECT_DIR, ".temp_prompt.md")
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        print(f"[LOG] Temporary prompt file created")

        # Use PowerShell to pipe the file to claude with --no-session-persistence
        ps_cmd = f'Get-Content "{temp_file}" -Raw | claude --print --no-session-persistence'
        result = subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True, text=True, timeout=300)
        
        print(f"[LOG] Claude exit code: {result.returncode}")
        print(f"[LOG] Output length: {len(result.stdout)}")
        print(f"[LOG] Error length: {len(result.stderr)}")
        
        if result.returncode == 0 and result.stdout.strip():
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            success_msg = f"Report generated successfully: {output_file}"
            print(success_msg)
            with open(log_file, 'a') as log:
                log.write(f"{today} {success_msg}\n")
            return output_file
        else:
            error_msg = f"Error: returncode={result.returncode}, stderr={result.stderr[:200]}"
            print(error_msg)
            with open(log_file, 'a') as log:
                log.write(f"{today} {error_msg}\n")
            return None
    except subprocess.TimeoutExpired:
        error_msg = "Report generation timed out after 5 minutes"
        print(error_msg)
        with open(log_file, 'a') as log:
            log.write(f"{today} {error_msg}\n")
        return None
    except Exception as e:
        error_msg = f"Exception: {e}"
        print(error_msg)
        with open(log_file, 'a') as log:
            log.write(f"{today} {error_msg}\n")
        return None
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass

if __name__ == "__main__":
    # Generate report
    report_file = generate_report()
    if report_file:
        print("Report generated. Run 'streamlit run dashboard.py' to view.")
    else:
        print("Failed to generate report.")