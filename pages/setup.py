import streamlit as st
import json
from storage import upsert_student
from openai_utils import ai_refine_idea

TONE_OPTIONS = ["Friendly & Direct", "Professional", "Motivating", "Energetic & Fun"]


def render():
    st.markdown("## 🚀 Start Your College Recommender")
    st.caption("You're building an AI-powered college match app. Let's get to know you and your vision.")
    st.divider()

    with st.form("setup_form"):
        st.markdown("### Step 1: About You")
        name = st.text_input("Your name:", placeholder="First name is fine")

        st.markdown("### Step 2: Your User")
        st.caption("Be specific — the more real your user feels, the better your app will be.")
        target_user = st.text_area(
            "Who is your app for?",
            placeholder="e.g. A 17-year-old junior who has strong EC's but is overwhelmed by the number of college options and doesn't know where she actually fits.",
            height=80,
        )

        st.markdown("### Step 3: The Problem You're Solving")
        st.caption("What gap does your app fill? Why can't they just Google it?")
        problem = st.text_area(
            "What problem does your app solve?",
            placeholder="e.g. Students apply based on rankings alone and end up at schools that don't fit their actual goals, budget, or personality. A recommendation engine can surface hidden-fit schools they'd never find on their own.",
            height=80,
        )

        st.markdown("### Step 4: App Tone")
        tone = st.radio(
            "How should your app communicate with users?",
            TONE_OPTIONS,
            horizontal=True,
        )

        submitted = st.form_submit_button("Create My Project →", type="primary", use_container_width=True)

    if submitted:
        if not name:
            st.error("Please enter your name.")
            return
        if not target_user or not problem:
            st.error("Please fill in both the target user and problem fields.")
            return

        student_data = {
            "name": name,
            "project_type": "College Recommender",
            "target_user": target_user,
            "problem": problem,
            "tone": tone,
            "features": json.dumps([]),
            "week_progress": json.dumps({}),
            "week1_data": json.dumps({}),
            "week2_data": json.dumps({}),
            "week3_data": json.dumps({}),
            "week4_data": json.dumps({}),
            "config": json.dumps({
                "app_title": "My College Match Finder",
                "intro_text": "Tell us about yourself — we'll find your best-fit colleges.",
                "recommendation_categories": ["Safety", "Match", "Reach"],
            }),
        }

        student_id = upsert_student(student_data)
        st.session_state.student_id = student_id

        st.success(f"Project created! Welcome, {name}! 🎉")
        st.markdown("---")
        st.markdown("### 🤖 AI Coach — Initial Feedback on Your Idea")
        with st.spinner("Analyzing your idea..."):
            feedback = ai_refine_idea("College Recommender", problem, target_user, [])
        st.info(feedback)
        st.markdown("---")
        if st.button("Go to My Project Dashboard →", type="primary", use_container_width=True):
            st.session_state.page = "project"
            st.rerun()
