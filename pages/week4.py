import streamlit as st
from storage import get_student, save_week_data, mark_week_complete
from ui_components import week_header, complete_week_button
from code_generator import generate_app_code, _sanitize_action_plan_prompt
from code_runner import run_code

GAP_PLACEHOLDER = """\
If my SAT score is more than 200 points below the school's median, that is a gap.
If my GPA is 0.3 or more below the school's expected GPA for its selectivity level, that is a gap.
If I haven't taken any AP or IB courses and the school's academic selectivity is above 80, that is a gap.
If the school's acceptance rate is below 10% and my match score is below 70, that is a reach gap."""

ACTION_PLAN_PROMPT_PLACEHOLDER = """\
A student has a {match_score}% match with {college_name} (acceptance rate: {acceptance_rate}, region: {region}).

Their identified profile gaps are: {gaps}.

Based on these gaps, identify 3-5 specific activities and improvements the student can work on over the next 60-90 days to close these gaps and strengthen their application. Focus on realistic, local activities — study groups, clubs, online courses, community projects — not just generic advice."""

PROMPT_VARIABLES = [
    ("{college_name}",    "The name of the matched college",             "MIT"),
    ("{match_score}",     "The student's match score (0–100)",           "87"),
    ("{acceptance_rate}", "The college's acceptance rate",               "4%"),
    ("{region}",          "Geographic region of the college",            "Northeast"),
    ("{gaps}",            "Comma-separated list of identified gaps",     "SAT gap (145 pts), Rigor gap"),
]

SAMPLE_DATA = {
    "college_name":    "MIT",
    "match_score":     "87",
    "acceptance_rate": "4%",
    "region":          "Northeast",
    "gaps":            "SAT gap (145 pts below median), Rigor gap (only 3 AP courses)",
}


def render():
    student_id = st.session_state.get("student_id")
    if not student_id:
        st.warning("No student selected.")
        return
    student = get_student(student_id)
    if not student:
        st.error("Student not found.")
        return

    week4_done = student.get("week_progress", {}).get("week4", False)
    week_header(4, "Gap Analysis, Action Plan & Final App",
                "Identify profile gaps, write the AI prompt that drives your action plan, and compile your complete app.",
                week4_done)

    ex = student.get("week4_data", {})

    st.markdown("### 🎯 Week 4 Goals")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
- Define what counts as a "gap" between your profile and a recommended school
- Write a prompt that tells your app how to generate personalized improvement plans
- See how the same prompting skills from Week 3 apply to action plan logic
- Compile all four weeks of code into one complete, runnable app
        """)
    with c2:
        with st.container(border=True):
            st.markdown("**The full app arc**")
            st.caption("Week 4 is where it all comes together:")
            st.markdown("🔍 **Gap analysis** — shows users where they fall short")
            st.markdown("🤖 **Prompt-driven plans** — your prompt becomes the app's planning intelligence")
            st.markdown("🎓 **Final app** — all four weeks compiled into one runnable Python script")

    st.divider()
    st.markdown("### 📝 Week 4 Tasks")

    tab1, tab2, tab3 = st.tabs([
        "🔍 Task 1 — Gap Analysis",
        "🤖 Task 2 — Action Plan Prompt",
        "🎓 Task 3 — Final App Assembly",
    ])

    # ─── TAB 1: Gap Analysis Designer ────────────────────────────────────────
    with tab1:
        st.markdown("**What is a gap?**")
        st.info(
            "A 'gap' is a place where your current profile falls short of what a recommended school expects. "
            "Your app will analyze each result and show the user their gaps — not to discourage them, "
            "but to give them a concrete target to work toward."
        )

        st.markdown("**Define your gap rules in plain English:**")
        st.caption(
            "Each rule should describe one specific situation where a gap exists. "
            "Start each rule with 'If ...'"
        )

        gap_rules = st.text_area(
            "Gap rules:",
            value=ex.get("gap_rules_text", GAP_PLACEHOLDER),
            height=200,
            key="w4_gaps",
            label_visibility="collapsed",
        )

        parsed_gaps = _parse_gap_rules(gap_rules)
        if parsed_gaps:
            st.markdown(f"**✅ {len(parsed_gaps)} gap rule(s) detected**")
            for g in parsed_gaps:
                st.markdown(f"  • {g}")
        elif gap_rules.strip():
            st.caption("Write one rule per line. Start each with 'If ...'")

        with st.expander("💡 What kinds of gaps should you define?"):
            st.markdown("""
