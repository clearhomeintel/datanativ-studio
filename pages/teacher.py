import streamlit as st
from storage import get_all_students, get_student
from ui_components import info_card

def render():
    st.markdown("## 🏫 Teacher Dashboard")
    st.caption("Overview of all student projects and weekly progress")
    st.divider()

    students = get_all_students()

    if not students:
        st.info("No student projects yet. Students create projects from the Home page.")
        return

    total = len(students)
    completed_all = sum(1 for s in students if all(s.get("week_progress",{}).get(w,False) for w in ["week1","week2","week3","week4"]))
    avg_weeks = sum(sum(1 for w in ["week1","week2","week3","week4"] if s.get("week_progress",{}).get(w,False)) for s in students) / total if total else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Students", total)
    with col2:
        st.metric("Avg Weeks Complete", f"{avg_weeks:.1f}/4")
    with col3:
        st.metric("Fully Complete", completed_all)

    st.divider()

    project_type_counts = {}
    for s in students:
        pt = s.get("project_type","Unknown")
        project_type_counts[pt] = project_type_counts.get(pt,0) + 1

    st.markdown("### Project Type Distribution")
    cols = st.columns(min(len(project_type_counts), 4))
    for i, (pt, count) in enumerate(project_type_counts.items()):
        with cols[i % 4]:
            st.metric(pt.split(" ")[0], count)

    st.divider()

    st.markdown("### All Student Projects")

    search = st.text_input("Search by student name or project type:", placeholder="Type to filter...")

    filtered = students
    if search:
        search_lower = search.lower()
        filtered = [s for s in students if search_lower in s.get("name","").lower() or search_lower in s.get("project_type","").lower()]

    for student in filtered:
        progress = student.get("week_progress", {})
        weeks_done = sum(1 for w in ["week1","week2","week3","week4"] if progress.get(w, False))
        week_badges = "".join(["✅" if progress.get(f"week{i+1}",False) else "⬜" for i in range(4)])
        features = student.get("features", [])
        features_str = ", ".join(features) if isinstance(features, list) else str(features)

        with st.expander(f"**{student['name']}** — {student['project_type']} | {weeks_done}/4 weeks {week_badges}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Project Type:** {student['project_type']}")
                st.markdown(f"**Tone:** {student.get('tone','')}")
                st.markdown(f"**Target User:** {student.get('target_user','Not defined')[:150]}")
                st.markdown(f"**Problem:** {student.get('problem','Not defined')[:150]}")
                if features_str:
                    st.markdown(f"**Features:** {features_str}")
            with col2:
                st.markdown(f"**Week 1 (Problem & User):** {'✅' if progress.get('week1') else '⏳'}")
                st.markdown(f"**Week 2 (Logic & Design):** {'✅' if progress.get('week2') else '⏳'}")
                st.markdown(f"**Week 3 (Code Editing):** {'✅' if progress.get('week3') else '⏳'}")
                st.markdown(f"**Week 4 (Test & Pitch):** {'✅' if progress.get('week4') else '⏳'}")

                week4 = student.get("week4_data", {})
                if week4.get("pitch"):
                    with st.container(border=True):
                        st.markdown("**📣 Final Pitch:**")
                        st.caption(week4["pitch"][:300] + ("..." if len(week4.get("pitch","")) > 300 else ""))

            week1 = student.get("week1_data", {})
            if week1.get("problem_statement"):
                st.markdown(f"**Problem Statement:** {week1['problem_statement'][:200]}")

            week4 = student.get("week4_data", {})
            if week4.get("feedback_notes"):
                st.markdown(f"**Test Feedback:** {week4['feedback_notes'][:200]}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"View {student['name']}'s App Preview", key=f"view_{student['id']}"):
                    st.session_state.student_id = student["id"]
                    st.session_state.page = "preview"
                    st.rerun()
            with col2:
                if st.button(f"Switch to {student['name']}", key=f"switch_{student['id']}"):
                    st.session_state.student_id = student["id"]
                    st.session_state.page = "project"
                    st.rerun()

    st.divider()

    if st.button("📥 Export Summary (copy below)", use_container_width=True):
        summary_lines = [f"DataNativ Studio — Class Summary\n{'='*40}"]
        for s in students:
            progress = s.get("week_progress", {})
            weeks_done = sum(1 for w in ["week1","week2","week3","week4"] if progress.get(w, False))
            summary_lines.append(f"\n{s['name']} | {s['project_type']} | {weeks_done}/4 weeks")
            week4 = s.get("week4_data", {})
            if week4.get("pitch"):
                summary_lines.append(f"  Pitch: {week4['pitch'][:150]}...")

        st.code("\n".join(summary_lines), language=None)
