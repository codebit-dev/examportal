from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from datetime import timezone
import json
import secrets
import os
import requests
import threading
from code_executor import CodeExecutor

# Indian Standard Time (IST) - UTC+5:30
IST_OFFSET = timedelta(hours=5, minutes=30)

def now_ist():
    """Get current time in Indian Standard Time (timezone-naive for DB compatibility)"""
    return datetime.utcnow() + IST_OFFSET

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, using system environment variables

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///examportal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration - extended timeout for exams
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)  # 8 hour session timeout
app.config['SESSION_COOKIE_SECURE'] = False  # Set True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Mail config — update with real SMTP credentials
# For Gmail: Use App Password (not regular password)
# Generate at: https://myaccount.google.com/apppasswords
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])

db = SQLAlchemy(app)
mail = Mail(app)

# ─── MODELS ──────────────────────────────────────────────────────────────────

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    exams = db.relationship('Exam', backref='teacher', lazy=True)

class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    security_key = db.Column(db.String(20), unique=True, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    total_time_minutes = db.Column(db.Integer, default=60)
    mcq_enabled = db.Column(db.Boolean, default=True)
    coding_enabled = db.Column(db.Boolean, default=True)
    mcq_time_minutes = db.Column(db.Integer, default=30)
    coding_time_minutes = db.Column(db.Integer, default=30)
    is_active = db.Column(db.Boolean, default=True)
    allowed_emails = db.Column(db.Text)  # Comma-separated list of allowed emails (empty = anyone)
    created_at = db.Column(db.DateTime, default=now_ist)
    questions = db.relationship('Question', backref='exam', lazy=True, cascade='all, delete-orphan')
    attempts = db.relationship('Attempt', backref='exam', lazy=True, cascade='all, delete-orphan')

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    section = db.Column(db.String(10), nullable=False)  # 'mcq' or 'coding'
    order_num = db.Column(db.Integer, default=0)
    text = db.Column(db.Text, nullable=False)
    marks = db.Column(db.Integer, default=1)
    # MCQ fields
    option_a = db.Column(db.String(500))
    option_b = db.Column(db.String(500))
    option_c = db.Column(db.String(500))
    option_d = db.Column(db.String(500))
    correct_option = db.Column(db.String(1))  # 'a','b','c','d'
    # Coding fields
    expected_output = db.Column(db.Text)
    language_hint = db.Column(db.String(50))
    starter_code = db.Column(db.Text)  # Starter code template
    test_cases = db.Column(db.Text)  # JSON array of test cases: [{"input": "...", "output": "..."}]

class Attempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exam.id'), nullable=False)
    candidate_name = db.Column(db.String(100), nullable=False)
    candidate_email = db.Column(db.String(150), nullable=False)
    started_at = db.Column(db.DateTime, default=now_ist)
    submitted_at = db.Column(db.DateTime)
    mcq_submitted = db.Column(db.Boolean, default=False)
    mcq_started_at = db.Column(db.DateTime)
    mcq_score = db.Column(db.Integer, default=0)
    coding_submitted = db.Column(db.Boolean, default=False)
    coding_started_at = db.Column(db.DateTime)
    coding_score = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Integer, default=0)
    max_score = db.Column(db.Integer, default=0)
    answers = db.relationship('Answer', backref='attempt', lazy=True, cascade='all, delete-orphan')
    email_sent = db.Column(db.Boolean, default=False)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('attempt.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answer_text = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    marks_awarded = db.Column(db.Integer, default=0)
    question = db.relationship('Question')

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def send_result_email(attempt_id):
    """Send exam results via Brevo API"""
    try:
        with app.app_context():
            attempt = Attempt.query.get(attempt_id)

            if not attempt or attempt.email_sent:
                print(f"[EMAIL] Not sent: attempt={attempt_id}")
                return

            exam = Exam.query.get(attempt.exam_id)

            print(f"[EMAIL] Sending email to {attempt.candidate_email}")

            html_content = render_template(
                'email_result.html',
                attempt=attempt,
                exam=exam
            )

            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "accept": "application/json",
                    "api-key": os.getenv("BREVO_API_KEY"),
                    "content-type": "application/json"
                },
                json={
                    "sender": {
                        "name": "Examforge",
                        "email": "devdeepcoc2005@gmail.com"
                    },
                    "to": [
                        {
                            "email": attempt.candidate_email
                        }
                    ],
                    "subject": f"Your Results: {exam.title}",
                    "htmlContent": html_content
                }
            )

            print("[EMAIL] Response:", response.text)

            if response.status_code not in [200, 201]:
                raise Exception(response.text)

            attempt.email_sent = True
            db.session.commit()

            print(f"[EMAIL] ✓ Email sent successfully")

    except Exception as e:
        print(f"[EMAIL] ✗ Error: {e}")

        import traceback
        traceback.print_exc()
