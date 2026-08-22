import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from database import init_db, create_user, authenticate_user, get_user, update_profile
from database import get_subjects, add_subject, update_subject, delete_subject
from database import get_chapters, add_chapter, update_chapter, delete_chapter
from database import add_study_session, get_study_sessions, get_daily_minutes
from database import add_revision, get_due_revisions, complete_revision, get_stats
from utils import hash_password, motivational_message, xp_for_minutes, level_from_xp

st.set_page_config(
    page_title="CA Compass",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()

# --- Session State Initializations ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"
if "lecture_logs" not in st.session_state:
    st.session_state.lecture_logs = []
if "pending_homework" not in st.session_state:
    st.session_state.pending_homework = []

# ---------- Styling ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 15% 10%, rgba(93, 75, 150, .16), transparent 28%),
            radial-gradient(circle at 85% 15%, rgba(0, 180, 190, .10), transparent 25%),
            #080b12;
        color: #f4f7fb;
    }

    [data-testid="stSidebar"] {
        background: #0c1019;
        border-right: 1px solid #202838;
    }

    .brand {
        font-size: 30px;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 2px;
    }

    .tagline {
        color: #8f9aae;
        font-size: 12px;
        margin-bottom: 24px;
    }

    .hero {
        padding: 28px;
        border: 1px solid #242d3d;
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(25,31,45,.96), rgba(13,17,27,.96));
        box-shadow: 0 15px 45px rgba(0,0,0,.22);
    }

    .hero h1 {
        margin: 0;
        font-size: 34px;
        font-weight: 800;
    }

    .hero p {
        color: #9ca8bb;
        margin-top: 7px;
    }

    .metric-card {
        padding: 20px;
        min-height: 128px;
        border-radius: 17px;
        border: 1px solid #242d3d;
        background: #101621;
    }

    .metric-label {
        color: #8f9aae;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: .7px;
    }

    .metric-value {
        font-size: 29px;
        font-weight: 800;
        margin-top: 8px;
    }

    .metric-sub {
        color: #7e8ba0;
        font-size: 12px;
        margin-top: 4px;
    }

    .mission {
        padding: 15px 17px;
        margin: 9px 0;
        border-radius: 14px;
        border: 1px solid #263044;
        background: #0f1520;
    }

    .small-muted {
        color: #8290a5;
        font-size: 12px;
    }

    .section-title {
        font-size: 21px;
        font-weight: 750;
        margin-top: 25px;
        margin-bottom: 10px;
    }

    div.stButton > button {
        border-radius: 10px;
        font-weight: 650;
    }
</style>
""", unsafe_allow_html=True)


def go(page):
    st.session_state.page = page


def logout():
    st.session_state.user_id = None
    st.session_state.is_admin = False
    st.session_state.page = "Dashboard"
    st.rerun()


# ---------- Auth / Login ----------
if st.session_state.user_id is None and not st.session_state.is_admin:
    st.markdown("""
    <div class="hero">
        <div class="brand">🎓 CA COMPASS</div>
        <div class="tagline">Study. Progress. Level Up. Become a CA.</div>
        <h1>Your CA journey, tracked like a mission.</h1>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔐 Login", "🚀 Create Account"])

    with tab1:
        with st.form("login"):
            username = st.text_input("Login ID")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Enter CA Compass", use_container_width=True)
            
            if submitted:
                # --- SECRET ADMIN GATEWAY ---
                # Change "boss" and "mysecret123" to your actual desired login!
                if username.strip() == "boss" and password == "mysecret123":
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    # Normal Student Login
                    user_id = authenticate_user(username.strip(), password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.rerun()
                    else:
                        st.error("Invalid Login ID or password.")

    with tab2:
        with st.form("signup"):
            st.subheader("Create your CA profile")
            name = st.text_input("Full Name")
            username = st.text_input("Choose Login ID")
            password = st.text_input("Create Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            attempt = st.selectbox("CA Final Attempt", [
                "May 2027", "November 2027", "May 2028", "November 2028", "Other"
            ])
            articleship = st.checkbox("I am currently doing articleship")
            submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                if not name.strip() or not username.strip() or not password:
                    st.error("Please fill all required fields.")
                elif len(password) < 6:
                    st.error("Password should contain at least 6 characters.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                # Prevent users from taking the admin username
                elif username.strip() == "boss":
                    st.error("This username is reserved.")
                else:
                    try:
                        uid = create_user(name.strip(), username.strip(), hash_password(password), attempt, articleship)
                        st.session_state.user_id = uid
                        st.success("Account created. Welcome to CA Compass!")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))

    st.stop()


