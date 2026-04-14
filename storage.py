import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "datanativ.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            project_type TEXT,
            target_user TEXT,
            problem TEXT,
            tone TEXT,
            features TEXT,
            week_progress TEXT DEFAULT '{}',
            week1_data TEXT DEFAULT '{}',
            week2_data TEXT DEFAULT '{}',
            week3_data TEXT DEFAULT '{}',
            week4_data TEXT DEFAULT '{}',
            config TEXT DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    _seed_demo_students()

def _seed_demo_students():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM students")
    count = c.fetchone()[0]
    conn.close()
    if count == 0:
        demo_students = [
            {
                "name": "Alex Chen",
                "project_type": "College Recommender",
                "target_user": "High school juniors who feel overwhelmed by college choices",
                "problem": "Students don't know which colleges match their actual goals, not just their GPA.",
                "tone": "Friendly & Direct",
                "features": json.dumps(["Academic Fit", "Campus Culture Match", "Financial Aid Estimator"]),
                "week_progress": json.dumps({"week1": True, "week2": True, "week3": False, "week4": False}),
                "week1_data": json.dumps({
                    "problem_statement": "Many high school students apply to colleges based only on rankings, missing schools that actually fit their learning style, goals, and budget.",
                    "user_persona": "A junior who is ambitious but unsure which colleges actually match their interests beyond just prestige.",
                    "why_recommendations": "Because college choice has too many variables for any student to manually compare—a smart recommender can surface hidden gem schools.",
                    "challenge_response": "I focused on financial fit and campus culture, not just academics."
                }),
                "week2_data": json.dumps({
                    "input_questions": "GPA, SAT/ACT scores, preferred location, campus size, major interest, budget range",
                    "recommendation_logic": "Score each college on academic fit (40%), financial fit (30%), culture match (20%), location (10%)",
                    "scoring_factors": "GPA vs acceptance rate, aid availability vs budget, campus size preference",
                    "output_description": "Top 3 colleges with match percentage, why each fits, and key stats"
                }),
            },
            {
                "name": "Maya Patel",
                "project_type": "Extracurricular Finder",
                "target_user": "9th and 10th graders who want to find activities they'll love",
                "problem": "Students join random clubs without knowing what fits their personality and goals.",
                "tone": "Energetic & Fun",
                "features": json.dumps(["Personality Match", "Goal Alignment", "Time Commitment Filter"]),
                "week_progress": json.dumps({"week1": True, "week2": False, "week3": False, "week4": False}),
                "week1_data": json.dumps({
                    "problem_statement": "Most students pick extracurriculars based on what their friends do, not what they're actually passionate about.",
                    "user_persona": "A 9th grader who feels lost when choosing activities for high school.",
                    "why_recommendations": "There are hundreds of possible activities—a recommender saves time and helps students find what they'll actually stick with.",
                    "challenge_response": ""
                }),
                "week2_data": json.dumps({}),
            },
            {
                "name": "Jordan Smith",
                "project_type": "Study Strategy Coach",
                "target_user": "Students who study hard but still get mediocre grades",
                "problem": "Effort doesn't always equal results because students use the wrong study methods for their learning style.",
                "tone": "Serious & Motivating",
                "features": json.dumps(["Learning Style Detection", "Subject-Specific Tips", "Weekly Study Plan"]),
                "week_progress": json.dumps({"week1": True, "week2": True, "week3": True, "week4": True}),
                "week1_data": json.dumps({
                    "problem_statement": "Students spend hours studying but use ineffective techniques—a coach recommends personalized strategies.",
                    "user_persona": "A motivated student who feels their effort isn't paying off.",
                    "why_recommendations": "Every student learns differently. One-size study advice fails most students.",
                    "challenge_response": "I narrowed focus to 3 specific learning styles: visual, auditory, and kinesthetic."
                }),
                "week2_data": json.dumps({
                    "input_questions": "Learning style, current grades, subjects, study hours, test anxiety level",
                    "recommendation_logic": "Match learning style to proven techniques, weight by subject difficulty",
                    "scoring_factors": "Learning style alignment, subject complexity, time available",
                    "output_description": "3 personalized study strategies with specific steps and schedule"
                }),
                "week3_data": json.dumps({
                    "app_title": "StudySmarter Coach",
                    "intro_text": "Answer a few quick questions and get your personalized study strategy.",
                    "edited_inputs": "Learning style, current GPA, weakest subjects, available study hours",
                    "scoring_weights": "Learning style: 40%, Subject fit: 35%, Time: 25%"
                }),
                "week4_data": json.dumps({
                    "feedback_notes": "Testers loved the specific technique suggestions. Wanted more examples.",
                    "improvements": "Added example schedules for each learning style.",
                    "pitch": "StudySmarter Coach matches your unique learning style to proven strategies—so every study hour actually counts."
                }),
            }
        ]
        for s in demo_students:
            upsert_student(s)

