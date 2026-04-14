import streamlit as st

def week_header(week_num: int, title: str, subtitle: str, is_complete: bool = False):
    status = "✅ Complete" if is_complete else f"📅 Week {week_num}"
    st.markdown(f"## {status} — {title}")
    st.caption(subtitle)
    st.divider()

def challenge_box(title: str, description: str, key: str, existing_value: str = ""):
    with st.container(border=True):
        st.markdown(f"**🎯 Healthy Challenge: {title}**")
        st.caption(description)
        # If there's a saved value and session_state hasn't been populated yet, seed it
        if existing_value and key not in st.session_state:
            st.session_state[key] = existing_value
        response = st.text_area("Your response:", key=key, height=80,
                                placeholder="Write your thinking here...")
        return response

def score_bar(label: str, score: float, max_score: float = 100):
    pct = score / max_score
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(f"**{label}**")
    with col2:
        st.progress(pct, text=f"{int(score)}/{int(max_score)}")

def recommendation_card(title: str, score: float, category: str, reasons: list, details: dict = None):
    category_colors = {"Safety": "🟢", "Match": "🔵", "Reach": "🔴", 
                       "Best Fit": "🟢", "Strong Option": "🔵", "Backup Choice": "🔴",
                       "Primary Strategy": "🟢", "Secondary Strategy": "🔵", "Backup Method": "🔴"}
    emoji = category_colors.get(category, "⭐")

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {title}")
            st.caption(f"{emoji} {category}")
        with col2:
            st.metric("Match Score", f"{int(score)}%")

        if reasons:
            st.markdown("**Why this fits you:**")
            for r in reasons:
                st.markdown(f"- ✓ {r}")

        if details:
            with st.expander("More details"):
                for k, v in details.items():
                    st.markdown(f"**{k}:** {v}")

def ai_feedback_panel(feedback_text: str, is_loading: bool = False):
    with st.container(border=True):
        st.markdown("**🤖 AI Coach Feedback**")
        if is_loading:
            st.info("Getting AI feedback...")
        elif feedback_text:
            st.markdown(feedback_text)
        else:
            st.caption("Complete the section above and click 'Get AI Feedback' to receive coaching.")

def progress_summary(week_progress: dict):
    weeks = ["week1", "week2", "week3", "week4"]
    labels = ["Problem & User", "Logic & Design", "Code Editing", "Testing & Pitch"]
    cols = st.columns(4)
    for i, (week, label) in enumerate(zip(weeks, labels)):
        with cols[i]:
            done = week_progress.get(week, False)
            st.metric(
                label=f"Week {i+1}",
                value="✅ Done" if done else "⏳ In Progress",
                delta=label
            )

def editable_code_block(section_name: str, description: str, default_value: str, key: str):
    st.markdown(f"**📝 {section_name}**")
    st.caption(description)
    col1, col2 = st.columns([4, 1])
    with col1:
        edited = st.text_area("", value=default_value, key=key, height=100, label_visibility="collapsed")
    with col2:
        explain_btn = st.button("💡 Explain", key=f"explain_{key}")
    return edited, explain_btn

def info_card(title: str, content: str, icon: str = "ℹ️"):
    with st.container(border=True):
        st.markdown(f"{icon} **{title}**")
        st.markdown(content)

def complete_week_button(week_key: str, label: str = "Mark Week Complete ✅"):
    return st.button(label, type="primary", use_container_width=True, key=f"complete_{week_key}")