# ---------- SECRET ADMIN DASHBOARD ----------
if st.session_state.is_admin:
    st.markdown('<div class="hero"><h1>👑 Master Admin Dashboard</h1><p>Welcome to the command center. View all user data here.</p></div>', unsafe_allow_html=True)
    
    if st.button("🚪 Logout Admin", type="primary"):
        logout()
        
    conn = sqlite3.connect("ca_compass.db")
    
    st.subheader("👥 Registered Users")
    df_users = pd.read_sql_query("SELECT id, name, username, attempt, articleship FROM users", conn)
    st.dataframe(df_users, use_container_width=True, hide_index=True)
    
    st.divider()
    
    st.subheader("🏆 Global Study Leaderboard")
    leaderboard_query = """
        SELECT u.name as Student, u.username as User_ID, SUM(s.minutes)/60.0 as Total_Hours
        FROM users u
        LEFT JOIN study_sessions s ON u.id = s.user_id
        GROUP BY u.id
        ORDER BY Total_Hours DESC
    """
    df_leaderboard = pd.read_sql_query(leaderboard_query, conn)
    df_leaderboard['Total_Hours'] = df_leaderboard['Total_Hours'].fillna(0).round(1)
    st.dataframe(df_leaderboard, use_container_width=True, hide_index=True)
    
    st.divider()
    
    st.subheader("📋 Master Study & Lecture Logs")
    logs_query = """
        SELECT u.name as Student, s.date as Date, s.subject as Subject, 
               s.session_type as Type, s.minutes as Minutes_Studied
        FROM study_sessions s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.date DESC
    """
    df_all_sessions = pd.read_sql_query(logs_query, conn)
    st.dataframe(df_all_sessions, use_container_width=True, hide_index=True)
    
    conn.close()
    st.stop() # Stops the rest of the app from loading so normal tabs don't show up


# ---------- NORMAL USER FLOW (Students Only) ----------
user = get_user(st.session_state.user_id)
if not user:
    logout()

with st.sidebar:
    st.markdown('<div class="brand">🎓 CA COMPASS</div>', unsafe_allow_html=True)
    st.markdown('<div class="tagline">Your CA command center</div>', unsafe_allow_html=True)

    st.caption(f"Welcome, {user['name']}")
    st.caption(f"Attempt: {user['attempt']}")

    # Notice there is NO admin button here!
    pages = [
        ("🏠", "Dashboard"),
        ("📚", "Subjects & Chapters"),
        ("🎯", "Study Planner"),
        ("📅", "Daily Lectures"), 
        ("⏱️", "Pomodoro Focus"),
        ("🔄", "Revision Center"),
        ("📊", "Analytics"),
        ("🏆", "Achievements"),
        ("⚙️", "Settings"),
    ]

    for icon, label in pages:
        if st.button(f"{icon}  {label}", key=f"nav_{label}", use_container_width=True):
            go(label)

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        logout()


