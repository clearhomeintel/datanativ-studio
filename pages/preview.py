"""
preview.py — App Preview for DataNativ Studio.
Executes the student's generated Python code as a module and renders results
as a native Streamlit UI — cards, metrics, colors, gap analysis, visualization.
"""
import io
import contextlib
import re
import streamlit as st
from storage import get_student, save_week_data
from code_generator import generate_app_code


# ── Helpers ────────────────────────────────────────────────────────────────────

def _std_enabled(student: dict, key: str) -> bool:
    return bool(student.get("week2_data", {}).get(f"std_{key}_enabled", False))


def _get_passion_questions(student: dict) -> list:
    pqs = student.get("week2_data", {}).get("passion_questions", [])
    return [q for q in pqs if q.get("question", "").strip()]


def _exec_generated_code(code: str) -> dict | None:
    """
    Exec the generated code in an isolated namespace.
    Returns the namespace dict so we can call functions from it.
    Prevents the __main__ block from running.
    """
    # Prevent the if __name__ == "__main__" block from firing
    code_no_main = re.sub(
        r'if __name__\s*==\s*["\']__main__["\']:.*',
        '# (main block disabled for preview)',
        code,
        flags=re.DOTALL,
    )
    namespace = {"__name__": "datanativ_preview"}
    try:
        exec(code_no_main, namespace)   # noqa: S102
        return namespace
    except Exception as e:
        return {"__exec_error__": str(e)}


def _category_emoji(cat: str) -> str:
    return {"Safety": "🟢", "Match": "🟡", "Reach": "🔴"}.get(cat, "⚪")


