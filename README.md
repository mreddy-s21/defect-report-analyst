# 🐛 Defect Report Analyst — AI-Powered Project Status Reporter

An LLM-powered application that reads an Excel defect tracking sheet, analyzes open bugs and blockers using Claude AI, generates a plain-English stakeholder report, and optionally emails it to your team automatically.

Built as a practical alternative to manual JIRA status emails — drop in your Excel sheet, get a professional report in seconds.

---

## 📌 The Problem It Solves

Engineering teams track defects in spreadsheets or tools like JIRA, but turning that raw data into a clear stakeholder update is manual, time-consuming, and inconsistent. Project managers spend 20–30 minutes every day:

- Counting open vs closed defects
- Identifying which blockers need escalation
- Writing status emails that look different every time
- Missing patterns that only become obvious when you look at the data as a whole

This app automates all of that. It reads your defect Excel sheet, sends it to Claude AI for intelligent analysis, and produces a structured report every time — consistent, fast, and smarter than a simple count.

---

## 🤖 LLM Used and Why

**Model: Claude (Anthropic) — `claude-opus-4-6`**

Claude was chosen over other LLMs for three reasons:

1. **Analytical reasoning** — Claude excels at reading structured tabular data and drawing meaningful conclusions, not just summarizing what's already visible
2. **Instruction following** — the report format (Executive Summary, Key Numbers, Blockers, Trends, Actions, Health Status) is followed consistently across every run
3. **Tone control** — Claude produces reports that are professional and measured, not alarmist — important when sending to non-technical stakeholders

GPT-4 was considered but Anthropic's API offered simpler setup and better consistency on structured output tasks in testing.

---

## 💡 How Prompting, Evaluation, and Iteration Were Handled

### Prompting Strategy

The app uses a **two-part prompt design**:

**System prompt** — defines Claude's persona and output format:
```
You are a senior software engineering analyst who specializes in defect tracking 
and project health reporting. Always format your report with these exact sections:
1. Executive Summary
2. Key Numbers
3. Blockers & Critical Issues
4. Trends & Patterns
5. Recommended Actions
6. Overall Health (🟢 / 🟡 / 🔴)
```

**User prompt** — provides the actual data dynamically:
```
Today's date: [date]
DEFECT DATA: [Excel content as CSV text + pre-computed summaries]
Generate the stakeholder report now.
```

Pre-computing summaries (status counts, severity breakdowns) before sending to the LLM reduces token usage and helps Claude focus on analysis rather than counting.

### Evaluation

Reports were evaluated on:
- **Completeness** — does every section appear?
- **Accuracy** — do the numbers in the report match the Excel data?
- **Usefulness** — would a project manager act on the Recommended Actions?
- **Tone** — is it professional without being generic?

### Iteration

Three prompt iterations were made:

| Version | Problem | Fix |
|---------|---------|-----|
| v1 | Report was too long, buried key info | Added "3-4 sentences max" constraint to Executive Summary |
| v2 | Numbers sometimes didn't match raw data | Added pre-computed summaries to the prompt as ground truth |
| v3 | Recommended Actions were vague ("fix the bugs") | Added "top 3, numbered, specific" instruction |

---

## ⚖️ Tradeoffs and Limitations

| Tradeoff | Detail |
|----------|--------|
| **Column name flexibility** | The app auto-detects Status and Severity columns by keyword matching. If your columns are named differently (e.g. "Bug Type" instead of "Severity"), it still works but pre-computed summaries may be skipped |
| **Excel size** | Very large sheets (1000+ rows) will approach token limits. For large sheets, add a filter upstream to pass only Open/Blocked items to the LLM |
| **LLM cost** | Each report run costs approximately $0.01–0.03 in API credits. At daily frequency this is ~$5–10/year |
| **Email** | Email sending is optional and requires a Gmail App Password. The app works fully without it — reports are always saved locally in `output/` |
| **No memory** | Each run is independent — the LLM does not compare today's report to yesterday's. Trend detection is within-run only |
| **Hallucination risk** | Claude may occasionally interpret ambiguous data differently than expected. Pre-computed summaries mitigate this for counts, but qualitative analysis should be reviewed |

---

## 🚀 How to Run It

### Prerequisites
- Python 3.11+
- An Anthropic API key — get one free at [console.anthropic.com](https://console.anthropic.com)

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR-USERNAME/defect-reporter.git
cd defect-reporter

# 2. Install dependencies
pip install anthropic pandas openpyxl python-dotenv

# 3. Set up your API key
copy .env.example .env        # Windows
# cp .env.example .env        # Mac/Linux

# Edit .env and add your ANTHROPIC_API_KEY

# 4. Add your Excel file
# Place your defects spreadsheet at: data/defects.xlsx
# (A sample file is already included to test with)

# 5. Run the app
python main.py
```

### Expected Excel Format

Your Excel file should have columns like:

| Defect_ID | Title | Status | Severity | Assigned_To | Module | Days_Open |
|-----------|-------|--------|----------|-------------|--------|-----------|
| DEF-001 | Login crash | Open | Blocker | John S | Auth | 3 |

Column names are flexible — the app detects them automatically.

### Sample Output

```
============================================================
  DEFECT REPORT ANALYST — Powered by Claude AI
============================================================

📂 Reading Excel file: data/defects.xlsx
   ✅ Loaded 10 defects, 9 columns

🤖 Sending data to Claude for analysis...
   ✅ Analysis complete

💾 Report saved: output/defect_report_2026-02-27_1430.txt

============================================================
  GENERATED REPORT
============================================================

## Executive Summary
The project currently has 10 open defects across 6 modules, 
with 3 critical blockers requiring immediate attention...

## Overall Health
🔴 At Risk — 3 blockers unresolved with 2 overdue target dates
```

---

## 📁 Project Structure

```
defect-reporter/
├── main.py              # Main application
├── data/
│   └── defects.xlsx     # Your Excel input file (sample included)
├── output/              # Generated reports saved here
├── .env.example         # Template for your API key
├── .env                 # Your actual keys (NOT in GitHub)
├── .gitignore           # Keeps .env out of GitHub
└── README.md
```

---

## 🔒 Security Note

Your API key is stored in `.env` which is listed in `.gitignore`. It will never be uploaded to GitHub. Never paste your API key into code files or share it in chat.

---

## 👩‍💻 Author

**Monica Reddy** — Mainframe Software Engineer | AI/Automation enthusiast  
This project bridges enterprise systems thinking with modern AI tooling — the same pattern used to modernize legacy batch report distribution in financial services environments.