# ---------- Dashboard ----------
if st.session_state.page == "Dashboard":
    stats = get_stats(user["id"])
    level, current_xp, next_xp = level_from_xp(stats["xp"])
    daily = get_daily_minutes(user["id"])
    today_hours = daily.get("today", 0) / 60
    week_hours = daily.get("week", 0) / 60
    quote = motivational_message(today_hours, stats["streak"])

    # Attempt Countdown Calculation
    target_date = None
    if user['attempt'] == "May 2027":
        target_date = date(2027, 5, 1)
    elif user['attempt'] == "November 2027":
        target_date = date(2027, 11, 1)
    elif user['attempt'] == "May 2028":
        target_date = date(2028, 5, 1)
    elif user['attempt'] == "November 2028":
        target_date = date(2028, 11, 1)

    days_left = (target_date - date.today()).days if target_date else "N/A"

    st.markdown(f"""
    <div class="hero">
        <div class="small-muted">CA FINAL • {user['attempt']}</div>
        <h1>Good morning, {user['name'].split()[0]} 👋</h1>
        <p>{quote}</p>
    </div>
    """, unsafe_allow_html=True)

    if user.get("articleship"):
        st.info("🏢 **Articleship Active:** Balance is key. Aim for 3-4 consistent hours of study daily alongside office work.")
    else:
        st.success("🚀 **Dedicated Study Period Active:** You are in full study mode! Push for 8-10 hours of focused deep work today.")

    st.markdown('<div class="section-title">⚡ Your Command Center</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("⏳", "DAYS LEFT", f"{days_left}", "Until your attempt"),
        ("🔥", "STREAK", f"{stats['streak']} days", "Consistency beats intensity"),
        ("⏱️", "TODAY", f"{today_hours:.1f} hrs", "Focused study time"),
        ("⭐", "LEVEL", f"Level {level}", f"{current_xp:,} XP"),
    ]
    for col, (icon, label, value, sub) in zip([c1,c2,c3,c4], cards):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{icon} {label}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">⚔️ Today\'s Missions</div>', unsafe_allow_html=True)

    subjects = get_subjects(user["id"])
    if not subjects:
        st.info("Start by adding your CA subjects in **Subjects & Chapters**.")
    else:
        missions = subjects[:3]
        for s in missions:
            mins = int(s["daily_target_minutes"] or 45)
            st.markdown(f"""
            <div class="mission">
                <b>📘 {s['name']}</b>
                <span style="float:right;color:#8d7cff;">+{xp_for_minutes(mins)} XP</span><br>
                <span class="small-muted">Today's suggested target: {mins} minutes</span>
            </div>
            """, unsafe_allow_html=True)


# ---------- Subjects ----------
elif st.session_state.page == "Subjects & Chapters":
    st.title("📚 Subjects & Chapters")
    st.caption("Add and track your syllabus chapters manually.")

    subjects = get_subjects(user["id"])

    with st.expander("➕ Add a Subject Manually", expanded=not subjects):
        with st.form("add_subject"):
            name = st.text_input("Subject name", placeholder="e.g. Financial Reporting")
            target = st.number_input("Daily target (minutes)", min_value=5, max_value=600, value=45)
            if st.form_submit_button("Add Subject"):
                if name.strip():
                    add_subject(user["id"], name.strip(), target)
                    st.rerun()

    for s in subjects:
        with st.expander(f"📘 {s['name']}  •  {s['progress']}% complete"):
            st.progress(min(max(float(s["progress"]) / 100, 0), 1))
            c1, c2, c3 = st.columns([2,1,1])
            with c1:
                new_progress = st.slider("Progress %", 0, 100, int(s["progress"]), key=f"p{s['id']}")
            with c2:
                new_target = st.number_input("Daily min", 5, 600, int(s["daily_target_minutes"]), key=f"t{s['id']}")
            with c3:
                st.write("")
                if st.button("Save", key=f"save{s['id']}"):
                    update_subject(s["id"], new_progress, new_target)
                    st.rerun()

            st.markdown("**Chapters**")
            chapters = get_chapters(s["id"])
            for ch in chapters:
                cc1, cc2, cc3 = st.columns([4,2,1])
                with cc1:
                    st.write(f"**{ch['name']}**")
                with cc2:
                    st.progress(ch["progress"]/100)
                with cc3:
                    if st.button("🗑️", key=f"delch{ch['id']}"):
                        delete_chapter(ch["id"])
                        st.rerun()

            with st.form(f"chapter{s['id']}"):
                chapter_name = st.text_input("Add chapter", key=f"cn{s['id']}")
                if st.form_submit_button("Add Chapter"):
                    if chapter_name.strip():
                        add_chapter(s["id"], chapter_name.strip())
                        st.rerun()


