"""
Defect Report Analyst
=====================
Reads an Excel defect tracking sheet, uses Claude AI to analyze
open defects and blockers, generates a stakeholder report,
and optionally emails it to your team.

Author: Monica Reddy
"""

import os
import json
import smtplib
import pandas as pd
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from anthropic import Anthropic
from dotenv import load_dotenv

# ── Load .env file (your secret API key lives here) ──────────────────────────
# This reads the .env file in the same folder as main.py
load_dotenv()

# ── Configuration ────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
EMAIL_SENDER      = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD    = os.environ.get("EMAIL_PASSWORD", "")   # Gmail App Password
EMAIL_RECIPIENTS  = os.environ.get("EMAIL_RECIPIENTS", "") # Comma-separated

EXCEL_FILE        = "data/defects.xlsx"   # Path to your Excel file
OUTPUT_DIR        = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Step 1: Read Excel ────────────────────────────────────────────────────────

def load_defects(filepath: str) -> tuple[pd.DataFrame, str]:
    """Load defect data from Excel and convert to a clean text summary."""
    print(f"\n📂 Reading Excel file: {filepath}")
    df = pd.read_excel(filepath)

    # Normalize column names (strip spaces, lowercase)
    df.columns = [c.strip() for c in df.columns]

    print(f"   ✅ Loaded {len(df)} defects, {len(df.columns)} columns")
    print(f"   Columns found: {list(df.columns)}")

    # Build a text representation for the LLM
    summary_lines = []
    summary_lines.append(f"Total defects in sheet: {len(df)}")
    summary_lines.append(f"Columns: {', '.join(df.columns)}\n")

    # Count by status if column exists
    status_col = next((c for c in df.columns if "status" in c.lower()), None)
    if status_col:
        counts = df[status_col].value_counts().to_dict()
        summary_lines.append(f"Status breakdown: {json.dumps(counts)}")

    # Count by severity/priority if exists
    sev_col = next((c for c in df.columns if any(k in c.lower() for k in ["sever","prior","type","blocker"])), None)
    if sev_col:
        counts = df[sev_col].value_counts().to_dict()
        summary_lines.append(f"Severity/Priority breakdown: {json.dumps(counts)}")

    # Full data as CSV text (LLM reads this)
    csv_text = df.to_csv(index=False)
    full_text = "\n".join(summary_lines) + "\n\nFULL DATA:\n" + csv_text

    return df, full_text


# ── Step 2: Analyze with Claude ───────────────────────────────────────────────

def analyze_with_claude(data_text: str) -> str:
    """Send defect data to Claude and get a stakeholder report back."""
    print("\n🤖 Sending data to Claude for analysis...")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    system_prompt = """You are a senior software engineering analyst who specializes in 
defect tracking and project health reporting. Your job is to read raw defect/bug tracking 
data and produce a clear, concise stakeholder report.

Your reports are:
- Written in plain English (no jargon)
- Focused on what matters: blockers, trends, risk, and recommended actions
- Structured so a non-technical manager can understand them in 2 minutes
- Honest about risks without being alarmist

Always format your report with these exact sections:
1. Executive Summary (3-4 sentences max)
2. Key Numbers (use a simple table format)
3. Blockers & Critical Issues (list each one with owner if available)
4. Trends & Patterns (what you notice in the data)
5. Recommended Actions (top 3, numbered, specific)
6. Overall Health (one of: 🟢 Healthy / 🟡 Needs Attention / 🔴 At Risk — with one sentence reason)"""

    user_prompt = f"""Please analyze the following defect tracking data and generate 
a daily stakeholder report.

Today's date: {datetime.now().strftime("%B %d, %Y")}

DEFECT DATA:
{data_text}

Generate the stakeholder report now."""

    # Call Claude API
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1500,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    report = message.content[0].text
    print("   ✅ Analysis complete")
    return report


# ── Step 3: Save Report ───────────────────────────────────────────────────────

def save_report(report: str) -> Path:
    """Save the report to a dated text file."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename  = OUTPUT_DIR / f"defect_report_{timestamp}.txt"

    header = f"""{'='*60}
DEFECT STATUS REPORT
Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}
{'='*60}

"""
    full_report = header + report

    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_report)

    print(f"\n💾 Report saved: {filename}")
    return filename


# ── Step 4: Email Report ──────────────────────────────────────────────────────

def send_email(report: str, report_file: Path):
    """Email the report to stakeholders via Gmail."""
    if not EMAIL_SENDER or not EMAIL_RECIPIENTS:
        print("\n📧 Email not configured — skipping send (see README to enable)")
        return

    print(f"\n📧 Sending report to: {EMAIL_RECIPIENTS}")

    recipients = [r.strip() for r in EMAIL_RECIPIENTS.split(",")]
    subject    = f"Defect Status Report — {datetime.now().strftime('%B %d, %Y')}"

    # Build email body
    body = f"""Hi Team,

Please find today's automated defect status report below.

{report}

---
This report was generated automatically by the Defect Report Analyst.
Source file: {EXCEL_FILE}
"""

    msg = MIMEMultipart()
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, recipients, msg.as_string())
        print("   ✅ Email sent successfully")
    except Exception as e:
        print(f"   ⚠️  Email failed: {e}")
        print("   (Report was still saved locally)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  DEFECT REPORT ANALYST — Powered by Claude AI")
    print("=" * 60)

    # Check API key
    if not ANTHROPIC_API_KEY:
        print("\n❌ ERROR: ANTHROPIC_API_KEY not set.")
        print("   Run: set ANTHROPIC_API_KEY=your-key-here  (Windows)")
        print("   Run: export ANTHROPIC_API_KEY=your-key-here  (Mac/Linux)")
        return

    # Check Excel file
    if not Path(EXCEL_FILE).exists():
        print(f"\n❌ ERROR: Excel file not found at '{EXCEL_FILE}'")
        print("   Place your defects.xlsx file in the data/ folder")
        return

    # Run the pipeline
    df, data_text   = load_defects(EXCEL_FILE)
    report          = analyze_with_claude(data_text)
    report_file     = save_report(report)
    send_email(report, report_file)

    # Print to console too
    print("\n" + "=" * 60)
    print("  GENERATED REPORT")
    print("=" * 60)
    print(report)
    print("\n✅ Done! Check the output/ folder for the saved report.")


if __name__ == "__main__":
    main()
