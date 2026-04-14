import json
import os
import streamlit as st
from openai import OpenAI
from storage import get_student, save_week_data, mark_week_complete
from ui_components import week_header, complete_week_button
from code_generator import generate_app_code
from code_runner import run_code

# ── OpenAI client ──────────────────────────────────────────────────────────────
_oai_client = None
def _openai():
    global _oai_client
    if _oai_client is None:
        _oai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))
    return _oai_client

# ── Standardized academic input definitions ────────────────────────────────────
STD_INPUTS = [
    {
        "key": "gpa",
        "label": "GPA (unweighted, 0–4.0)",
        "description": "Compared to each school's expected GPA based on its selectivity level.",
        "default_weight": 35,
        "on": True,
    },
    {
        "key": "sat",
        "label": "SAT Composite Score (400–1600)",
        "description": "Measured against each school's real SAT 50th percentile from the CDS Excel.",
        "default_weight": 30,
        "on": True,
    },
    {
        "key": "act",
        "label": "ACT Composite Score (1–36)",
        "description": "Converted to SAT scale (× 45) for direct comparison.",
        "default_weight": 0,
        "on": False,
    },
    {
        "key": "class_rank",
        "label": "Class Rank Percentile (1 = top 1%, 100 = bottom)",
        "description": "Selective schools expect applicants from the top of their class.",
        "default_weight": 20,
        "on": True,
    },
    {
        "key": "rigor",
        "label": "Course Rigor — AP / IB / Dual Enrollment count (0–10+)",
        "description": "High-selectivity schools expect rigorous coursework.",
        "default_weight": 15,
        "on": True,
    },
]

COLLEGE_ATTR_LABELS = {
    "research_score":         "Research & innovation culture",
    "campus_energy":          "Campus social life & vibe",
    "extracurricular_score":  "Clubs, activities & leadership",
    "support_score":          "Student support & community",
    "academic_selectivity":   "Academic selectivity & prestige",
    "financial_accessibility":"Financial aid & affordability",
}
VALID_ATTRS = list(COLLEGE_ATTR_LABELS.keys())

AI_SYSTEM_PROMPT = """\
You are an expert college admissions advisor and AI system designer.
A high school student has answered a custom passion question that THEY wrote.
Your job is to analyze their answer and extract 3–6 keywords that reveal who they are,
then map each keyword to the college attribute it most strongly signals.

Valid college attributes (use ONLY these exact strings):
- research_score         → Research, science, technology, data, building, invention, academics
- campus_energy          → Art, music, design, theater, film, creativity, culture, social life
- extracurricular_score  → Sports, clubs, leadership, organizing, teams, activities
- support_score          → Community, volunteering, teaching, helping, mentoring, people
- academic_selectivity   → Business, entrepreneurship, competition, prestige, achievement
- financial_accessibility → Finance, scholarships, cost, affordability

Return ONLY valid JSON — no explanation, no markdown, no code fences:
{"keywords": [{"word": "keyword", "attribute": "exact_attr_name", "why": "one sentence why this word signals that attribute"}]}

Each keyword must appear in or be directly implied by the student's answer.
Every attribute value must be one of the six valid strings above exactly."""


def _ai_analyze(question: str, answer: str) -> dict:
    try:
        response = _openai().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": AI_SYSTEM_PROMPT},
                {"role": "user",   "content": f"Question: {question}\n\nStudent answer: {answer}"},
            ],
            temperature=0.3,
            max_tokens=500,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:-1])
        data = json.loads(raw)
        cleaned = [
            item for item in data.get("keywords", [])
            if item.get("attribute") in VALID_ATTRS and item.get("word")
        ]
        return {"keywords": cleaned}
    except Exception as e:
        return {"error": str(e)}


def render():
    student_id = st.session_state.get("student_id")
    if not student_id:
        st.warning("No student selected.")
        return
    student = get_student(student_id)
    if not student:
        st.error("Student not found.")
        return

    week2_done = student.get("week_progress", {}).get("week2", False)
    week_header(2, "Input Architecture & Scoring Design",
                "Configure your academic inputs, design passion-based questions, and set your scoring weights.",
                week2_done)

    ex = student.get("week2_data", {})

    st.markdown("### 🎯 Week 2 Goals")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