# ---------- Daily Lectures ----------
elif st.session_state.page == "Daily Lectures":
    st.title("📅 Daily Lectures Tracker")
    st.caption("Log your coaching sessions, important points, and automatically schedule post-articleship homework.")

    subjects = get_subjects(user["id"])
    if not subjects:
        st.warning("Please add subjects from the **Subjects & Chapters** tab first.")
    else:
        with st.form("lecture_tracker"):
            c1, c2 = st.columns(2)
            with c1:
                session_time = st.selectbox("Lecture Time", ["Morning 🌅", "Night 🌙"])
                subject_names = {s["name"]: s["id"] for s in subjects}
                subject_studied = st.selectbox("Subject", list(subject_names.keys()))
                chapter_studied = st.text_input("Chapter/Topic Covered", placeholder="e.g. Ind AS 115")
                study_hours = st.number_input("Lecture Duration (Hours)", min_value=0.5, step=0.5, value=2.0)
            
            with c2:
                imp_points = st.text_area("Key Points Learned (Optional)", placeholder="Jot down quick notes...")
                imp_questions = st.text_area("Important Questions Marked (Optional)", placeholder="e.g. Q4, Q9 from module")
                homework_qs = st.text_area("Homework Questions (Optional)", placeholder="Will be added to your pending tasks.")

            submit_lecture = st.form_submit_button("Log Lecture Session", use_container_width=True)

            if submit_lecture:
                minutes = int(study_hours * 60)
                log_title = f"{subject_studied} ({session_time} Lecture)"
                
                add_study_session(user["id"], log_title, minutes, "Lecture")
                
                new_log = {
                    "Date": date.today().strftime("%Y-%m-%d"),
                    "Time": session_time.split()[0],
                    "Subject": subject_studied,
                    "Topic": chapter_studied,
                    "Key Points": imp_points if imp_points else "-",
                    "Imp Qs": imp_questions if imp_questions else "-"
                }
                st.session_state.lecture_logs.insert(0, new_log) 

                if homework_qs.strip():
                    st.session_state.pending_homework.append({
                        "id": str(datetime.now().timestamp()),
                        "subject": subject_studied,
                        "topic": chapter_studied,
                        "tasks": homework_qs
                    })
                    st.info("Homework added to your pending list for after articleship.")

                st.balloons()
                st.success(f"Logged {study_hours} hours for {subject_studied}. XP Earned!")
                st.rerun()

    st.divider()
    
    if st.session_state.pending_homework:
        st.subheader("📝 Pending Homework")
        st.caption("Complete these tasks during your post-articleship self-study session.")
        
        for hw in st.session_state.pending_homework:
            with st.container():
                st.markdown(f"""
                <div class="mission" style="border-left: 4px solid #00b4be;">
                    <b>{hw['subject']} - {hw['topic']}</b><br>
                    <span class="small-muted">Tasks: {hw['tasks']}</span>
                </div>
                """, unsafe_allow_html=True)
                
                hw_col1, hw_col2 = st.columns([1, 1])
                with hw_col1:
                    hw_mins = st.number_input("Minutes spent on HW", min_value=15, step=15, value=45, key=f"time_{hw['id']}")
                with hw_col2:
                    st.write("") 
                    st.write("")
                    if st.button("✅ Mark Completed & Claim XP", key=f"btn_{hw['id']}"):
                        add_study_session(user["id"], f"Homework: {hw['subject']}", hw_mins, "Self Study")
                        st.session_state.pending_homework = [h for h in st.session_state.pending_homework if h['id'] != hw['id']]
                        st.success(f"Homework completed! Earned XP for {hw_mins} minutes.")
                        st.rerun()

    st.subheader("📋 Lecture History")
    if st.session_state.lecture_logs:
        df_logs = pd.DataFrame(st.session_state.lecture_logs)
        st.dataframe(df_logs, use_container_width=True, hide_index=True)
    else:
        st.info("No lectures logged yet. Start tracking your classes above!")