**SAT gap:** Your score vs. the school's median
**GPA gap:** Your GPA vs. what the school expects for its selectivity tier
**Rigor gap:** Not enough AP/IB courses for a highly selective school
**Acceptance rate gap:** School is a reach (very low acceptance rate) given your profile
**Extracurricular gap:** School values strong ECs but you haven't highlighted them
            """)

    # ─── TAB 2: AI-Powered Action Plan Prompt ────────────────────────────────
    with tab2:
        st.markdown("## You're not writing the plan — you're writing the instructions.")
        st.markdown(
            "In Week 3 you wrote a prompt that generated a chart. "
            "Now you'll write a prompt that tells your app **how to generate a personalized improvement plan** "
            "for every student, for every college they matched with."
        )

        with st.expander("🤔 What's the difference between a plan and a prompt?", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    st.markdown("❌ **Old approach — you write the plan:**")
                    st.caption("\"Focus on SAT prep. Take practice tests twice a week.\"")
                    st.caption("")
                    st.caption("**Problem:** Same advice for every student, every college. No context. Not personalized.")
            with col2:
                with st.container(border=True):
                    st.markdown("✅ **Your approach — you write the instructions:**")
                    st.caption("\"Given that this student has a {match_score}% match and gaps: {gaps}, suggest specific activities in {region}...\"")
                    st.caption("")
                    st.caption("**Result:** Every student gets a plan built from their actual gaps and the school's real data.")

        st.markdown("---")
        st.markdown("### Available variables — your app will fill these in for each student:")
        var_cols = st.columns(len(PROMPT_VARIABLES))
        for i, (var, desc, sample) in enumerate(PROMPT_VARIABLES):
            with var_cols[i]:
                with st.container(border=True):
                    st.code(var, language="text")
                    st.caption(desc)
                    st.caption(f"e.g. `{sample}`")

        st.markdown("---")
        st.markdown("**Write your action plan prompt:**")
        st.caption(
            "Use the variables above. Your prompt becomes the logic that drives your app's personalized plans. "
            "The more specific and thoughtful your prompt, the better your plans will be."
        )

        saved_prompt = ex.get("action_plan_prompt", "")
        action_plan_prompt = st.text_area(
            "Action plan prompt:",
            value=saved_prompt,
            height=180,
            key="w4_action_prompt",
            placeholder=ACTION_PLAN_PROMPT_PLACEHOLDER,
            label_visibility="collapsed",
        )

        # Live preview with sample data
        if action_plan_prompt.strip():
            sanitized = _sanitize_action_plan_prompt(action_plan_prompt)
            if sanitized != action_plan_prompt:
                st.warning(
                    "⚠️ **Bracket typo auto-fixed!** Your prompt had mismatched brackets "
                    "(like `(var)` or `[var}` instead of `{var}`). "
                    "Here's what your app will actually use:"
                )
                st.code(sanitized, language="text")
            try:
                preview = sanitized.format(**SAMPLE_DATA)
                st.markdown("**Live preview — this prompt gets filled in and sent to GPT for each student:**")
                with st.container(border=True):
                    st.markdown(f"*Sample prompt sent to AI for MIT (87% match):*")
                    st.markdown(preview)
                    st.caption("↑ GPT reads this and writes a personalized 3–5 step action plan for the student.")
            except KeyError as e:
                st.warning(f"Unknown variable: `{{{e}}}` — check the variable names above and try again.")

        st.markdown("---")
        with st.expander("💡 Connecting this to what you learned in Week 3"):
            st.markdown("""
**In Week 3**, you learned four prompting techniques:
- Zero-Shot: just describe what you want
- Role Prompting: "act as an advisor who..."
- Few-Shot: show an example first
- Chain-of-Thought: "Step 1: look at gaps. Step 2: for each gap..."

**All four techniques work here too.**

Try rewriting your prompt using Role Prompting:
> *"Act as a college guidance counselor. A student has a {match_score}% match with {college_name}..."*

Or Chain-of-Thought:
> *"Step 1: Look at the gaps: {gaps}. Step 2: For each gap, identify the type of improvement needed. Step 3: Suggest activities in {region} that address that specific gap."*

**The same skill — writing good prompts — applies across every part of your app.**
            """)

        with st.expander("💡 Tips for writing a great action plan prompt"):
            st.markdown("""
