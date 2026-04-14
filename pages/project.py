import streamlit as st
from storage import get_student
from ui_components import progress_summary, info_card

def render():
    student_id = st.session_state.get("student_id")
    if not student_id:
        st.warning("No student selected.")
        if st.button("Go Home"):
            st.session_state.page = "home"
            st.rerun()
        return

    student = get_student(student_id)
    if not student:
        st.error("Student not found.")
        return

    st.markdown(f"## 📦 {student['name']}'s Project Dashboard")
    st.caption(f"*{student['project_type']}* | Tone: {student.get('tone','')}")
    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Weekly Progress")
        progress_summary(student.get("week_progress", {}))
    with col2:
        weeks_done = sum(1 for w in ["week1","week2","week3","week4"] if student.get("week_progress",{}).get(w,False))
        st.metric("Overall Progress", f"{weeks_done}/4 weeks", "Keep going! 🚀")

    st.divider()

    st.markdown("### Project Summary")
    col1, col2 = st.columns(2)
    with col1:
        info_card("Your Target User", student.get("target_user","Not defined yet"), "👤")
    with col2:
        info_card("Problem You're Solving", student.get("problem","Not defined yet"), "🎯")

    features = student.get("features", [])
    if isinstance(features, list) and features:
        st.markdown("**Core Features:**")
        for f in features:
            st.markdown(f"- {f}")

    config = student.get("config", {})
    if config.get("app_title"):
        st.markdown(f"**App Title:** `{config['app_title']}`")

    st.divider()

    st.markdown("### Jump Into This Week")
    weeks_progress = student.get("week_progress", {})
    week1_done = weeks_progress.get("week1", False)
    week2_done = weeks_progress.get("week2", False)
    week3_done = weeks_progress.get("week3", False)
    week4_done = weeks_progress.get("week4", False)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button(f"{'✅' if week1_done else '📅'} Week 1\nProblem & User", use_container_width=True):
            st.session_state.page = "week1"
            st.rerun()
    with col2:
        btn2_label = f"{'✅' if week2_done else '📅'} Week 2\nLogic & Design"
        if st.button(btn2_label, use_container_width=True):
            st.session_state.page = "week2"
            st.rerun()
    with col3:
        btn3_label = f"{'✅' if week3_done else '📅'} Week 3\nCode Editing"
        if st.button(btn3_label, use_container_width=True):
            st.session_state.page = "week3"
            st.rerun()
    with col4:
        btn4_label = f"{'✅' if week4_done else '📅'} Week 4\nTest & Pitch"
        if st.button(btn4_label, use_container_width=True):
            st.session_state.page = "week4"
            st.rerun()

    st.divider()
    if st.button("👁️ Preview My App", type="primary", use_container_width=True):
        st.session_state.page = "preview"
        st.rerun()
