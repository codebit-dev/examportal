# Email Configuration Guide

## Setting Up Email for Exam Results

The exam portal can automatically send result emails to students after they complete an exam.

### For Gmail Users (Recommended)

1. **Enable 2-Step Verification** on your Google Account
   - Go to: https://myaccount.google.com/security
   - Enable 2-Step Verification if not already enabled

2. **Generate an App Password**
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" and your device
   - Click "Generate"
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

3. **Configure the Application**
   
   Create a `.env` file in the project root:
   ```env
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=abcdefghijklmnop  # Remove spaces from app password
   MAIL_DEFAULT_SENDER=your_email@gmail.com
   ```

### For Outlook/Hotmail Users

```env
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@outlook.com
MAIL_PASSWORD=your_password
MAIL_DEFAULT_SENDER=your_email@outlook.com
```

### For Yahoo Mail Users

```env
MAIL_SERVER=smtp.mail.yahoo.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your_email@yahoo.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=your_email@yahoo.com
```

## Testing Email Configuration

After configuring, the application will:
- Log email sending attempts to the console
- Show detailed error messages if email fails
- Mark emails as sent in the database

Check the terminal output for messages like:
- `Sending email to student@example.com for exam: Python Test`
- `Email sent successfully to student@example.com`
- `Email error: [error details]`

## Troubleshooting

### Common Issues

1. **"Email not configured: MAIL_USERNAME is empty"**
   - Make sure `.env` file exists and has `MAIL_USERNAME` set
   - Restart the Flask application after creating `.env`

2. **Authentication Error**
   - For Gmail: Use App Password, not your regular password
   - Check if 2-Step Verification is enabled
   - Verify the app password has no spaces

3. **Connection Timeout**
   - Check your internet connection
   - Verify the MAIL_SERVER and MAIL_PORT are correct
   - Some networks block SMTP ports

4. **Email not sending but no error**
   - Check terminal logs for detailed messages
   - Verify `email_sent` field is False in database
   - Students can only receive email once per attempt

## Security Notes

- Never commit `.env` file to version control
- Use `.env.example` as a template
- App passwords are more secure than regular passwords
- Rotate app passwords periodically
