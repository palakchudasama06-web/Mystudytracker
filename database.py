import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta
from utils import verify_password

DB_PATH = Path(__file__).parent / "ca_compass.db"


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = conn()
    cur = c.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        attempt TEXT NOT NULL,
        articleship INTEGER DEFAULT 0,
        xp INTEGER DEFAULT 0,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        progress REAL DEFAULT 0,
        daily_target_minutes INTEGER DEFAULT 45,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );

    CREATE TABLE IF NOT EXISTS chapters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        progress REAL DEFAULT 0,
        completed INTEGER DEFAULT 0,
        FOREIGN KEY(subject_id) REFERENCES subjects(id)
    );

    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        minutes INTEGER NOT NULL,
        session_type TEXT NOT NULL,
        date TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS revisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        chapter_id INTEGER NOT NULL,
        chapter_name TEXT NOT NULL,
        revision_type TEXT NOT NULL,
        due_date TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)

    c.commit()
    c.close()


def create_user(name, username, password_hash, attempt, articleship):
    c = conn()
    try:
        cur = c.execute(
            """INSERT INTO users(name,username,password_hash,attempt,articleship,created_at)
               VALUES(?,?,?,?,?,?)""",
            (name, username, password_hash, attempt, int(articleship), datetime.now().isoformat())
        )
        c.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("That Login ID is already taken.")
    finally:
        c.close()


def authenticate_user(username, password):
    c = conn()
    row = c.execute("SELECT id,password_hash FROM users WHERE username=?", (username,)).fetchone()
    c.close()
    if row and verify_password(password, row["password_hash"]):
        return row["id"]
    return None


def get_user(user_id):
    c = conn()
    row = c.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    c.close()
    return dict(row) if row else None


def update_profile(user_id, name, attempt, articleship):
    c = conn()
    c.execute(
        "UPDATE users SET name=?, attempt=?, articleship=? WHERE id=?",
        (name, attempt, int(articleship), user_id)
    )
    c.commit()
    c.close()


def get_subjects(user_id):
    c = conn()
    rows = c.execute(
        "SELECT * FROM subjects WHERE user_id=? ORDER BY id", (user_id,)
    ).fetchall()
    c.close()
    return [dict(x) for x in rows]


def add_subject(user_id, name, daily_target):
    c = conn()
    c.execute(
        "INSERT INTO subjects(user_id,name,daily_target_minutes) VALUES(?,?,?)",
        (user_id, name, daily_target)
    )
    c.commit()
    c.close()


def update_subject(subject_id, progress, daily_target):
    c = conn()
    c.execute(
        "UPDATE subjects SET progress=?, daily_target_minutes=? WHERE id=?",
        (progress, daily_target, subject_id)
    )
    c.commit()
    c.close()


def delete_subject(subject_id):
    c = conn()
    c.execute("DELETE FROM chapters WHERE subject_id=?", (subject_id,))
    c.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
    c.commit()
    c.close()


def get_chapters(subject_id):
    c = conn()
    rows = c.execute(
        "SELECT * FROM chapters WHERE subject_id=? ORDER BY id", (subject_id,)
    ).fetchall()
    c.close()
    return [dict(x) for x in rows]


def add_chapter(subject_id, name):
    c = conn()
    c.execute("INSERT INTO chapters(subject_id,name) VALUES(?,?)", (subject_id, name))
    c.commit()
    c.close()


def update_chapter(chapter_id, progress, completed):
    c = conn()
    c.execute(
        "UPDATE chapters SET progress=?, completed=? WHERE id=?",
        (progress, int(completed), chapter_id)
    )
    c.commit()
    c.close()


def delete_chapter(chapter_id):
    c = conn()
    c.execute("DELETE FROM chapters WHERE id=?", (chapter_id,))
    c.commit()
    c.close()


def add_study_session(user_id, subject, minutes, session_type):
    c = conn()
    now = datetime.now()
    c.execute(
        """INSERT INTO study_sessions(user_id,subject,minutes,session_type,date,created_at)
           VALUES(?,?,?,?,?,?)""",
        (user_id, subject, int(minutes), session_type, now.date().isoformat(), now.isoformat())
    )
    xp = int(minutes) * 2
    c.execute("UPDATE users SET xp=xp+? WHERE id=?", (xp, user_id))
    c.commit()
    c.close()


def get_study_sessions(user_id, limit=100):
    c = conn()
    rows = c.execute(
        """SELECT * FROM study_sessions WHERE user_id=?
           ORDER BY created_at DESC LIMIT ?""",
        (user_id, limit)
    ).fetchall()
    c.close()
    return [dict(x) for x in rows]


def get_daily_minutes(user_id):
    c = conn()
    today = date.today()
    values = {}

    for key, start in {
        "today": today,
        "week": today - timedelta(days=6),
        "month": today - timedelta(days=29),
    }.items():
        row = c.execute(
            "SELECT COALESCE(SUM(minutes),0) total FROM study_sessions WHERE user_id=? AND date>=?",
            (user_id, start.isoformat())
        ).fetchone()
        values[key] = int(row["total"])

    c.close()
    return values


def calculate_streak(user_id):
    c = conn()
    rows = c.execute(
        "SELECT DISTINCT date FROM study_sessions WHERE user_id=? ORDER BY date DESC",
        (user_id,)
    ).fetchall()
    c.close()

    dates = {date.fromisoformat(r["date"]) for r in rows}
    if not dates:
        return 0

    today = date.today()
    current = today if today in dates else today - timedelta(days=1)
    streak = 0

    while current in dates:
        streak += 1
        current -= timedelta(days=1)

    return streak


def get_stats(user_id):
    c = conn()
    row = c.execute(
        "SELECT COALESCE(xp,0) xp FROM users WHERE id=?", (user_id,)
    ).fetchone()
    total = c.execute(
        "SELECT COALESCE(SUM(minutes),0) total FROM study_sessions WHERE user_id=?",
        (user_id,)
    ).fetchone()
    c.close()

    return {
        "xp": int(row["xp"]),
        "total_minutes": int(total["total"]),
        "streak": calculate_streak(user_id),
    }


def add_revision(chapter_id, revision_type):
    offsets = {
        "24 Hours": 1,
        "7 Days": 7,
        "21 Days": 21,
        "45 Days": 45,
        "Final Revision": 90,
    }
    c = conn()
    ch = c.execute("SELECT name, subject_id FROM chapters WHERE id=?", (chapter_id,)).fetchone()
    if not ch:
        c.close()
        return

    user = c.execute(
        "SELECT user_id FROM subjects WHERE id=?", (ch["subject_id"],)
    ).fetchone()

    due = date.today() + timedelta(days=offsets.get(revision_type, 7))
    c.execute(
        """INSERT INTO revisions(user_id,chapter_id,chapter_name,revision_type,due_date)
           VALUES(?,?,?,?,?)""",
        (user["user_id"], chapter_id, ch["name"], revision_type, due.isoformat())
    )
    c.commit()
    c.close()


def get_due_revisions(user_id):
    c = conn()
    rows = c.execute(
        """SELECT * FROM revisions
           WHERE user_id=? AND completed=0 AND due_date<=?
           ORDER BY due_date""",
        (user_id, date.today().isoformat())
    ).fetchall()
    c.close()
    return [dict(x) for x in rows]


def complete_revision(revision_id):
    c = conn()
    c.execute("UPDATE revisions SET completed=1 WHERE id=?", (revision_id,))
    c.commit()
    c.close()