def calculate_mcq_score(attempt):
    score = 0
    for answer in attempt.answers:
        q = answer.question
        if q.section == 'mcq':
            correct = answer.answer_text and answer.answer_text.lower() == q.correct_option.lower()
            answer.is_correct = correct
            answer.marks_awarded = q.marks if correct else 0
            score += answer.marks_awarded
    return score

def calculate_coding_score(attempt, exam):
    """Auto-grade coding questions based on test case results"""
    print(f"  [GRADE] Starting grading for attempt {attempt.id}")
    coding_questions = Question.query.filter_by(exam_id=exam.id, section='coding').all()
    print(f"  [GRADE] Found {len(coding_questions)} coding question(s)")
    total_score = 0
    
    for idx, question in enumerate(coding_questions):
        print(f"  [GRADE] Processing question {idx+1}/{len(coding_questions)} (id={question.id})")
        
        if not question.test_cases:
            print(f"  [GRADE]   Skipping - no test cases")
            continue
        
        # Find student's answer for this question
        answer = Answer.query.filter_by(
            attempt_id=attempt.id,
            question_id=question.id
        ).first()
        
        if not answer or not answer.answer_text:
            print(f"  [GRADE]   Skipping - no answer submitted")
            continue
        
        print(f"  [GRADE]   Answer length: {len(answer.answer_text)} chars")
        
        # Parse test cases
        try:
            test_cases = json.loads(question.test_cases)
            print(f"  [GRADE]   Loaded {len(test_cases)} test case(s)")
        except Exception as e:
            print(f"  [GRADE]   ERROR parsing test cases: {e}")
            continue
        
        if not test_cases:
            print(f"  [GRADE]   Skipping - empty test cases")
            continue
        
        # Run code against test cases
        print(f"  [GRADE]   Running test cases...")
        try:
            results = CodeExecutor.run_test_cases('python', answer.answer_text, test_cases)
            print(f"  [GRADE]   Test execution complete")
        except Exception as e:
            print(f"  [GRADE]   ERROR running tests: {e}")
            import traceback
            traceback.print_exc()
            results = []
        
        # Calculate score based on passed test cases
        passed_count = sum(1 for r in results if r['passed'])
        total_count = len(results)
        
        print(f"  [GRADE]   Results: {passed_count}/{total_count} passed")
        
        if total_count > 0:
            # Marks proportional to test cases passed
            marks_earned = (passed_count / total_count) * question.marks
            answer.marks_awarded = round(marks_earned, 2)
            answer.is_correct = (passed_count == total_count)  # True only if all pass
            total_score += marks_earned
            db.session.add(answer)
            print(f"  [GRADE]   Marks awarded: {marks_earned}/{question.marks}")
    
    print(f"  [GRADE] Total score: {total_score}")
    return round(total_score, 2)

def get_max_score(exam):
    return sum(q.marks for q in exam.questions)

