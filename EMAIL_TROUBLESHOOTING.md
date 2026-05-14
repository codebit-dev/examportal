# Email Troubleshooting Guide

## Quick Test

1. **Restart your Flask server** (required after .env changes):
   - Stop the server (Ctrl+C)
   - Run: `python app.py`

2. **Check email configuration**:
   - Visit: `http://127.0.0.1:5000/test-email`
   - You should see your email settings
   - If `MAIL_PASSWORD_SET` is `false`, your .env file isn't loading

3. **Test sending an exam**:
   - Complete an exam (both MCQ and Coding sections)
   - Submit the exam
   - Check the Flask terminal for `[EMAIL]` logs

## Common Issues

### Issue 1: "MAIL_USERNAME is empty"
**Solution**: Your `.env` file isn't being loaded
- Make sure `.env` file is in the same folder as `app.py`
- Check that python-dotenv is installed: `pip install python-dotenv`
- Restart Flask server after creating/editing .env

### Issue 2: "Connection refused" or "Timeout"
**Solution**: Gmail is blocking the connection
- You MUST use an App Password, not your regular Gmail password
- Generate App Password: https://myaccount.google.com/apppasswords
- Requirements:
  - 2-Step Verification must be enabled
  - Use 16-character app password (no spaces)

### Issue 3: "Authentication failed"
**Solution**: Wrong password or app password expired
- Regenerate App Password from Google
- Update `.env` file with new password
- Restart Flask server

### Issue 4: Email sent but never received
**Solution**: Check spam folder or email was already sent
- Each attempt only sends email ONCE (tracked by `email_sent` flag)
- Check your Spam/Junk folder
- Check Flask terminal for `[EMAIL] ✓ Email sent successfully`

## Your Current Configuration

Based on your `.env` file:
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=devdeepcoc2005@gmail.com
MAIL_PASSWORD=zpsmcbdryylenonj
MAIL_DEFAULT_SENDER=devdeepcoc2005@gmail.com
```

✅ Configuration looks correct!

## Steps to Test Now

1. **Restart Flask server**:
   ```powershell
   # Stop current server (Ctrl+C)
   cd C:\Users\DEVDE\OneDrive\Desktop\examportal
   python app.py
   ```

2. **Visit test endpoint**:
   ```
   http://127.0.0.1:5000/test-email
   ```

3. **Take a test exam**:
   - Join an exam as a student
   - Complete MCQ section
   - Complete Coding section  
   - Submit exam
   - Check terminal for `[EMAIL]` logs

4. **If still not working**, share the terminal output showing the `[EMAIL]` logs

## Reset Email Status for Testing

If you want to resend email for a previous attempt:
```python
python -c "
from app import db, app, Attempt
with app.app_context():
    attempt = Attempt.query.get(YOUR_ATTEMPT_ID)
    attempt.email_sent = False
    db.session.commit()
    print(f'Reset email_sent for attempt {attempt.id}')
"
```