def _web_search_local(query: str, max_results: int = 4) -> list[str]:
    """
    Fetch real search result snippets from DuckDuckGo HTML for a given query.
    Returns a list of plain-text snippet strings.
    """
    import urllib.request, urllib.parse, re
    try:
        q = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={q}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
        )
        html = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", errors="ignore")
        snippets = re.findall(r'result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
        clean = []
        for s in snippets[:max_results]:
            text = re.sub(r'<[^>]+>', '', s).strip()
            text = re.sub(r'&#x27;', "'", text)
            text = re.sub(r'&amp;', "&", text)
            text = re.sub(r'&quot;', '"', text)
            if text:
                clean.append(text)
        return clean
    except Exception:
        return []


def _build_local_context(location: str, interests: list[str], gaps: list[str]) -> str:
    """
    Run targeted web searches and return a block of real local search results
    for GPT to reference when writing the action plan.
    """
    if not location.strip():
        return ""

    searches = []

    # Academic gap searches
    if any("gpa" in g.lower() or "academic" in g.lower() for g in gaps):
        searches.append(f"tutoring centers academic programs high school {location}")
    if any("sat" in g.lower() or "score" in g.lower() for g in gaps):
        searches.append(f"SAT prep classes test prep {location}")
    if any("rigor" in g.lower() or "ap" in g.lower() or "course" in g.lower() for g in gaps):
        searches.append(f"AP course prep online community college dual enrollment {location}")

    # Interest-based searches
    for interest in interests[:2]:
        searches.append(f"{interest} club program workshop high school {location}")

    # General fall-back
    if not searches:
        searches.append(f"high school extracurricular programs clubs {location}")
    searches.append(f"internship volunteer opportunity high school student {location}")

    all_snippets = []
    for q in searches[:4]:          # cap at 4 searches to stay fast
        snippets = _web_search_local(q, max_results=3)
        if snippets:
            all_snippets.append(f"Search: {q}")
            for s in snippets:
                all_snippets.append(f"  → {s[:180]}")

    return "\n".join(all_snippets) if all_snippets else ""


def _generate_combined_plan(
    results: list,
    gaps_per_college: list,          # [(college_name, score, [gap strings]), ...]
    user_inputs: dict,
    passion_questions: list,
    student_location: str,
    action_plan_prompt: str,
) -> str:
    """
    Call GPT once to produce a single personalized action plan covering all matched colleges.
    Searches the web for real local opportunities before calling GPT.
    """
    import os
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

        # Build colleges + gaps summary
        college_lines = []
        all_gaps: list[str] = []
        for cname, score, gaps in gaps_per_college:
            gap_text = ", ".join(gaps) if gaps else "no major gaps"
            college_lines.append(f"  • {cname} ({score}% match) — gaps: {gap_text}")
            all_gaps.extend(gaps)
        colleges_block = "\n".join(college_lines) if college_lines else "  • No colleges listed"

        # Build passion answers block + extract interest keywords for search
        passion_lines = []
        interest_keywords: list[str] = []
        for q in passion_questions:
            qtext  = q.get("question", "")
            answer = user_inputs.get(qtext, "").strip()
            if qtext and answer:
                passion_lines.append(f"  Q: {qtext}\n  A: {answer}")
                # Pull first few words of answer as interest keyword
                words = answer.split()
                if len(words) >= 2:
                    interest_keywords.append(" ".join(words[:4]))
        passion_block = (
            "\n".join(passion_lines) if passion_lines
            else "  (No passion question answers provided)"
        )

        location = student_location.strip() or ""

        # ── Real web search for local opportunities ────────────────────────────
        local_context = ""
        if location:
            local_context = _build_local_context(location, interest_keywords, all_gaps)

        local_block = (
            f"\n\nReal local search results for {location} — reference SPECIFIC programs, "
            f"centers, or organizations found below in your plan:\n{local_context}"
            if local_context else ""
        )

        system_msg = (
            "You are a college guidance counselor writing a concise, encouraging, "
            "and highly specific action plan for a high school student. "
            "You have been given REAL web search results showing actual local programs, "
            "tutoring centers, clubs, and opportunities near the student. "
            "You MUST reference specific real names (organizations, centers, programs) from the search results. "
            "Write a single action plan with 4–6 numbered steps. "
            "Each step should name a REAL, SPECIFIC resource or program from the search results. "
            "Use an encouraging, direct tone. Keep total length under 400 words."
        )

        user_msg = (
            f"Student's current location: {location or 'not specified'}\n\n"
            f"Matched colleges and profile gaps:\n{colleges_block}\n\n"
            f"Student's personal interests:\n{passion_block}"
            f"{local_block}\n\n"
            f"Planning framework (use this as the basis for the plan):\n\"{action_plan_prompt}\"\n\n"
            "Write the action plan now, referencing real local resources by name."
        )

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=600,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not generate plan: {e}"


def _render_native_chart(results: list, viz_type: str):
    """Render the student's chosen visualization as a real Streamlit chart."""
    import pandas as pd
    import altair as alt

    if not results:
        return

    # Build a tidy DataFrame from results
    rows = []
    for r in results:
        net = r.get("tuition", 0) - r.get("avg_financial_aid", 0)
        rows.append({
            "College":         r.get("name", ""),
            "Match Score":     r.get("score", 0),
            "Acceptance Rate": round(r.get("acceptance_rate", 0) * 100, 1),
            "Net Cost ($k)":   round(net / 1000, 1),
            "SAT Median":      r.get("sat_range", 0) if isinstance(r.get("sat_range"), (int, float)) else 0,
            "Category":        r.get("category", "Match"),
        })
    df = pd.DataFrame(rows)

    cat_colors = {"Safety": "#22c55e", "Match": "#eab308", "Reach": "#ef4444"}

    if viz_type == "bar" or viz_type not in ("table", "comparison", "cost", "tier_summary"):
        # Horizontal bar chart of match scores
        chart = (
            alt.Chart(df)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                x=alt.X("Match Score:Q", scale=alt.Scale(domain=[0, 100]), title="Match Score (%)"),
                y=alt.Y("College:N", sort="-x", title=""),
                color=alt.Color(
                    "Category:N",
                    scale=alt.Scale(
                        domain=list(cat_colors.keys()),
                        range=list(cat_colors.values()),
                    ),
                    legend=alt.Legend(title="Category"),
                ),
                tooltip=["College", "Match Score", "Category", "Acceptance Rate"],
            )
            .properties(height=max(120, len(df) * 60))
        )
        st.altair_chart(chart, use_container_width=True)

    elif viz_type == "table":
        display_df = df[["College", "Match Score", "Category", "Acceptance Rate", "Net Cost ($k)"]].copy()
        display_df["Acceptance Rate"] = display_df["Acceptance Rate"].apply(lambda x: f"{x}%")
        display_df["Net Cost ($k)"]   = display_df["Net Cost ($k)"].apply(lambda x: f"${x}k/yr")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    elif viz_type == "comparison":
        # Scatter: match score vs acceptance rate
        chart = (
            alt.Chart(df)
            .mark_circle(size=160)
            .encode(
                x=alt.X("Acceptance Rate:Q", title="Acceptance Rate (%)"),
                y=alt.Y("Match Score:Q", title="Match Score (%)", scale=alt.Scale(domain=[0, 100])),
                color=alt.Color(
                    "Category:N",
                    scale=alt.Scale(
                        domain=list(cat_colors.keys()),
                        range=list(cat_colors.values()),
                    ),
                ),
                tooltip=["College", "Match Score", "Acceptance Rate", "Category"],
                text=alt.Text("College:N"),
            )
            .properties(height=320)
        )
        labels = chart.mark_text(dy=-14, fontSize=12)
        st.altair_chart((chart + labels), use_container_width=True)

    elif viz_type == "cost":
        # Grouped bar: net cost per college
        chart = (
            alt.Chart(df)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
            .encode(
                x=alt.X("College:N", title=""),
                y=alt.Y("Net Cost ($k):Q", title="Estimated Net Cost ($k/yr)"),
                color=alt.Color(
                    "Category:N",
                    scale=alt.Scale(
                        domain=list(cat_colors.keys()),
                        range=list(cat_colors.values()),
                    ),
                ),
                tooltip=["College", "Net Cost ($k)", "Category"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart, use_container_width=True)

    elif viz_type == "tier_summary":
        # Donut / grouped bar by tier
        tier_counts = df.groupby("Category").size().reset_index(name="Count")
        chart = (
            alt.Chart(tier_counts)
            .mark_arc(innerRadius=60)
            .encode(
                theta=alt.Theta("Count:Q"),
                color=alt.Color(
                    "Category:N",
                    scale=alt.Scale(
                        domain=list(cat_colors.keys()),
                        range=list(cat_colors.values()),
                    ),
                ),
                tooltip=["Category", "Count"],
            )
            .properties(height=260)
        )
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.altair_chart(chart, use_container_width=True)
        with col_b:
            for _, row in tier_counts.iterrows():
                emoji = {"Safety": "🟢", "Match": "🟡", "Reach": "🔴"}.get(row["Category"], "⚪")
                st.metric(f"{emoji} {row['Category']}", f"{row['Count']} school(s)")


# ── Render ─────────────────────────────────────────────────────────────────────

def render():
    student_id = st.session_state.get("student_id")
    if not student_id:
        st.warning("No student selected.")
        return

    student = get_student(student_id)
    if not student:
        st.error("Student not found.")
        return

    config        = student.get("config", {})
    week2         = student.get("week2_data", {})
    week_progress = student.get("week_progress", {})
    passion_qs    = _get_passion_questions(student)
    has_engine    = bool(week2.get("std_gpa_enabled") or passion_qs)

    app_title = config.get("app_title", f"My {student.get('project_type','App')}")
    tagline   = student.get("problem", "Find your best match.")

    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown(f"# 👁️ App Preview — {app_title}")
    st.caption(
        "Experience your app as a real student would. "
        "Fill in the profile below and click **▶ Run My App** — "
        "results render as a real app with cards, metrics, and your custom visualization."
    )

    if not has_engine:
        st.warning(
            "⚠️ Your scoring engine isn't configured yet. "
            "Complete **Week 2** to enable inputs and scoring, then come back here."
        )
        return

    # Remind to save if any week is in progress
    unsaved_warning = (
        "💡 **Tip:** If you made changes in Week 2, 3, or 4 today, click **Save** "
        "on those pages before running the preview — the preview uses your last saved data."
    )
    st.info(unsaved_warning)

    st.divider()

    # ── App banner ─────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown(f"## {app_title}")
        st.caption(f"{tagline} — Built by **{student['name']}**")

    st.divider()

    # ── Input form ─────────────────────────────────────────────────────────────
    st.markdown("### 📝 Enter a Student Profile to Test")
    st.caption("Fill in the fields your app collects, then click Run My App.")

    with st.form("preview_form"):
        user_inputs: dict = {}

        # ── Current location ──────────────────────────────────────────────────
        st.markdown("#### 📍 Current Location")
        student_location = st.text_input(
            "City and state (used for local activity suggestions in your action plan):",
            placeholder="e.g. Austin, TX",
            key="preview_location",
        )

        academic_enabled = any(
            _std_enabled(student, k)
            for k in ["gpa", "sat", "act", "class_rank", "rigor"]
        )

        if academic_enabled:
            st.markdown("#### 📚 Academic Profile")
            c1, c2 = st.columns(2)
            with c1:
                if _std_enabled(student, "gpa"):
                    user_inputs["gpa"] = st.slider("GPA (weighted):", 2.0, 4.5, 3.5, step=0.1)
                if _std_enabled(student, "sat"):
                    user_inputs["sat"] = st.number_input("SAT Score:", 400, 1600, 1200, step=10)
                if _std_enabled(student, "act"):
                    user_inputs["act"] = st.number_input("ACT Score:", 1, 36, 27)
            with c2:
                if _std_enabled(student, "class_rank"):
                    user_inputs["class_rank"] = st.slider("Class Rank percentile (1 = top):", 1, 100, 20)
                if _std_enabled(student, "rigor"):
                    user_inputs["rigor"] = st.slider("AP/IB courses taken:", 0, 10, 4)

        if passion_qs:
            st.markdown("#### 💡 Your Passion Questions")
            st.caption("These are the questions you designed. Type a sample student answer for each.")
            for q in passion_qs:
                answer = st.text_area(
                    q["question"],
                    height=80,
                    key=f"preview_passion_{q.get('id','q')}",
                    placeholder="Type a sample student answer…",
                )
                user_inputs[q["question"]] = answer

        submitted = st.form_submit_button(
            "▶  Run My App",
            type="primary",
            use_container_width=True,
        )

    # ── Results ────────────────────────────────────────────────────────────────
    if submitted:
        st.divider()
        st.markdown(f"## 🎓 {app_title} — Results")
        st.caption("This is exactly what a student sees when they use your app.")

        code = generate_app_code(student)

        with st.spinner("Scoring 42 real colleges using your engine… (AI passion scoring may take a few seconds on first run)"):
            ns = _exec_generated_code(code)

        if ns is None or "__exec_error__" in ns:
            err = (ns or {}).get("__exec_error__", "Unknown error")
            st.error(f"Your code has an error: {err}")
            with st.expander("🐛 View Generated Code"):
                st.code(code, language="python")
            return

        recommend       = ns.get("recommend")
        format_headline = ns.get("format_headline", lambda rank, name, score, cat: f"#{rank} — {name} ({score}%)")
        show_fields     = ns.get("SHOW_FIELDS", ["match_score", "acceptance_rate", "net_cost"])
        college_data    = ns.get("COLLEGE_DATA", [])
        analyze_gaps    = ns.get("analyze_gaps",        lambda u, c: [])
        gen_plan        = ns.get("generate_action_plan", lambda g, c, u: "")
        show_visual     = ns.get("show_visual")

        if not recommend:
            st.error("No scoring engine found. Complete Week 2 to unlock it.")
            return

        try:
            results = recommend(user_inputs)
        except Exception as e:
            st.error(f"Scoring engine error: {e}")
            with st.expander("🐛 View Generated Code"):
                st.code(code, language="python")
            return

        if not results:
            st.warning("No results returned — check your scoring configuration.")
            return

        # ── Result cards ───────────────────────────────────────────────────────
        for i, r in enumerate(results[:5]):
            cat      = r.get("category", "Match")
            emoji    = _category_emoji(cat)
            score    = r.get("score", 0)
            name     = r.get("name", "College")
            net_cost = r.get("tuition", 0) - r.get("avg_financial_aid", 0)

            # Build a full college dict from the result (guaranteed per-college data)
            college = next((c for c in college_data if c["name"] == name), {})
            college_for_gaps = {
                "name":            name,
                "region":          r.get("region", college.get("region", "")),
                "acceptance_rate": r.get("acceptance_rate", college.get("acceptance_rate", 0)),
                "tuition":         r.get("tuition", college.get("tuition", 0)),
                "avg_financial_aid": r.get("avg_financial_aid", college.get("avg_financial_aid", 0)),
                "sat_range":       r.get("sat_range", college.get("sat_range", 0)),
                **college,
            }
            # Pass per-college match_score so each action plan is unique
            college_inputs = {**user_inputs, "_last_score": score}

            headline = format_headline(i + 1, name, score, cat)

            with st.container(border=True):
                st.markdown(f"### {emoji} {headline}")
                st.progress(score / 100)

                # Metrics row — only show what the student enabled
                metric_cols = st.columns(4)
                col_idx = 0
                if "match_score" in show_fields:
                    with metric_cols[col_idx]:
                        st.metric("Match Score", f"{score}%")
                    col_idx += 1
                if "sat_median" in show_fields and col_idx < 4:
                    with metric_cols[col_idx]:
                        st.metric("SAT Median", r.get("sat_range", "N/A"))
                    col_idx += 1
                if "net_cost" in show_fields and col_idx < 4:
                    with metric_cols[col_idx]:
                        st.metric("Net Cost/yr", f"${net_cost:,.0f}")
                    col_idx += 1
                if "acceptance_rate" in show_fields and col_idx < 4:
                    with metric_cols[col_idx]:
                        accept = r.get("acceptance_rate", 0)
                        st.metric("Acceptance Rate", f"{accept * 100:.0f}%")
                    col_idx += 1
                if "region" in show_fields and col_idx < 4:
                    with metric_cols[col_idx]:
                        st.metric("Region", r.get("region", "—"))
                    col_idx += 1

                # Gap analysis — show gaps per card (no plan here)
                try:
                    gaps = analyze_gaps(college_inputs, college_for_gaps)
                except Exception:
                    gaps = []

                if gaps:
                    st.warning(f"⚠️ {len(gaps)} gap(s) vs. {name}: " + " · ".join(gaps))
                else:
                    st.success("✅ No major profile gaps for this school")

        # ── Visualization — exec AI-generated plotly code directly ─────────────
        st.divider()
        w3 = student.get("week3_data", {})
        viz_type = w3.get("viz_type", "bar")
        viz_labels = {
            "bar":         "📊 Match Score Chart",
            "table":       "📋 College Comparison Table",
            "comparison":  "⚖️ Match Score vs Acceptance Rate",
            "cost":        "💰 Estimated Net Cost Comparison",
            "tier_summary":"🎯 Safety / Match / Reach Summary",
        }
        st.markdown(f"### {viz_labels.get(viz_type, '📊 Your Custom Visualization')}")

        show_visual = ns.get("show_visual")
        if show_visual:
            try:
                show_visual(results)
            except Exception as e:
                # Fallback to native altair chart if AI code fails
                st.warning(f"Custom visualization error — showing default chart. ({e})")
                _render_native_chart(results, viz_type)
        else:
            _render_native_chart(results, viz_type)

        # ── Single combined action plan section ────────────────────────────────
        st.divider()
        action_plan_prompt = student.get("week4_data", {}).get("action_plan_prompt", "").strip()
        if action_plan_prompt:
            st.markdown("### 📋 Your Personalized Action Plan")
            st.caption(
                "One plan built from your matched colleges, your profile gaps, "
                "your personal interests, and your current location — powered by GPT."
            )

            # Collect per-college gaps for the combined plan
            gaps_per_college = []
            for r in results[:5]:
                name   = r.get("name", "College")
                score  = r.get("score", 0)
                col_d  = next((c for c in college_data if c["name"] == name), {})
                col_ctx = {
                    "name":            name,
                    "region":          r.get("region", col_d.get("region", "")),
                    "acceptance_rate": r.get("acceptance_rate", col_d.get("acceptance_rate", 0)),
                    **col_d,
                }
                try:
                    g = analyze_gaps({**user_inputs, "_last_score": score}, col_ctx)
                except Exception:
                    g = []
                gaps_per_college.append((name, score, g))

            with st.spinner("🔍 Searching for real local opportunities, then writing your plan…"):
                plan = _generate_combined_plan(
                    results,
                    gaps_per_college,
                    user_inputs,
                    passion_qs,
                    student_location,
                    action_plan_prompt,
                )

            if plan:
                with st.container(border=True):
                    st.markdown(plan)

        st.divider()

        # Week progress summary
        with st.expander("📊 Week Progress Summary", expanded=False):
            cols = st.columns(4)
            for col, (label, key) in zip(cols, [
                ("Week 1 — Problem", "week1"),
                ("Week 2 — Engine",  "week2"),
                ("Week 3 — Display", "week3"),
                ("Week 4 — Gaps",    "week4"),
            ]):
                with col:
                    done = week_progress.get(key, False)
                    st.markdown(f"{'✅' if done else '⏳'} **{label}**")

        with st.expander("📟 View Full Generated Code", expanded=False):
            st.code(code, language="python")

    else:
        # Pre-submission state — show week status
        st.markdown("")
        cols = st.columns(4)
        for col, (label, desc, key) in zip(cols, [
            ("Week 1", "Problem & User",   "week1"),
            ("Week 2", "Scoring Engine",   "week2"),
            ("Week 3", "Presentation",     "week3"),
            ("Week 4", "Gap Analysis",     "week4"),
        ]):
            done = week_progress.get(key, False)
            with col:
                with st.container(border=True):
                    st.markdown(f"**{label}**")
                    st.caption(desc)
                    st.markdown("✅ Saved" if done else "⏳ In Progress")

        st.markdown("")
        st.info(
            "Fill in a student profile above and click **▶ Run My App** "
            "to see your college recommender in action — real cards, real scores, real data."
        )
