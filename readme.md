# SatyaMatrix - The Network of Truth

AI-Powered Fact-Checking Assistant with automated email notifications.

## Features

- 🤖 AI-powered fact-checking chatbot
- 📧 Automated email notifications to all users
- 🎨 Beautiful black & white email design
- 💾 MongoDB user storage
- ☁️ Cloudinary file uploads
- 🔒 Secure authentication

## Email System

**Powered by Brevo (SendinBlue)**
- 300 emails/day free
- Sends to all active MongoDB users
- Professional HTML emails with:
  - Title, Author, Date, Time
  - Description
  - Query & Response
  - Black background, white text

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and update:
- MongoDB URI
- Brevo SMTP credentials
- Cloudinary credentials

### 3. Run Server
```bash
python manage.py runserver
```

### 4. Access Application
- Chat: http://localhost:8000/auth/chat/
- Admin: http://localhost:8000/admin/

## Email Configuration

See `BREVO_QUICK_START.md` for Brevo setup instructions.

Current configuration sends emails to **8 MongoDB users** automatically when chatbot responds.

## Documentation

- `BREVO_SETUP.md` - Detailed Brevo configuration
- `BREVO_QUICK_START.md` - Quick setup guide
- `EMAIL_FORMAT_UPDATED.md` - Email template documentation
- `email_preview.html` - Visual email preview

## Tech Stack

- **Backend**: Django 5.x
- **Database**: MongoDB + SQLite
- **Email**: Brevo (SendinBlue)
- **Storage**: Cloudinary
- **Frontend**: HTML, CSS, JavaScript

## Project Structure

```
SatyaMatrx/
├── user/                   # User app (auth, chat, email)
├── templates/              # HTML templates
├── static/                 # CSS, JS, assets
├── SatyaMatrx/            # Django settings
└── .env                    # Configuration (not in git)
```

## License

© 2025 SatyaMatrix - The Network of Truth