# ---------- Planner ----------
elif st.session_state.page == "Study Planner":
    st.title("🎯 Study Planner")
    
    if user.get("articleship"):
        st.caption("Build a realistic plan around your articleship hours.")
    else:
        st.caption("Optimize your dedicated study leave schedule.")

    with st.form("planner"):
        c1, c2 = st.columns(2)
        with c1:
            articleship_today = st.checkbox("Articleship / Office today", value=bool(user["articleship"]))
            office_hours = st.number_input("Articleship hours", 0.0, 16.0, 8.0 if articleship_today else 0.0, .5)
        with c2:
            available = st.number_input("Study time available today (hours)", .5, 16.0, 3.5 if articleship_today else 10.0, .5)
            energy = st.select_slider("Energy level", options=["Low", "Medium", "High"], value="Medium")

        if st.form_submit_button("Generate Today's Plan", use_container_width=True):
            subjects = get_subjects(user["id"])
            if not subjects:
                st.warning("Add subjects first.")
            else:
                weights = [max(5, int(s["daily_target_minutes"])) for s in subjects]
                total = sum(weights)
                available_minutes = int(available * 60)
                st.success(f"Plan generated for {available_minutes} minutes ({available} hours).")
                for s, w in zip(subjects, weights):
                    allocated = max(10, round(available_minutes * w / total / 5) * 5)
                    st.markdown(f"**{s['name']}** — {allocated} minutes")
                    st.progress(min(allocated / max(available_minutes, 1), 1))
                if energy == "Low":
                    st.info("Low-energy mode: start with revision or pending homework before heavy new learning.")


# ---------- Pomodoro ----------
elif st.session_state.page == "Pomodoro Focus":
    st.title("⏱️ Pomodoro Focus")
    st.caption("Every focused minute is progress. The app records the subject and duration automatically.")

    subjects = get_subjects(user["id"])
    subject_names = [s["name"] for s in subjects] or ["General Study"]

    c1, c2 = st.columns([1,1])
    with c1:
        subject = st.selectbox("What are you studying?", subject_names)
        mode = st.selectbox("Session type", ["Pomodoro", "Deep Work", "Custom"])
        if mode == "Pomodoro":
            duration = st.select_slider("Focus duration", options=[15,20,25,30,45,50], value=25)
        elif mode == "Deep Work":
            duration = st.select_slider("Focus duration", options=[45,60,75,90,120], value=60)
        else:
            duration = st.number_input("Minutes", 5, 300, 30)

    with c2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">FOCUS RULE</div>
            <div class="metric-value">No Zero Days.</div>
            <div class="metric-sub">Even 15 focused minutes keeps the journey alive.</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("▶️ Start / Complete Focus Session", use_container_width=True):
        add_study_session(user["id"], subject, duration, mode)
        st.balloons()
        st.success(f"Session recorded: {duration} minutes of {subject}. +{xp_for_minutes(duration)} XP")
        st.rerun()

    sessions = get_study_sessions(user["id"], 10)
    if sessions:
        st.markdown("### Recent Sessions")
        for s in sessions:
            st.write(f"**{s['date']}** • {s['subject']} • {s['minutes']} min • {s['session_type']}")


# ---------- Revisions ----------
elif st.session_state.page == "Revision Center":
    st.title("🔄 Revision Center")
    st.caption("Turn every completed chapter into a spaced-revision mission.")

    due = get_due_revisions(user["id"])
    if not due:
        st.success("You're clear! Add revisions after completing chapters.")
    else:
        for r in due:
            c1, c2 = st.columns([4,1])
            with c1:
                st.write(f"**{r['chapter_name']}** — {r['revision_type']} • Due {r['due_date']}")
            with c2:
                if st.button("Done", key=f"rev{r['id']}"):
                    complete_revision(r["id"])
                    st.rerun()

    st.markdown("### Add a Revision")
    chapters_all = []
    for s in get_subjects(user["id"]):
        for ch in get_chapters(s["id"]):
            chapters_all.append((ch["id"], f"{s['name']} — {ch['name']}"))

    if chapters_all:
        with st.form("add_revision"):
            selected = st.selectbox("Chapter", chapters_all, format_func=lambda x: x[1])
            revision_type = st.selectbox("Revision stage", ["24 Hours", "7 Days", "21 Days", "45 Days", "Final Revision"])
            if st.form_submit_button("Schedule Revision"):
                add_revision(selected[0], revision_type)
                st.success("Revision scheduled.")
                st.rerun()
    else:
        st.info("Add chapters under Subjects & Chapters first.")


