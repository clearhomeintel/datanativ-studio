import streamlit as st
from storage import get_all_students

def render():
    st.markdown("""
# Welcome to DataNativ Studio 🎓
### *The AI Recommendation App Builder for Future Innovators*
""")

    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown("**📅 4-Week Journey**")
            st.caption("Build a real AI recommendation app from idea to demo day—step by step.")
    with col2:
        with st.container(border=True):
            st.markdown("**🤖 AI-Powered Coaching**")
            st.caption("Get personalized feedback from an AI coach on your ideas, logic, and code.")
    with col3:
        with st.container(border=True):
            st.markdown("**👁️ Live App Preview**")
            st.caption("See your recommendation app come to life as you build it—in real time.")

    st.divider()

    st.markdown("### What You'll Build")
    st.markdown("""
In this bootcamp, you'll design and build a **recommendation-style AI app** — not just a chatbot.

Real recommendation apps include:
- College fit finders used by millions of students
- Spotify's music recommendation engine  
- Netflix's content suggestion algorithm
- Career path matchers used by companies worldwide

**You'll learn how to think like the product designers behind them.**
""")

    st.divider()

    st.markdown("### Your 4-Week Roadmap")
    cols = st.columns(4)
    weeks = [
        ("Week 1", "Problem & User", "Define who your app helps and why recommendations matter for them."),
        ("Week 2", "Logic & Design", "Define the inputs your app collects and how it ranks recommendations."),
        ("Week 3", "Code Editing", "Safely edit key parts of your app's code with AI explanations."),
        ("Week 4", "Test & Pitch", "Test with real users, iterate, and present your final demo-day pitch."),
    ]
    for i, (week, title, desc) in enumerate(weeks):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"**{week}**")
                st.markdown(f"*{title}*")
                st.caption(desc)

    st.divider()

    st.markdown("### Start or Continue Your Project")

    existing_students = get_all_students()

    if existing_students:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Continue as an existing student:**")
            student_options = {f"{s['name']} — {s['project_type']}": s['id'] for s in existing_students}
            selected = st.selectbox("Choose your name:", list(student_options.keys()), label_visibility="collapsed")
            if st.button("Continue My Project →", use_container_width=True, type="primary"):
                st.session_state.student_id = student_options[selected]
                st.session_state.page = "project"
                st.rerun()
        with col2:
            st.markdown("**Or start fresh:**")
            st.write("")
            if st.button("🚀 Start a New Project", use_container_width=True):
                st.session_state.student_id = None
                st.session_state.page = "setup"
                st.rerun()
    else:
        st.markdown("Ready to build your AI app?")
        if st.button("🚀 Start Your Project", type="primary", use_container_width=True):
            st.session_state.page = "setup"
            st.rerun()

    st.divider()
    st.caption("DataNativ Studio — AI Bootcamp for High School Students | Powered by OpenAI")