def upsert_student(data):
    conn = get_conn()
    c = conn.cursor()
    if "id" in data and data["id"]:
        c.execute("""
            UPDATE students SET
                name=?, project_type=?, target_user=?, problem=?, tone=?, features=?,
                week_progress=?, week1_data=?, week2_data=?, week3_data=?, week4_data=?,
                config=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (
            data.get("name",""),
            data.get("project_type",""),
            data.get("target_user",""),
            data.get("problem",""),
            data.get("tone",""),
            data.get("features","[]") if isinstance(data.get("features"), str) else json.dumps(data.get("features",[])),
            data.get("week_progress","{}") if isinstance(data.get("week_progress"), str) else json.dumps(data.get("week_progress",{})),
            data.get("week1_data","{}") if isinstance(data.get("week1_data"), str) else json.dumps(data.get("week1_data",{})),
            data.get("week2_data","{}") if isinstance(data.get("week2_data"), str) else json.dumps(data.get("week2_data",{})),
            data.get("week3_data","{}") if isinstance(data.get("week3_data"), str) else json.dumps(data.get("week3_data",{})),
            data.get("week4_data","{}") if isinstance(data.get("week4_data"), str) else json.dumps(data.get("week4_data",{})),
            data.get("config","{}") if isinstance(data.get("config"), str) else json.dumps(data.get("config",{})),
            data["id"]
        ))
        student_id = data["id"]
    else:
        c.execute("""
            INSERT INTO students (name, project_type, target_user, problem, tone, features,
                week_progress, week1_data, week2_data, week3_data, week4_data, config)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data.get("name",""),
            data.get("project_type",""),
            data.get("target_user",""),
            data.get("problem",""),
            data.get("tone",""),
            data.get("features","[]") if isinstance(data.get("features"), str) else json.dumps(data.get("features",[])),
            data.get("week_progress","{}") if isinstance(data.get("week_progress"), str) else json.dumps(data.get("week_progress",{})),
            data.get("week1_data","{}") if isinstance(data.get("week1_data"), str) else json.dumps(data.get("week1_data",{})),
            data.get("week2_data","{}") if isinstance(data.get("week2_data"), str) else json.dumps(data.get("week2_data",{})),
            data.get("week3_data","{}") if isinstance(data.get("week3_data"), str) else json.dumps(data.get("week3_data",{})),
            data.get("week4_data","{}") if isinstance(data.get("week4_data"), str) else json.dumps(data.get("week4_data",{})),
            data.get("config","{}") if isinstance(data.get("config"), str) else json.dumps(data.get("config",{})),
        ))
        student_id = c.lastrowid
    conn.commit()
    conn.close()
    return student_id

def get_student(student_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE id=?", (student_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    for field in ["features", "week_progress", "week1_data", "week2_data", "week3_data", "week4_data", "config"]:
        try:
            d[field] = json.loads(d[field] or "{}")
        except Exception:
            d[field] = {} if field != "features" else []
    return d

def get_all_students():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM students ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    students = []
    for row in rows:
        d = dict(row)
        for field in ["features", "week_progress", "week1_data", "week2_data", "week3_data", "week4_data", "config"]:
            try:
                d[field] = json.loads(d[field] or "{}")
            except Exception:
                d[field] = {} if field != "features" else []
        students.append(d)
    return students

def save_week_data(student_id, week_key, data):
    student = get_student(student_id)
    if not student:
        return
    student[f"{week_key}_data"] = data
    student["id"] = student_id
    upsert_student(student)

def mark_week_complete(student_id, week_key):
    student = get_student(student_id)
    if not student:
        return
    progress = student.get("week_progress", {})
    progress[week_key] = True
    student["week_progress"] = progress
    student["id"] = student_id
    upsert_student(student)
