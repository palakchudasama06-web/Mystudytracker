import os
from datetime import datetime, date, timedelta
from supabase import create_client, Client

# --- SUPABASE CREDENTIALS ---
SUPABASE_URL = "https://ryswgudzkbabjuiofrne.supabase.co"
SUPABASE_KEY = "sb_publishable_fZWSgYIZatoT0TeTwkKw_w_CugLKbR2"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def init_db():
    # Tables are initialized directly in the Supabase SQL Editor
    pass


# ---------- User Authentication ----------

def create_user(name, username, password_hash, attempt, articleship):
    data = {
        "name": name,
        "username": username,
        "password_hash": password_hash,
        "attempt": attempt,
        "articleship": articleship
    }
    
    try:
        response = supabase.table("users").insert(data).execute()
        return response.data[0]["id"]
    except Exception as e:
        # This catches the Supabase APIError instead of crashing the app
        raise ValueError("Failed to create account! This Login ID might already be taken, or the database tables are missing in Supabase.")


def authenticate_user(username, raw_password):
    from utils import verify_password
    response = supabase.table("users").select("*").eq("username", username).execute()
    if response.data:
        user = response.data[0]
        if verify_password(raw_password, user["password_hash"]):
            return user["id"]
    return None


def get_user(user_id):
    if not user_id:
        return None
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    return response.data[0] if response.data else None


def update_profile(user_id, name, attempt, articleship):
    supabase.table("users").update({
        "name": name,
        "attempt": attempt,
        "articleship": articleship
    }).eq("id", user_id).execute()


# ---------- Subjects & Chapters ----------

def get_subjects(user_id):
    response = supabase.table("subjects").select("*").eq("user_id", user_id).execute()
    return response.data or []


def add_subject(user_id, name, daily_target):
    supabase.table("subjects").insert({
        "user_id": user_id,
        "name": name,
        "daily_target_minutes": daily_target,
        "progress": 0
    }).execute()


def update_subject(subject_id, progress, daily_target):
    supabase.table("subjects").update({
        "progress": progress,
        "daily_target_minutes": daily_target
    }).eq("id", subject_id).execute()


def delete_subject(subject_id):
    supabase.table("subjects").delete().eq("id", subject_id).execute()


def get_chapters(subject_id):
    response = supabase.table("chapters").select("*").eq("subject_id", subject_id).execute()
    return response.data or []


def add_chapter(subject_id, name):
    supabase.table("chapters").insert({
        "subject_id": subject_id,
        "name": name,
        "progress": 0
    }).execute()


def update_chapter(chapter_id, progress):
    supabase.table("chapters").update({"progress": progress}).eq("id", chapter_id).execute()


def delete_chapter(chapter_id):
    supabase.table("chapters").delete().eq("id", chapter_id).execute()


# ---------- Study Sessions & Analytics ----------

def add_study_session(user_id, subject, minutes, session_type):
    today_str = date.today().isoformat()
    supabase.table("study_sessions").insert({
        "user_id": user_id,
        "subject": subject,
        "minutes": minutes,
        "session_type": session_type,
        "date": today_str
    }).execute()


def get_study_sessions(user_id, limit=500):
    response = supabase.table("study_sessions").select("*").eq("user_id", user_id).order("date", desc=True).limit(limit).execute()
    return response.data or []


def get_daily_minutes(user_id):
    today_str = date.today().isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    month_ago = (date.today() - timedelta(days=30)).isoformat()

    sessions = get_study_sessions(user_id, limit=1000)

    today_mins = sum(s["minutes"] for s in sessions if s["date"] == today_str)
    week_mins = sum(s["minutes"] for s in sessions if s["date"] >= week_ago)
    month_mins = sum(s["minutes"] for s in sessions if s["date"] >= month_ago)

    return {"today": today_mins, "week": week_mins, "month": month_mins}


def get_stats(user_id):
    sessions = get_study_sessions(user_id, limit=2000)
    total_minutes = sum(s["minutes"] for s in sessions)
    xp = int(total_minutes * 1.5)

    # Calculate streak
    unique_dates = sorted(list(set(s["date"] for s in sessions)), reverse=True)
    streak = 0
    check_date = date.today()

    for d_str in unique_dates:
        d = datetime.strptime(d_str, "%Y-%m-%d").date()
        if d == check_date:
            streak += 1
            check_date -= timedelta(days=1)
        elif d == check_date - timedelta(days=1):
            streak += 1
            check_date = d - timedelta(days=1)
        else:
            break

    return {"total_minutes": total_minutes, "xp": xp, "streak": streak}


# ---------- Revisions ----------

def add_revision(chapter_id, revision_type):
    offset_days = {"24 Hours": 1, "7 Days": 7, "21 Days": 21, "45 Days": 45, "Final Revision": 60}.get(revision_type, 1)
    due = (date.today() + timedelta(days=offset_days)).isoformat()

    supabase.table("revisions").insert({
        "chapter_id": chapter_id,
        "revision_type": revision_type,
        "due_date": due,
        "completed": False
    }).execute()


def get_due_revisions(user_id):
    response = supabase.table("revisions").select("*, chapters!inner(name, subject_id, subjects!inner(user_id))").eq("completed", False).eq("chapters.subjects.user_id", user_id).execute()
    revisions = []
    if response.data:
        for row in response.data:
            revisions.append({
                "id": row["id"],
                "chapter_name": row["chapters"]["name"],
                "revision_type": row["revision_type"],
                "due_date": row["due_date"]
            })
    return revisions


def complete_revision(revision_id):
    supabase.table("revisions").update({"completed": True}).eq("id", revision_id).execute()
