# CA Compass 🎓

A professional, gaming-inspired study tracker built specifically for CA students, with articleship-friendly planning, Pomodoro/focus tracking, XP, levels, streaks, revisions, analytics and customizable subjects.

## Features in this version

- Login ID + password account system
- CA Final attempt selection during signup
- Articleship status
- Personalized dashboard
- Subject and chapter management
- Study targets
- Study planner
- Pomodoro / Deep Work / Custom focus sessions
- Study time tracked by subject
- XP and levels
- Study streaks
- Spaced revision center
- Analytics
- Achievements
- Professional dark gaming-style UI
- SQLite local database
- Passwords stored as PBKDF2 hashes, not plain text

## 1. Install Python

Use Python 3.10+.

Check:

```bash
python --version
```

## 2. Create the environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Mac/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install libraries

```bash
pip install -r requirements.txt
```

## 4. Run

```bash
streamlit run app.py
```

The browser will open the application.

## Database

The app automatically creates:

`ca_compass.db`

Do not delete this file if you want to retain local user data.

## Important hosting note

SQLite is excellent for the first local prototype, but for a real public Streamlit deployment with multiple CA students, move authentication and data to a persistent hosted database such as PostgreSQL/Supabase.

The next production version should also add:

- Persistent cloud authentication/database
- Email/password reset
- Secure session management
- Browser-based Pomodoro countdown
- Automatic daily missions
- Exam countdown based on exact attempt date
- CA Final syllabus templates
- Automatic revision scheduling
- Notifications/reminders
- Mobile responsive PWA
- Admin dashboard
- Cloud backup
- More achievements and gamification