# ─── AUTH ROUTES ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/teacher/register', methods=['GET', 'POST'])
def teacher_register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not name or not email or not password:
            flash('All fields required.', 'error')
            return render_template('teacher_register.html')
        if Teacher.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('teacher_register.html')
        teacher = Teacher(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(teacher)
        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('teacher_login'))
    return render_template('teacher_register.html')

@app.route('/teacher/login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        teacher = Teacher.query.filter_by(email=email).first()
        if teacher and check_password_hash(teacher.password_hash, password):
            session['teacher_id'] = teacher.id
            session['teacher_name'] = teacher.name
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('teacher_login.html')

@app.route("/ping")
def ping():
    return "OK", 200

@app.route('/teacher/logout')
def teacher_logout():
    session.clear()
    return redirect(url_for('index'))

def teacher_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'teacher_id' not in session:
            return redirect(url_for('teacher_login'))
        return f(*args, **kwargs)
    return decorated

# ─── TEACHER DASHBOARD ───────────────────────────────────────────────────────

@app.route('/dashboard')
@teacher_required
def dashboard():
    teacher = Teacher.query.get(session['teacher_id'])
    exams = Exam.query.filter_by(teacher_id=teacher.id).order_by(Exam.created_at.desc()).all()
    exam_stats = []
    for exam in exams:
        attempts = Attempt.query.filter_by(exam_id=exam.id).all()
        submitted = [a for a in attempts if a.submitted_at]
        exam_stats.append({
            'exam': exam,
            'total_attempts': len(attempts),
            'submitted': len(submitted),
            'avg_score': round(sum(a.total_score for a in submitted) / len(submitted), 1) if submitted else 0,
            'max_score': get_max_score(exam)
        })
    return render_template('dashboard.html', teacher=teacher, exam_stats=exam_stats)

# ─── EXAM CREATION ───────────────────────────────────────────────────────────

@app.route('/exam/create', methods=['GET', 'POST'])
@teacher_required
def create_exam():
    if request.method == 'POST':
        data = request.get_json()
        key = secrets.token_hex(4).upper()
        while Exam.query.filter_by(security_key=key).first():
            key = secrets.token_hex(4).upper()

        exam = Exam(
            title=data['title'],
            security_key=key,
            teacher_id=session['teacher_id'],
            total_time_minutes=int(data.get('total_time', 60)),
            mcq_enabled=data.get('mcq_enabled', True),
            coding_enabled=data.get('coding_enabled', True),
            mcq_time_minutes=int(data.get('mcq_time', 30)),
            coding_time_minutes=int(data.get('coding_time', 30)),
            allowed_emails=data.get('allowed_emails', '').strip(),
        )
        db.session.add(exam)
        db.session.flush()

        for i, q in enumerate(data.get('mcq_questions', [])):
            question = Question(
                exam_id=exam.id,
                section='mcq',
                order_num=i,
                text=q['text'],
                marks=int(q.get('marks', 1)),
                option_a=q.get('option_a', ''),
                option_b=q.get('option_b', ''),
                option_c=q.get('option_c', ''),
                option_d=q.get('option_d', ''),
                correct_option=q.get('correct', 'a'),
            )
            db.session.add(question)

        for i, q in enumerate(data.get('coding_questions', [])):
            question = Question(
                exam_id=exam.id,
                section='coding',
                order_num=i,
                text=q['text'],
                marks=int(q.get('marks', 10)),
                expected_output=q.get('expected_output', ''),
                language_hint=q.get('language_hint', 'python'),
                starter_code=q.get('starter_code', ''),
                test_cases=q.get('test_cases', ''),
            )
            db.session.add(question)

        db.session.commit()
        return jsonify({'success': True, 'key': key, 'exam_id': exam.id})

    return render_template('create_exam.html')

@app.route('/exam/<int:exam_id>/edit', methods=['GET', 'POST'])
@teacher_required
def edit_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if exam.teacher_id != session['teacher_id']:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json()
        exam.title = data['title']
        exam.total_time_minutes = int(data.get('total_time', 60))
        exam.mcq_enabled = data.get('mcq_enabled', True)
        exam.coding_enabled = data.get('coding_enabled', True)
        exam.mcq_time_minutes = int(data.get('mcq_time', 30))
        exam.coding_time_minutes = int(data.get('coding_time', 30))
        exam.is_active = data.get('is_active', True)
        exam.allowed_emails = data.get('allowed_emails', '').strip()

        # Remove old questions and re-add
        Question.query.filter_by(exam_id=exam.id).delete()

        for i, q in enumerate(data.get('mcq_questions', [])):
            question = Question(
                exam_id=exam.id, section='mcq', order_num=i,
                text=q['text'], marks=int(q.get('marks', 1)),
                option_a=q.get('option_a', ''), option_b=q.get('option_b', ''),
                option_c=q.get('option_c', ''), option_d=q.get('option_d', ''),
                correct_option=q.get('correct', 'a'),
            )
            db.session.add(question)

        for i, q in enumerate(data.get('coding_questions', [])):
            question = Question(
                exam_id=exam.id, section='coding', order_num=i,
                text=q['text'], marks=int(q.get('marks', 10)),
                expected_output=q.get('expected_output', ''),
                language_hint=q.get('language_hint', 'python'),
                starter_code=q.get('starter_code', ''),
                test_cases=q.get('test_cases', ''),
            )
            db.session.add(question)

        db.session.commit()
        return jsonify({'success': True})

    mcq_qs = Question.query.filter_by(exam_id=exam.id, section='mcq').order_by(Question.order_num).all()
    coding_qs = Question.query.filter_by(exam_id=exam.id, section='coding').order_by(Question.order_num).all()
    return render_template('create_exam.html', exam=exam, mcq_qs=mcq_qs, coding_qs=coding_qs)

@app.route('/exam/<int:exam_id>/toggle', methods=['POST'])
@teacher_required
def toggle_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if exam.teacher_id != session['teacher_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    exam.is_active = not exam.is_active
    db.session.commit()
    return jsonify({'active': exam.is_active})

@app.route('/exam/<int:exam_id>/delete', methods=['POST'])
@teacher_required
def delete_exam(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if exam.teacher_id != session['teacher_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    db.session.delete(exam)
    db.session.commit()
    return jsonify({'success': True})

# ─── RESULTS VIEW ─────────────────────────────────────────────────────────────

@app.route('/exam/<int:exam_id>/results')
@teacher_required
def exam_results(exam_id):
    exam = Exam.query.get_or_404(exam_id)
    if exam.teacher_id != session['teacher_id']:
        return redirect(url_for('dashboard'))
    attempts = Attempt.query.filter_by(exam_id=exam_id).order_by(Attempt.submitted_at.desc()).all()
    max_score = get_max_score(exam)
    return render_template('exam_results.html', exam=exam, attempts=attempts, max_score=max_score)

@app.route('/attempt/<int:attempt_id>/detail')
@teacher_required
def attempt_detail(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    exam = Exam.query.get(attempt.exam_id)
    if exam.teacher_id != session['teacher_id']:
        return redirect(url_for('dashboard'))
    answers = Answer.query.filter_by(attempt_id=attempt_id).all()
    return render_template('attempt_detail.html', attempt=attempt, exam=exam, answers=answers)

@app.route('/attempt/<int:attempt_id>/score', methods=['POST'])
@teacher_required
def update_coding_score(attempt_id):
    attempt = Attempt.query.get_or_404(attempt_id)
    exam = Exam.query.get(attempt.exam_id)
    if exam.teacher_id != session['teacher_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    for answer_id, marks in data.get('scores', {}).items():
        answer = Answer.query.get(int(answer_id))
        if answer and answer.attempt_id == attempt_id:
            answer.marks_awarded = int(marks)
            answer.is_correct = int(marks) > 0
    db.session.flush()
    attempt.coding_score = sum(
        a.marks_awarded for a in attempt.answers if a.question.section == 'coding'
    )
    attempt.total_score = attempt.mcq_score + attempt.coding_score
    db.session.commit()
    return jsonify({'success': True, 'total': attempt.total_score})

# ─── STUDENT ROUTES ──────────────────────────────────────────────────────────

@app.route('/join', methods=['GET', 'POST'])
def join_exam():
    if request.method == 'POST':
        key = request.form.get('security_key', '').strip().upper()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()

        if not key or not name or not email:
            flash('All fields are required.', 'error')
            return render_template('join_exam.html')

        exam = Exam.query.filter_by(security_key=key, is_active=True).first()
        if not exam:
            flash('Invalid or inactive exam key.', 'error')
            return render_template('join_exam.html')

        # Check if email is in allowed list (if set)
        if exam.allowed_emails and exam.allowed_emails.strip():
            allowed_list = [e.strip().lower() for e in exam.allowed_emails.split(',')]
            if email not in allowed_list:
                flash('Your email is not authorized to take this exam. Contact your teacher.', 'error')
                return render_template('join_exam.html')

        # Check if student already attempted this exam
        existing_attempt = Attempt.query.filter_by(
            exam_id=exam.id,
            candidate_email=email,
            submitted_at=db.session.query(db.func.max(Attempt.submitted_at)).filter_by(exam_id=exam.id).scalar_subquery()
        ).first()
        
        # Simpler check - any submitted attempt
        existing_attempt = Attempt.query.filter_by(
            exam_id=exam.id,
            candidate_email=email
        ).filter(Attempt.submitted_at.isnot(None)).first()
        
        if existing_attempt:
            flash(f'You have already completed this exam on {existing_attempt.submitted_at.strftime("%Y-%m-%d %H:%M")}. You cannot attempt it again.', 'error')
            return render_template('join_exam.html')

        # Check for in-progress attempt
        in_progress = Attempt.query.filter_by(
            exam_id=exam.id,
            candidate_email=email,
            submitted_at=None
        ).first()
        
        if in_progress:
            # Resume existing attempt
            session['attempt_id'] = in_progress.id
            session['exam_id'] = exam.id
            session['exam_start'] = in_progress.started_at.isoformat()
            session.permanent = True  # Make session permanent with extended lifetime
            
            if exam.mcq_enabled and not in_progress.mcq_submitted:
                return redirect(url_for('exam_mcq'))
            elif exam.coding_enabled:
                return redirect(url_for('exam_coding'))
            else:
                flash('Exam sections are not available.', 'error')
                return render_template('join_exam.html')

        # Create new attempt
        attempt = Attempt(exam_id=exam.id, candidate_name=name, candidate_email=email)
        db.session.add(attempt)
        db.session.commit()

        session['attempt_id'] = attempt.id
        session['exam_id'] = exam.id
        session['exam_start'] = now_ist().isoformat()
        session.permanent = True  # Make session permanent with extended lifetime

        # Redirect to instructions page first
        return redirect(url_for('exam_instructions'))

    prefill_key = request.args.get('key', '')
    return render_template('join_exam.html', prefill_key=prefill_key)

@app.route('/exam/instructions')
def exam_instructions():
    """Show exam instructions before starting"""
    if 'attempt_id' not in session:
        return redirect(url_for('join_exam'))
    
    attempt = Attempt.query.get(session['attempt_id'])
    exam = Exam.query.get(session['exam_id'])
    
    return render_template('exam_instructions.html', exam=exam, attempt=attempt)

@app.route('/exam/mcq', methods=['GET', 'POST'])
def exam_mcq():
    if 'attempt_id' not in session:
        return redirect(url_for('join_exam'))

    attempt = Attempt.query.get(session['attempt_id'])
    exam = Exam.query.get(session['exam_id'])

    if not exam.mcq_enabled:
        return redirect(url_for('exam_coding'))

    if attempt.mcq_submitted:
        if exam.coding_enabled:
            return redirect(url_for('exam_coding'))
        return redirect(url_for('exam_done'))

    # Initialize MCQ section start time
    if not attempt.mcq_started_at:
        attempt.mcq_started_at = now_ist()
        db.session.commit()
    
    # Check if MCQ time has expired
    elapsed = now_ist() - attempt.mcq_started_at
    time_limit_minutes = exam.mcq_time_minutes if exam.mcq_enabled else exam.total_time_minutes
    if elapsed.total_seconds() >= time_limit_minutes * 60:
        # Time expired - auto submit with empty answers
        print(f"[MCQ] Time expired for attempt {attempt.id}, auto-submitting")
        return auto_submit_mcq(attempt, exam)

    questions = Question.query.filter_by(exam_id=exam.id, section='mcq').order_by(Question.order_num).all()

    if request.method == 'POST':
        data = request.get_json()
        # Check if this is an auto-submit (time expired)
        is_auto_submit = data.get('auto_submit', False)
        
        # Save answers
        Answer.query.filter(
            Answer.attempt_id == attempt.id,
            Answer.question_id.in_([q.id for q in questions])
        ).delete(synchronize_session=False)

        for q in questions:
            ans_text = data.get(str(q.id), '')
            correct = ans_text.lower() == q.correct_option.lower() if ans_text else False
            answer = Answer(
                attempt_id=attempt.id,
                question_id=q.id,
                answer_text=ans_text,
                is_correct=correct,
                marks_awarded=q.marks if correct else 0
            )
            db.session.add(answer)

        attempt.mcq_score = sum(
            q.marks for q in questions
            if data.get(str(q.id), '').lower() == q.correct_option.lower()
        )
        attempt.mcq_submitted = True
        db.session.commit()
        
        print(f"[MCQ] Submitted for attempt {attempt.id}, score: {attempt.mcq_score}")

        if exam.coding_enabled:
            return jsonify({'redirect': url_for('exam_coding')})
        else:
            # No coding section, submit entire exam
            attempt.submitted_at = now_ist()
            attempt.total_score = attempt.mcq_score
            attempt.max_score = get_max_score(exam)
            db.session.commit()
            send_result_email(attempt.id)
            return jsonify({'redirect': url_for('exam_done')})

    return render_template('exam_mcq.html', exam=exam, questions=questions, attempt=attempt)

def auto_submit_mcq(attempt, exam):
    """Auto-submit MCQ section when time expires"""
    questions = Question.query.filter_by(exam_id=exam.id, section='mcq').order_by(Question.order_num).all()
    
    # Save empty answers for unanswered questions
    for q in questions:
        existing = Answer.query.filter_by(
            attempt_id=attempt.id,
            question_id=q.id
        ).first()
        if not existing:
            answer = Answer(
                attempt_id=attempt.id,
                question_id=q.id,
                answer_text='',
                is_correct=False,
                marks_awarded=0
            )
            db.session.add(answer)
    
    attempt.mcq_score = 0
    attempt.mcq_submitted = True
    db.session.commit()
    
    print(f"[MCQ] Auto-submitted, score: 0")
    
    if exam.coding_enabled:
        return redirect(url_for('exam_coding'))
    else:
        attempt.submitted_at = now_ist()
        attempt.total_score = 0
        attempt.max_score = get_max_score(exam)
        db.session.commit()
        send_result_email(attempt.id)
        return redirect(url_for('exam_done'))

@app.route('/exam/coding', methods=['GET', 'POST'])
def exam_coding():
    if 'attempt_id' not in session:
        return redirect(url_for('join_exam'))

    attempt = Attempt.query.get(session['attempt_id'])
    exam = Exam.query.get(session['exam_id'])

    if exam.mcq_enabled and not attempt.mcq_submitted:
        return redirect(url_for('exam_mcq'))

    if not exam.coding_enabled:
        return redirect(url_for('exam_done'))
    
    if attempt.coding_submitted:
        return redirect(url_for('exam_done'))

    # Initialize Coding section start time
    if not attempt.coding_started_at:
        attempt.coding_started_at = now_ist()
        db.session.commit()
    
    # Check if Coding time has expired
    elapsed = now_ist() - attempt.coding_started_at
    time_limit_minutes = exam.coding_time_minutes
    if elapsed.total_seconds() >= time_limit_minutes * 60:
        # Time expired - auto submit
        print(f"[CODING] Time expired for attempt {attempt.id}, auto-submitting")
        return auto_submit_coding(attempt, exam, {})

    questions = Question.query.filter_by(exam_id=exam.id, section='coding').order_by(Question.order_num).all()

    if request.method == 'POST':
        data = request.get_json()
        
        try:
            # Save answers
            Answer.query.filter(
                Answer.attempt_id == attempt.id,
                Answer.question_id.in_([q.id for q in questions])
            ).delete(synchronize_session=False)

            for q in questions:
                answer = Answer(
                    attempt_id=attempt.id,
                    question_id=q.id,
                    answer_text=data.get(str(q.id), ''),
                    is_correct=None,
                    marks_awarded=0
                )
                db.session.add(answer)
            
            db.session.commit()
            
            # Auto-grade coding questions based on test cases
            print(f"[CODING] Auto-grading coding questions for attempt {attempt.id}")
            try:
                attempt.coding_score = calculate_coding_score(attempt, exam)
                print(f"[CODING] Grading complete, score: {attempt.coding_score}")
            except Exception as grading_error:
                print(f"[CODING] ERROR during grading: {grading_error}")
                import traceback
                traceback.print_exc()
                attempt.coding_score = 0  # Default to 0 if grading fails
            
            attempt.coding_submitted = True
            db.session.commit()
            
            print(f"[CODING] Submitted for attempt {attempt.id}, score: {attempt.coding_score}")

            # Submit entire exam
            attempt.submitted_at = now_ist()
            attempt.total_score = attempt.mcq_score + attempt.coding_score
            attempt.max_score = get_max_score(exam)
            db.session.commit()
            
            print(f"[EXAM] Final score: {attempt.total_score}/{attempt.max_score}")
            
            send_result_email(attempt.id)
            session.pop('attempt_id', None)
            session.pop('exam_id', None)
            session.pop('exam_start', None)
            return jsonify({'redirect': url_for('exam_done')})
            
        except Exception as e:
            print(f"[CODING] ERROR in submission: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    return render_template('exam_coding.html', exam=exam, questions=questions, attempt=attempt)

def auto_submit_coding(attempt, exam, data):
    """Auto-submit coding section when time expires"""
    questions = Question.query.filter_by(exam_id=exam.id, section='coding').order_by(Question.order_num).all()
    
    # Save empty answers for unanswered questions
    for q in questions:
        existing = Answer.query.filter_by(
            attempt_id=attempt.id,
            question_id=q.id
        ).first()
        if not existing:
            answer = Answer(
                attempt_id=attempt.id,
                question_id=q.id,
                answer_text='',
                is_correct=None,
                marks_awarded=0
            )
            db.session.add(answer)
    
    db.session.commit()
    
    # Auto-grade (will give 0 for empty answers)
    print(f"[CODING] Auto-submitting and grading for attempt {attempt.id}")
    attempt.coding_score = calculate_coding_score(attempt, exam)
    attempt.coding_submitted = True
    db.session.commit()
    
    print(f"[CODING] Auto-submitted, score: {attempt.coding_score}")
    
    # Submit entire exam
    attempt.submitted_at = now_ist()
    attempt.total_score = attempt.mcq_score + attempt.coding_score
    attempt.max_score = get_max_score(exam)
    db.session.commit()
    
    print(f"[EXAM] Final score (auto-submit): {attempt.total_score}/{attempt.max_score}")
    
    send_result_email(attempt.id)
    session.pop('attempt_id', None)
    session.pop('exam_id', None)
    session.pop('exam_start', None)
    return redirect(url_for('exam_done'))

@app.route('/exam/done')
def exam_done():
    return render_template('exam_done.html')

@app.route('/test-email')
def test_email_config():
    """Test email configuration"""
    mail_server = app.config.get('MAIL_SERVER', '(not set)')
    mail_port = app.config.get('MAIL_PORT', '(not set)')
    mail_tls = app.config.get('MAIL_USE_TLS', '(not set)')
    mail_username = app.config.get('MAIL_USERNAME', '(not set)')
    mail_password = app.config.get('MAIL_PASSWORD', '(not set)')
    
    return jsonify({
        'MAIL_SERVER': mail_server,
        'MAIL_PORT': mail_port,
        'MAIL_USE_TLS': mail_tls,
        'MAIL_USERNAME': mail_username,
        'MAIL_PASSWORD_SET': bool(mail_password and mail_password != '(not set)'),
        'dotenv_loaded': bool(os.environ.get('MAIL_USERNAME'))
    })

@app.route('/exam/save-mcq-progress', methods=['POST'])
def save_mcq_progress():
    if 'attempt_id' not in session:
        return jsonify({'error': 'No active session'}), 401
    # Just acknowledge — actual save on submit
    return jsonify({'ok': True})

@app.route('/exam/heartbeat', methods=['POST'])
def exam_heartbeat():
    """Keep session alive during exam and return time remaining"""
    if 'attempt_id' not in session:
        return jsonify({'error': 'No active session'}), 401
    
    # Refresh session lifetime
    session.permanent = True
    
    # Get time remaining for current section
    attempt = Attempt.query.get(session['attempt_id'])
    exam = Exam.query.get(session['exam_id'])
    
    time_remaining = None
    current_section = None
    
    if exam.mcq_enabled and not attempt.mcq_submitted:
        current_section = 'mcq'
        if attempt.mcq_started_at:
            elapsed = now_ist() - attempt.mcq_started_at
            time_limit_seconds = exam.mcq_time_minutes * 60
            remaining = time_limit_seconds - elapsed.total_seconds()
            time_remaining = max(0, int(remaining))
    elif exam.coding_enabled and not attempt.coding_submitted:
        current_section = 'coding'
        if attempt.coding_started_at:
            elapsed = now_ist() - attempt.coding_started_at
            time_limit_seconds = exam.coding_time_minutes * 60
            remaining = time_limit_seconds - elapsed.total_seconds()
            time_remaining = max(0, int(remaining))
    
    return jsonify({
        'ok': True,
        'message': 'Session refreshed',
        'current_section': current_section,
        'time_remaining': time_remaining
    })

@app.route('/exam/run-code', methods=['POST'])
def run_code():
    """Run code against test cases"""
    if 'attempt_id' not in session:
        return jsonify({'error': 'No active session'}), 401
    
    data = request.get_json()
    question_id = data.get('question_id')
    code = data.get('code', '')
    language = data.get('language', 'python')
    
    if not question_id or not code:
        return jsonify({'error': 'Missing question_id or code'}), 400
    
    # Get question from database
    question = Question.query.get(question_id)
    if not question:
        return jsonify({'error': 'Question not found'}), 404
    
    # Parse test cases
    test_cases = []
    if question.test_cases:
        try:
            test_cases = json.loads(question.test_cases)
        except:
            return jsonify({'error': 'Invalid test cases format'}), 500
    
    if not test_cases:
        return jsonify({'error': 'No test cases available'}), 400
    
    # Run code against test cases
    results = CodeExecutor.run_test_cases(language, code, test_cases)
    
    # Calculate score
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    score_percentage = (passed_count / total_count * 100) if total_count > 0 else 0
    
    return jsonify({
        'results': results,
        'passed': passed_count,
        'total': total_count,
        'score_percentage': score_percentage
    })

# ─── INIT ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))

    app.run(host='0.0.0.0', port=port)
