import streamlit as st
from storage import get_student, save_week_data, mark_week_complete
from ui_components import week_header, challenge_box, ai_feedback_panel, complete_week_button
from openai_utils import ai_week1_feedback
from code_generator import generate_app_code
from code_runner import run_code

def render():
    student_id = st.session_state.get("student_id")
    if not student_id:
        st.warning("No student selected.")
        return

    student = get_student(student_id)
    if not student:
        st.error("Student not found.")
        return

    week1_done = student.get("week_progress", {}).get("week1", False)
    week_header(1, "Problem & User Thinking", 
                "Define who your app is for, what problem it solves, and why recommendations are valuable.",
                week1_done)

    existing = student.get("week1_data", {})

    st.markdown("### 🎯 Week 1 Goals")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
- Define a specific, real user for your app
- Write a clear problem statement
- Explain why recommendations (not search) are the right solution
- Identify what makes your recommendation trustworthy
        """)
    with col2:
        with st.container(border=True):
            st.markdown("**Your Project**")
            st.markdown(f"**Type:** {student['project_type']}")
            st.markdown(f"**Target User:** {student.get('target_user','Not defined')}")
            st.markdown(f"**Problem:** {student.get('problem','Not defined')}")

    st.divider()

    st.markdown("### 📝 Week 1 Tasks")

    with st.expander("Task 1: Write Your Problem Statement", expanded=not existing.get("problem_statement")):
        st.caption("A strong problem statement is specific, real, and explains WHY this is a problem—not just what it is.")
        st.info(f"**Your original problem:** {student.get('problem','Not set yet')}")
        problem_statement = st.text_area(
            "Refined Problem Statement (make it more specific and vivid):",
            value=existing.get("problem_statement", student.get("problem", "")),
            height=100,
            key="w1_problem",
            placeholder="e.g. High school juniors spend an average of 40+ hours researching colleges, yet 40% feel their final choice doesn't truly fit them academically or culturally."
        )
        st.caption("💡 Tip: Add a specific statistic, person, or scenario to make it real.")

    with st.expander("Task 2: Describe Your User Persona", expanded=not existing.get("user_persona")):
        st.caption("A user persona is a specific, realistic description of the person your app helps. Give them a name, situation, and goal.")
        user_persona = st.text_area(
            "Your User Persona:",
            value=existing.get("user_persona", student.get("target_user", "")),
            height=100,
            key="w1_persona",
            placeholder="e.g. Marcus is a junior at a mid-size suburban high school. He has a 3.7 GPA and wants to study computer science, but feels overwhelmed by 200+ college options. He's worried about cost but also wants campus life..."
        )
        st.caption("💡 Tip: Include name, grade, goals, and fears. Make them feel real.")

    with st.expander("Task 3: Why Are Recommendations the Right Solution?", expanded=not existing.get("why_recommendations")):
        st.caption("Explain why a recommendation engine is better than just Googling or reading rankings. What can your app do that search can't?")
        why_recommendations = st.text_area(
            "Why recommendations work for this problem:",
            value=existing.get("why_recommendations", ""),
            height=80,
            key="w1_why",
            placeholder="e.g. Search gives you 100 results with no personalization. My app weighs your unique academic profile, budget, and culture preferences to surface colleges you'd actually love—not just ones that are famous."
        )

    st.divider()
    st.markdown("### 🎯 Healthy Challenges")
    challenge_response = challenge_box(
        "Make It More Specific",
        "Read your problem statement again. Can you make it even more specific? Add a number, a real situation, or a quote from a student who has this problem.",
        "w1_challenge1"
    )

    challenge2_response = challenge_box(
        "Find the Weak Spot",
        "What's the weakest part of your current idea? Is it unclear who benefits? Is the problem vague? Write down your honest self-critique.",
        "w1_challenge2"
    )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Week 1 Progress", use_container_width=True):
            data = {
                "problem_statement": st.session_state.get("w1_problem", existing.get("problem_statement","")),
                "user_persona": st.session_state.get("w1_persona", existing.get("user_persona","")),
                "why_recommendations": st.session_state.get("w1_why", existing.get("why_recommendations","")),
                "challenge_response": challenge_response,
                "challenge2_response": challenge2_response,
            }
            save_week_data(student_id, "week1", data)
            st.success("Week 1 progress saved!")
            st.rerun()

    with col2:
        if st.button("🤖 Get AI Coach Feedback", use_container_width=True):
            ps = st.session_state.get("w1_problem", existing.get("problem_statement",""))
            up = st.session_state.get("w1_persona", existing.get("user_persona",""))
            wr = st.session_state.get("w1_why", existing.get("why_recommendations",""))
            if not ps or not up:
                st.warning("Please fill in at least your problem statement and user persona first.")
            else:
                with st.spinner("Your AI coach is reviewing your work..."):
                    feedback = ai_week1_feedback(ps, up, wr)
                st.session_state["w1_ai_feedback"] = feedback

    if "w1_ai_feedback" in st.session_state:
        ai_feedback_panel(st.session_state["w1_ai_feedback"])

    st.divider()

    # ── Live Code Preview ──────────────────────────────────────────────────────
    with st.expander("📟 My Code So Far  ← open to see your Week 1 in code", expanded=True):
        st.caption("Your answers above are already in this Python script. Run it to confirm it works. Complete Week 2 to see your recommendation logic added.")
        # Rebuild student with current unsaved values so preview is live
        preview_student = get_student(student_id) or {}
        preview_student["week1_data"] = {
            "problem_statement": st.session_state.get("w1_problem", existing.get("problem_statement", "")),
            "user_persona":      st.session_state.get("w1_persona", existing.get("user_persona", "")),
            "why_recommendations": st.session_state.get("w1_why", existing.get("why_recommendations", "")),
        }
        generated = generate_app_code(preview_student)
        st.code(generated, language="python")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("▶ Run This Code", key="run_w1", use_container_width=True, type="primary"):
                with st.spinner("Running..."):
                    out = run_code(generated)
                st.session_state["w1_run_result"] = out
        with col_b:
            st.download_button("⬇ Download .py File", data=generated,
                               file_name="my_app_week1.py", mime="text/plain",
                               use_container_width=True)
        if "w1_run_result" in st.session_state:
            result = st.session_state["w1_run_result"]
            st.markdown("**Output:**")
            if result.get("timed_out"):
                st.error(result["stderr"])
            elif result["exit_code"] == 0:
                st.success("✅ Code ran successfully!")
                st.code(result["stdout"] or "(no output)", language="text")
            else:
                st.warning("⚠️ Code ran with errors:")
                st.code(result["stderr"] or result["stdout"] or "(no output)", language="text")

    st.divider()
    if complete_week_button("week1"):
        data = {
            "problem_statement": st.session_state.get("w1_problem", existing.get("problem_statement","")),
            "user_persona": st.session_state.get("w1_persona", existing.get("user_persona","")),
            "why_recommendations": st.session_state.get("w1_why", existing.get("why_recommendations","")),
            "challenge_response": challenge_response,
            "challenge2_response": challenge2_response,
        }
        save_week_data(student_id, "week1", data)
        mark_week_complete(student_id, "week1")
        st.success("Week 1 complete! 🎉 Move on to Week 2.")
        st.balloons()
        st.rerun()
