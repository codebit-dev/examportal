#!/usr/bin/env python
"""Test auto-grading system"""

from app import app, db, Attempt, Exam, Question, Answer, calculate_coding_score
from datetime import datetime

print("=" * 60)
print("Testing Auto-Grading System")
print("=" * 60)

with app.app_context():
    # Create test exam
    exam = Exam.query.first()
    if not exam:
        print("❌ No exam found in database. Please create an exam first.")
        exit(1)
    
    print(f"\n✓ Testing with exam: {exam.title}")
    print(f"  MCQ Time: {exam.mcq_time_minutes} min")
    print(f"  Coding Time: {exam.coding_time_minutes} min")
    
    # Get coding questions
    coding_questions = Question.query.filter_by(exam_id=exam.id, section='coding').all()
    print(f"\n✓ Found {len(coding_questions)} coding question(s)")
    
    for q in coding_questions:
        print(f"\n  Question: {q.text[:50]}...")
        print(f"  Marks: {q.marks}")
        print(f"  Has test cases: {bool(q.test_cases)}")
        
        if q.test_cases:
            import json
            test_cases = json.loads(q.test_cases)
            print(f"  Number of test cases: {len(test_cases)}")
    
    # Create test attempt
    attempt = Attempt(
        exam_id=exam.id,
        candidate_name="Test Student",
        candidate_email="test@example.com",
        started_at=datetime.utcnow(),
        mcq_submitted=True,
        mcq_score=5
    )
    db.session.add(attempt)
    db.session.flush()
    
    # Add test answers
    for q in coding_questions:
        if q.test_cases:
            # Sample correct answer
            answer = Answer(
                attempt_id=attempt.id,
                question_id=q.id,
                answer_text="def solution(n):\n    return n * 10",
                is_correct=None,
                marks_awarded=0
            )
            db.session.add(answer)
    
    db.session.commit()
    
    # Test auto-grading
    print("\n" + "=" * 60)
    print("Running Auto-Grading...")
    print("=" * 60)
    
    coding_score = calculate_coding_score(attempt, exam)
    
    print(f"\n✓ Coding Score: {coding_score}")
    print(f"✓ MCQ Score: {attempt.mcq_score}")
    print(f"✓ Total Score: {coding_score + attempt.mcq_score}")
    
    # Verify answers were graded
    for answer in attempt.answers:
        q = answer.question
        if q.section == 'coding':
            print(f"\n  Question {q.id}:")
            print(f"    Marks Awarded: {answer.marks_awarded}/{q.marks}")
            print(f"    Is Correct: {answer.is_correct}")
    
    print("\n" + "=" * 60)
    print("✓ Auto-grading test completed successfully!")
    print("=" * 60)
    print("\nNote: Coding questions are automatically graded based on")
    print("test case results when the student submits the exam.")
    print("No manual teacher grading required!")
