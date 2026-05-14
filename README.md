# ExamForge — Exam Portal

A full-featured Flask exam portal with MCQ + Coding sections, timed tests, security keys, and email result delivery.

## Setup

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure email (for result delivery)
# Edit app.py and set your SMTP credentials, OR use environment variables:
export MAIL_USERNAME="your@gmail.com"
export MAIL_PASSWORD="your_app_password"

# For Gmail, you need an App Password (not your regular password):
# Gmail → Security → 2-Step Verification → App Passwords

# 4. Run
python app.py
# Visit: http://localhost:5000
```

## Features

### Teacher
- Register / Login
- Create exams with:
  - Security key (auto-generated 8-char code)
  - Enable/disable MCQ section individually
  - Enable/disable Coding section individually
  - Set total time + per-section time limits
  - Add MCQ questions with 4 options, correct answer, and marks
  - Add Coding problems with language hint and expected output
- Edit existing exams
- Pause/Activate exams
- View all attempts in results dashboard
- Review coding answers and assign marks manually
- MCQ is auto-graded

### Student
- Enter security key + name + email to access exam
- Timed MCQ section with question navigation
- After submitting MCQ → moves to Coding (cannot go back)
- Code editor with syntax highlighting (per language)
- Auto-submit when time expires
- Results emailed after submission (not shown on screen)

## Email Configuration

The system uses Flask-Mail with Gmail SMTP by default.
To use Gmail:
1. Enable 2-Step Verification on your Google account
2. Generate an App Password at myaccount.google.com/apppasswords
3. Set MAIL_USERNAME and MAIL_PASSWORD

For other providers, update MAIL_SERVER and MAIL_PORT in app.py.

## File Structure

```
examportal/
├── app.py                    # Main Flask app
├── requirements.txt
├── README.md
└── templates/
    ├── base.html             # Base layout
    ├── index.html            # Landing page
    ├── teacher_login.html
    ├── teacher_register.html
    ├── dashboard.html        # Teacher dashboard
    ├── create_exam.html      # Exam builder (create + edit)
    ├── exam_results.html     # Results view for teacher
    ├── attempt_detail.html   # Per-student review + coding grading
    ├── join_exam.html        # Student entry page
    ├── exam_mcq.html         # MCQ taking interface
    ├── exam_coding.html      # Coding interface with editor
    ├── exam_done.html        # Submission confirmation
    └── email_result.html     # Email template for results
```
"# examforge" 
