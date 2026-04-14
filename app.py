import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from storage import init_db, get_student, get_all_students
import ui_components as ui

st.set_page_config(
    page_title="DataNativ Studio",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_db()

if "student_id" not in st.session_state:
    st.session_state.student_id = None
if "page" not in st.session_state:
    st.session_state.page = "home"

def nav_to(page):
    st.session_state.page = page
    st.rerun()

def sidebar():
    with st.sidebar:
        st.markdown("## 🎓 DataNativ Studio")
        st.markdown("*AI Bootcamp Builder*")
        st.divider()

        if st.session_state.student_id:
            student = get_student(st.session_state.student_id)
            if student:
                st.markdown(f"**👤 {student['name']}**")
                project_type = student.get("project_type", "")
                if project_type:
                    st.caption(f"📦 {project_type}")

                progress = student.get("week_progress", {})
                weeks_done = sum(1 for w in ["week1", "week2", "week3", "week4"] if progress.get(w, False))
                st.progress(weeks_done / 4, text=f"Week {weeks_done}/4 Complete")
                st.divider()

                pages = [
                    ("🏠 Home", "home"),
                    ("🚀 My Project", "project"),
                    ("📅 Week 1: Problem & User", "week1"),
                    ("⚙️ Week 2: Logic & Design", "week2"),
                    ("💻 Week 3: Code Editing", "week3"),
                    ("🎤 Week 4: Testing & Pitch", "week4"),
                    ("👁️ App Preview", "preview"),
                ]
                for label, page_key in pages:
                    done_marker = ""
                    if page_key in ["week1","week2","week3","week4"]:
                        if progress.get(page_key, False):
                            done_marker = " ✅"
                    if st.button(f"{label}{done_marker}", key=f"nav_{page_key}", use_container_width=True):
                        nav_to(page_key)

                st.divider()
                if st.button("🏫 Teacher Dashboard", use_container_width=True):
                    nav_to("teacher")
                if st.button("🔄 Switch Student", use_container_width=True):
                    st.session_state.student_id = None
                    nav_to("home")
        else:
            if st.button("🏠 Home", use_container_width=True):
                nav_to("home")
            if st.button("🏫 Teacher Dashboard", use_container_width=True):
                nav_to("teacher")

page = st.session_state.page

if page == "home":
    from pages import home
    sidebar()
    home.render()
elif page == "setup":
    from pages import setup
    sidebar()
    setup.render()
elif page == "project":
    from pages import project
    sidebar()
    project.render()
elif page == "week1":
    from pages import week1
    sidebar()
    week1.render()
elif page == "week2":
    from pages import week2
    sidebar()
    week2.render()
elif page == "week3":
    from pages import week3
    sidebar()
    week3.render()
elif page == "week4":
    from pages import week4
    sidebar()
    week4.render()
elif page == "preview":
    from pages import preview
    sidebar()
    preview.render()
elif page == "teacher":
    from pages import teacher
    sidebar()
    teacher.render()
else:
    sidebar()
    st.error("Page not found.")
    if st.button("Go Home"):
        nav_to("home")