- Choose which standardized academic metrics your app uses
- Write your own passion questions that reveal who your users really are
- Use AI to extract keywords from sample answers and map them to college attributes
- Control how much academic data vs passion data shapes the final score
        """)
    with c2:
        with st.container(border=True):
            st.markdown("**The two-pool scoring model**")
            st.caption("Your final match score is a blend of two pools:")
            st.markdown("🔢 **Academic Pool** — GPA, SAT, class rank, course rigor")
            st.markdown("💬 **Passion Pool** — your custom questions, scored by keyword matching")
            st.markdown("You control how much each pool contributes.")

    st.divider()
    st.markdown("### 📝 Week 2 Tasks")

    tab1, tab2, tab3 = st.tabs([
        "📊 Task 1 — Standardized Inputs",
        "✍️ Task 2 — Design Your Questions",
        "⚖️ Task 3 — Scoring Pool Weights",
    ])

    # ─── TAB 1: Standardized Inputs ──────────────────────────────────────────
    with tab1:
        st.caption("Enable the academic inputs your app will ask for. For each, set its weight within the academic pool (should add to 100%).")

        for inp in STD_INPUTS:
            k = inp["key"]
            with st.container(border=True):
                col_cb, col_desc, col_wt = st.columns([0.4, 4.0, 1.2])
                with col_cb:
                    st.write("")
                    enabled = st.checkbox(
                        "on",
                        value=bool(ex.get(f"std_{k}_enabled", inp["on"])),
                        key=f"w2_std_{k}_en",
                        label_visibility="collapsed",
                    )
                with col_desc:
                    style = "**" if enabled else ""
                    st.markdown(f"{style}{inp['label']}{style}")
                    st.caption(inp["description"])
                with col_wt:
                    if enabled:
                        st.number_input(
                            "Weight %",
                            min_value=0, max_value=100,
                            value=int(ex.get(f"std_{k}_weight", inp["default_weight"])),
                            key=f"w2_std_{k}_wt",
                            label_visibility="collapsed",
                        )
                    else:
                        st.caption("(off)")

        enabled_keys = [i["key"] for i in STD_INPUTS if st.session_state.get(f"w2_std_{i['key']}_en", i["on"])]
        std_total = sum(
            int(st.session_state.get(
                f"w2_std_{k}_wt",
                ex.get(f"std_{k}_weight", next(i["default_weight"] for i in STD_INPUTS if i["key"] == k))
            ))
            for k in enabled_keys
        )
        if enabled_keys:
            if abs(std_total - 100) <= 1:
                st.success(f"✅ Academic weights sum to {std_total}% — perfect!")
            else:
                st.warning(f"⚠️ Academic weights sum to {std_total}% — adjust to reach 100%.")

    # ─── TAB 2: Student-Designed Passion Questions ────────────────────────────
    with tab2:
        st.markdown("## Design your own questions.")
        st.markdown(
            "You decide what to ask. Write 1–3 questions that reveal who your users really are — "
            "beyond their grades and test scores. "
            "Then write a sample answer and let AI extract the scoring signals from it."
        )

        with st.expander("🤔 What makes a good passion question?", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                with st.container(border=True):
                    st.markdown("**✓ Specific, not vague**")
                    st.caption("Bad: \"What do you like?\"")
                    st.caption("Better: \"What could you talk about **for hours**?\"")
                    st.caption("Specific language raises the bar — filters for genuine passion, not casual interest.")
            with col2:
                with st.container(border=True):
                    st.markdown("**✓ Removes pressure**")
                    st.caption("Bad: \"What are your goals?\"")
                    st.caption("Better: \"**No grades, no pressure** — what would you build?\"")
                    st.caption("Removing expectations makes answers honest and intrinsically motivated.")
            with col3:
                with st.container(border=True):
                    st.markdown("**✓ Action-focused**")
                    st.caption("Bad: \"Do you care about your community?\"")
                    st.caption("Better: \"Have you **done** anything with real impact?\"")
                    st.caption("Actions reveal character better than opinions ever do.")

        st.markdown("---")

        # ── Number of questions selector ──────────────────────────────────────
        saved_passion = ex.get("passion_questions", [])
        default_num = max(len(saved_passion), 1)
        num_q = st.radio(
            "How many passion questions will your app ask?",
            options=[1, 2, 3],
            index=min(default_num - 1, 2),
            horizontal=True,
            key="w2_num_questions",
        )

        st.markdown("---")

        if "w2_ai_results" not in st.session_state:
            st.session_state["w2_ai_results"] = {}

        for i in range(num_q):
            saved_q = saved_passion[i] if i < len(saved_passion) else {}
            qid = f"q{i+1}"

            with st.container(border=True):
                st.markdown(f"### Question {i+1}")

                # ── Student writes the question ───────────────────────────────
                st.markdown("**Write your question:**")
                q_text = st.text_input(
                    f"Question {i+1} text",
                    value=st.session_state.get(f"w2_q{i}_text", saved_q.get("question", "")),
                    placeholder=f"e.g. What activity makes you completely lose track of time?",
                    key=f"w2_q{i}_text",
                    label_visibility="collapsed",
                )

                if not q_text.strip():
                    st.caption("⬆ Write a question first — then test a sample answer below.")
                else:
                    # ── Student writes a sample answer ────────────────────────
                    st.markdown("**Write a sample answer to test your question:**")
                    st.caption("Imagine how a real student would answer. The AI will extract scoring keywords from this.")
                    answer = st.text_area(
                        f"Sample answer {i+1}",
                        value=st.session_state.get(f"w2_answer_{qid}", saved_q.get("sample_answer", "")),
                        height=80,
                        placeholder="e.g. Honestly, I lose track of time whenever I'm coding or building something — especially apps that help people...",
                        key=f"w2_answer_{qid}",
                        label_visibility="collapsed",
                    )

                    col_btn, col_wt = st.columns([2, 1])
                    with col_btn:
                        analyze_clicked = st.button(
                            "🤖 Analyze with AI",
                            key=f"w2_analyze_{qid}",
                            use_container_width=True,
                            disabled=not answer.strip(),
                        )
                    with col_wt:
                        default_weights = [40, 35, 25]
                        st.number_input(
                            f"Weight % in passion pool",
                            min_value=0, max_value=100,
                            value=int(saved_q.get("weight", default_weights[i])),
                            key=f"w2_passion_{qid}_wt",
                            label_visibility="collapsed",
                        )

                    if analyze_clicked:
                        with st.spinner("Analyzing..."):
                            result = _ai_analyze(q_text, answer)
                        st.session_state["w2_ai_results"][qid] = result
                        st.rerun()

                    # ── AI Results ────────────────────────────────────────────
                    ai_result = st.session_state["w2_ai_results"].get(qid)
                    if ai_result:
                        if "error" in ai_result:
                            st.error(f"Analysis error: {ai_result['error']}")
                        else:
                            kws = ai_result.get("keywords", [])
                            if kws:
                                st.markdown("**AI detected these scoring signals in your sample answer:**")
                                by_attr = {}
                                for item in kws:
                                    by_attr.setdefault(item["attribute"], []).append(item)
                                cols = st.columns(min(len(by_attr), 3))
                                for j, (attr, items) in enumerate(by_attr.items()):
                                    with cols[j % len(cols)]:
                                        with st.container(border=True):
                                            st.caption(COLLEGE_ATTR_LABELS.get(attr, attr))
                                            for item in items:
                                                st.markdown(f"`{item['word']}`")
                                                st.caption(item.get("why", ""))
                                st.caption(
                                    "These keywords become your scoring function: when a real user's answer contains "
                                    "these words, your app scores them higher on the linked college dimension."
                                )
                            else:
                                st.info("No strong college signals found. Try a more specific sample answer.")

            st.write("")

        # ── Weight summary ────────────────────────────────────────────────────
        q_weights = [int(st.session_state.get(f"w2_passion_q{i+1}_wt", [40,35,25][i])) for i in range(num_q)]
        q_total   = sum(q_weights)
        st.markdown("**Passion pool weight breakdown:**")
        for i in range(num_q):
            q_text_val = st.session_state.get(f"w2_q{i}_text", "")
            label = f'"{q_text_val[:50]}..."' if len(q_text_val) > 50 else f'"{q_text_val}"' if q_text_val else f"Question {i+1}"
            st.markdown(f"  • {label}: **{q_weights[i]}%** of passion pool")
        if abs(q_total - 100) <= 1:
            st.success(f"✅ Passion weights sum to {q_total}% — great!")
        else:
            st.warning(f"⚠️ Passion weights sum to {q_total}% — adjust so they add to 100%.")

        st.divider()
        with st.expander("💡 How AI analysis becomes your scoring code", expanded=False):
            st.markdown("""