- **Reference the gaps directly:** `{gaps}` makes the plan specific to the student
- **Use the region:** `{region}` makes it locally relevant (Northeast vs South vs Midwest matters for clubs, programs, etc.)
- **Mention the match score:** `{match_score}%` tells the system how much work is needed
- **Specify timeframe:** "60-90 days" gives structure
- **Ask for concrete actions:** "specific activities", "online courses", "local programs" is better than "work harder"
- **Consider tone:** Is your app encouraging? Realistic? Urgent? Use language that matches.
            """)

    # ─── TAB 3: Final Assembly ────────────────────────────────────────────────
    with tab3:
        st.markdown("**Compile your complete app — all four weeks in one script.**")
        st.caption(
            "This is the finished product: a standalone Python recommendation engine that "
            "includes your inputs, scoring algorithm, presentation layer, gap analysis, and action plan generator."
        )

        weeks_done = student.get("week_progress", {})
        done_count = sum(1 for w in ["week1", "week2", "week3", "week4"] if weeks_done.get(w, False))

        if done_count < 3:
            st.warning(f"You've completed {done_count}/4 weeks. The more weeks you finish, the richer your final app will be — but you can compile anytime.")

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns(4)
            for col, wk, label in [
                (col1, "week1", "Week 1\nProblem"),
                (col2, "week2", "Week 2\nInputs"),
                (col3, "week3", "Week 3\nDisplay"),
                (col4, "week4", "Week 4\nGaps"),
            ]:
                with col:
                    if weeks_done.get(wk, False):
                        st.success(f"✅ {label}")
                    else:
                        st.warning(f"⬜ {label}")

        st.divider()

        if st.button("🎓 Build My Complete App", type="primary", use_container_width=True):
            full_student = get_student(student_id) or {}
            full_student["week4_data"] = _collect(ex)
            with st.spinner("Compiling all four weeks into one app..."):
                final_code = generate_app_code(full_student)
                result = run_code(final_code)
            st.session_state["w4_final_code"] = final_code
            st.session_state["w4_final_result"] = result
            st.rerun()

        if "w4_final_code" in st.session_state:
            final_code = st.session_state["w4_final_code"]
            result = st.session_state.get("w4_final_result", {})

            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    "⬇ Download Complete App (.py)",
                    data=final_code,
                    file_name="my_college_recommender_final.py",
                    mime="text/plain",
                    use_container_width=True,
                    type="primary",
                )
            with col_b:
                line_count = len(final_code.split("\n"))
                st.metric("Lines of code", f"{line_count:,}")

            if result.get("timed_out"):
                st.error("App timed out while running.")
            elif result.get("exit_code") == 0:
                st.success("✅ Complete app runs successfully!")
                st.code(result.get("stdout", ""), language="text")
            else:
                st.warning("Ran with errors — check the code below.")
                if result.get("stderr"):
                    st.code(result["stderr"], language="text")

            st.markdown("**Complete App Code:**")
            st.code(final_code, language="python")

    st.divider()

    # ── Live Code Panel ────────────────────────────────────────────────────────
    with st.expander("📟 My Code So Far", expanded=True):
        st.caption("All four weeks compiled into one growing script. Gap analysis and action plan sections appear once configured above.")
        preview_student = get_student(student_id) or {}
        preview_student["week4_data"] = _collect(ex)
        generated = generate_app_code(preview_student)
        st.code(generated, language="python")

        ca, cb = st.columns(2)
        with ca:
            if st.button("▶ Run This Code", key="run_w4_preview", use_container_width=True, type="primary"):
                with st.spinner("Running full app with gap analysis..."):
                    result = run_code(generated)
                st.session_state["w4_preview_result"] = result
        with cb:
            st.download_button(
                "⬇ Download .py", data=generated,
                file_name="my_app_week4.py", mime="text/plain",
                use_container_width=True,
            )
        if "w4_preview_result" in st.session_state:
            r = st.session_state["w4_preview_result"]
            if r.get("timed_out"):
                st.error(r["stderr"])
            elif r["exit_code"] == 0:
                st.success("✅ Full app is working!")
                st.code(r["stdout"] or "(no output)", language="text")
            else:
                st.warning("⚠️ Ran with errors")
                if r["stderr"]:
                    st.code(r["stderr"], language="text")

    st.divider()

    if st.button("💾 Save Week 4 Progress", use_container_width=True):
        save_week_data(student_id, "week4", _collect(ex))
        st.success("Week 4 progress saved!")
        st.rerun()

    st.divider()
    if complete_week_button("week4", "🎓 Mark Project Complete — I've Built My App!"):
        save_week_data(student_id, "week4", _collect(ex))
        mark_week_complete(student_id, "week4")
        st.success("🎓 Bootcamp complete! You just built a real AI recommendation engine from scratch. Amazing work!")
        st.balloons()
        st.rerun()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _collect(ex: dict) -> dict:
    return {
        "gap_rules_text":     st.session_state.get("w4_gaps",          ex.get("gap_rules_text", "")),
        "action_plan_prompt": st.session_state.get("w4_action_prompt", ex.get("action_plan_prompt", "")),
    }


def _parse_gap_rules(text: str) -> list:
    rules = []
    for line in (text or "").split("\n"):
        stripped = line.strip()
        if stripped.lower().startswith("if "):
            rules.append(stripped)
    return rules