# ---------- Analytics ----------
elif st.session_state.page == "Analytics":
    st.title("📊 Analytics")
    st.caption("Measure consistency, not just raw hours.")

    daily = get_daily_minutes(user["id"])
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Today", f"{daily.get('today',0)/60:.1f} hrs")
    with c2:
        st.metric("Last 7 Days", f"{daily.get('week',0)/60:.1f} hrs")
    with c3:
        st.metric("Last 30 Days", f"{daily.get('month',0)/60:.1f} hrs")

    df = get_study_sessions(user["id"], 500)
    if df:
        import plotly.express as px
        data = pd.DataFrame(df)
        data["date"] = pd.to_datetime(data["date"])
        daily_df = data.groupby("date", as_index=False)["minutes"].sum()
        fig = px.bar(daily_df, x="date", y="minutes", title="Study Minutes by Day")
        fig.update_layout(template="plotly_dark", paper_bgcolor="#101621", plot_bgcolor="#101621")
        st.plotly_chart(fig, use_container_width=True)

        subject_df = data.groupby("subject", as_index=False)["minutes"].sum().sort_values("minutes", ascending=False)
        fig2 = px.bar(subject_df, x="subject", y="minutes", title="Study Time by Subject")
        fig2.update_layout(template="plotly_dark", paper_bgcolor="#101621", plot_bgcolor="#101621")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Complete your first focus session to unlock analytics.")


# ---------- Achievements ----------
elif st.session_state.page == "Achievements":
    st.title("🏆 Achievements")
    stats = get_stats(user["id"])

    achievements = [
        ("🌱 First Step", stats["total_minutes"] >= 15, "Study for 15 minutes"),
        ("🔥 7-Day Warrior", stats["streak"] >= 7, "Maintain a 7-day streak"),
        ("⚔️ 10-Hour Milestone", stats["total_minutes"] >= 600, "Study 10 total hours"),
        ("💎 50-Hour Milestone", stats["total_minutes"] >= 3000, "Study 50 total hours"),
        ("🏆 100-Hour Milestone", stats["total_minutes"] >= 6000, "Study 100 total hours"),
    ]

    for title, unlocked, requirement in achievements:
        status = "UNLOCKED" if unlocked else "LOCKED"
        st.markdown(f"""
        <div class="mission">
            <b>{title}</b>
            <span style="float:right;">{'🟢' if unlocked else '🔒'} {status}</span><br>
            <span class="small-muted">{requirement}</span>
        </div>
        """, unsafe_allow_html=True)


# ---------- Settings ----------
elif st.session_state.page == "Settings":
    st.title("⚙️ Settings")
    st.caption("Customize CA Compass around your own study life.")

    with st.form("profile"):
        name = st.text_input("Name", user["name"])
        attempt = st.selectbox(
            "Attempt",
            ["May 2027", "November 2027", "May 2028", "November 2028", "Other"],
            index=["May 2027", "November 2027", "May 2028", "November 2028", "Other"].index(user["attempt"])
            if user["attempt"] in ["May 2027", "November 2027", "May 2028", "November 2028", "Other"] else 0
        )
        articleship = st.checkbox("Currently in articleship", value=bool(user["articleship"]))
        if st.form_submit_button("Save Profile"):
            update_profile(user["id"], name.strip(), attempt, articleship)
            st.success("Profile updated.")
            st.rerun()