**Here's what just happened:**

When you clicked Analyze, the AI read your question and sample answer, then returned:
```
"coding" → research_score
"helping people" → support_score
```

Your generated scoring engine does the same thing:
```python
if "coding" in user_answer.lower():
    score += college["research_score"] * weight
```

**The AI does this mapping automatically, reading context and meaning — not just exact words.**
Your scoring engine does it with explicit keywords. Same logic. Different power levels.

When you add an AI API to your app, users get smarter, more nuanced scoring.
You're building the keyword version first — that's how every AI system starts.
            """)

    # ─── TAB 3: Scoring Pool Weights ─────────────────────────────────────────
    with tab3:
        st.caption("Set the final weight balance: how much does the academic score contribute vs the passion score?")

        c1, c2 = st.columns(2)
        with c1:
            acad_pct = st.number_input(
                "🔢 Academic Pool Weight (%)",
                min_value=0, max_value=100,
                value=int(ex.get("academic_pool_weight", 70)),
                key="w2_acad_pct",
                help="GPA + SAT/ACT + class rank + course rigor",
            )
        with c2:
            passion_pct = st.number_input(
                "💬 Passion Pool Weight (%)",
                min_value=0, max_value=100,
                value=int(ex.get("passion_pool_weight", 30)),
                key="w2_passion_pct",
                help="Your custom passion question answers",
            )

        pool_total = acad_pct + passion_pct
        if abs(pool_total - 100) <= 1:
            st.success(f"✅ Pool weights sum to {pool_total}% — great!")
        else:
            st.warning(f"⚠️ Pool weights sum to {pool_total}% — they must add to 100%.")

        st.markdown("**Your scoring formula:**")
        st.code(
            f"final_match_score = (academic_score × {acad_pct}%)  +  (passion_score × {passion_pct}%)",
            language="text",
        )

        st.markdown("---")
        num_q = int(st.session_state.get("w2_num_questions", max(len(ex.get("passion_questions", [])), 1)))
        q_weights = [int(st.session_state.get(f"w2_passion_q{i+1}_wt", [40,35,25][i])) for i in range(num_q)]
        q_total   = sum(q_weights)
        st.markdown(f"**How your questions contribute to that {passion_pct}%:**")
        for i in range(num_q):
            q_text_val = st.session_state.get(f"w2_q{i}_text", f"Question {i+1}")
            pct_of_final = round(q_weights[i] / max(q_total, 1) * passion_pct)
            label = f'"{q_text_val[:40]}..."' if len(q_text_val) > 40 else f'"{q_text_val}"' if q_text_val else f"Question {i+1}"
            st.markdown(f"  • {label} → **{pct_of_final}% of your final score**")

    st.divider()

    if st.button("💾 Save Week 2 Progress", use_container_width=True):
        save_week_data(student_id, "week2", _collect(ex))
        st.success("Week 2 progress saved!")
        st.rerun()

    st.divider()

    with st.expander("📟 My Code So Far", expanded=True):
        st.caption("Sections unlock as you configure each task. Nothing is auto-filled — this code only reflects your actual choices.")
        preview_student = get_student(student_id) or {}
        preview_student["week2_data"] = _collect(ex)
        generated = generate_app_code(preview_student)
        st.code(generated, language="python")

        ca, cb = st.columns(2)
        with ca:
            if st.button("▶ Run This Code", key="run_w2", use_container_width=True, type="primary"):
                with st.spinner("Running your recommendation engine on 42 real colleges..."):
                    result = run_code(generated)
                st.session_state["w2_run_result"] = result
        with cb:
            st.download_button(
                "⬇ Download .py", data=generated,
                file_name="my_app_week2.py", mime="text/plain",
                use_container_width=True,
            )

        if "w2_run_result" in st.session_state:
            r = st.session_state["w2_run_result"]
            if r.get("timed_out"):
                st.error(r["stderr"])
            elif r["exit_code"] == 0:
                st.success("✅ Your recommendation engine is working!")
                st.code(r["stdout"] or "(no output)", language="text")
            else:
                st.warning("⚠️ Ran with errors")
                if r["stderr"]:
                    st.code(r["stderr"], language="text")

    st.divider()
    if complete_week_button("week2"):
        save_week_data(student_id, "week2", _collect(ex))
        mark_week_complete(student_id, "week2")
        st.success("Week 2 complete! 🎉 Head to Week 3 to design how your results look.")
        st.balloons()
        st.rerun()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _collect(ex: dict) -> dict:
    data = {
        "academic_pool_weight": int(st.session_state.get("w2_acad_pct", ex.get("academic_pool_weight", 70))),
        "passion_pool_weight":  int(st.session_state.get("w2_passion_pct", ex.get("passion_pool_weight", 30))),
    }
    for inp in STD_INPUTS:
        k = inp["key"]
        data[f"std_{k}_enabled"] = bool(st.session_state.get(f"w2_std_{k}_en", ex.get(f"std_{k}_enabled", inp["on"])))
        data[f"std_{k}_weight"]  = int(st.session_state.get(f"w2_std_{k}_wt", ex.get(f"std_{k}_weight", inp["default_weight"])))

    ai_results      = st.session_state.get("w2_ai_results", {})
    existing_passion = ex.get("passion_questions", [])
    num_q = int(st.session_state.get("w2_num_questions", max(len(existing_passion), 1)))
    default_weights = [40, 35, 25]

    passion_qs = []
    for i in range(num_q):
        qid   = f"q{i+1}"
        saved = existing_passion[i] if i < len(existing_passion) else {}
        ai    = ai_results.get(qid, {})

        q_text = st.session_state.get(f"w2_q{i}_text", saved.get("question", ""))
        if not q_text.strip():
            continue  # skip blank questions

        # Build keyword map from AI result or saved data
        if ai and "keywords" in ai:
            active_map = {item["word"]: item["attribute"] for item in ai["keywords"] if item.get("attribute") in VALID_ATTRS}
        else:
            active_map = saved.get("active_keywords", {})

        weight        = int(st.session_state.get(f"w2_passion_{qid}_wt", saved.get("weight", default_weights[i])))
        sample_answer = st.session_state.get(f"w2_answer_{qid}", saved.get("sample_answer", ""))

        passion_qs.append({
            "id":              qid,
            "question":        q_text,
            "active_keywords": active_map,
            "weight":          weight,
            "sample_answer":   sample_answer,
        })

    data["passion_questions"]   = passion_qs
    data["passion_inputs_text"] = _passion_qs_to_text(passion_qs)
    return data


def _passion_qs_to_text(questions: list) -> str:
    lines = []
    for q in questions:
        lines.append(f"Question: {q['question']}")
        for kw, attr in q.get("active_keywords", {}).items():
            lines.append(f"  {kw} → {attr}")
        lines.append("")
    return "\n".join(lines).strip()
