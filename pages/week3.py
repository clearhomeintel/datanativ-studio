import streamlit as st
from storage import get_student, save_week_data, mark_week_complete
from ui_components import week_header, complete_week_button
from code_generator import generate_app_code
from code_runner import run_code

# ── All available fields with design context ───────────────────────────────────
ALL_FIELDS = {
    "match_score":       {
        "label":   "Match Score (%)",
        "emotion": "Confidence",
        "why":     "The core number — tells a student at a glance how well they fit. Creates immediate signal.",
    },
    "acceptance_rate":   {
        "label":   "Acceptance Rate (%)",
        "emotion": "Reality check",
        "why":     "Anchors the score in reality. A 92% match at a 4% acceptance school means something different.",
    },
    "net_cost":          {
        "label":   "Estimated Net Cost / year",
        "emotion": "Clarity on what's possible",
        "why":     "Removes sticker price shock. Shows what the student would *actually* pay after financial aid.",
    },
    "sat_median":        {
        "label":   "SAT 50th Percentile",
        "emotion": "Positioning",
        "why":     "Lets a student instantly see if their scores put them above, at, or below the school's midpoint.",
    },
    "region":            {
        "label":   "Region",
        "emotion": "Belonging",
        "why":     "Students often have strong geographic preferences. This answers: 'will I feel far from home?'",
    },
    "setting":           {
        "label":   "Campus Setting",
        "emotion": "Fit and vibe",
        "why":     "Urban vs rural changes daily life drastically. This answers: 'does the environment match me?'",
    },
    "enrollment":        {
        "label":   "Enrollment Size",
        "emotion": "Scale of experience",
        "why":     "50,000 vs 2,000 students are completely different experiences. Size shapes identity.",
    },
    "financial_aid":     {
        "label":   "Average Financial Aid",
        "emotion": "Hope",
        "why":     "Seeing that a school gives generous aid can transform a 'reach' into a real possibility.",
    },
}

DEFAULT_FIELDS = ["match_score", "sat_median", "net_cost", "acceptance_rate", "region"]

SAMPLE_COLLEGES = [
    {
        "name": "MIT", "score": 91, "tier": "Reach", "rank": 1,
        "sat_range": 1545, "tuition": 57986, "avg_financial_aid": 51000,
        "acceptance_rate": 0.04, "region": "Northeast", "setting": "Urban", "enrollment": 4528,
    },
    {
        "name": "University of Michigan", "score": 78, "tier": "Match", "rank": 2,
        "sat_range": 1435, "tuition": 52266, "avg_financial_aid": 18000,
        "acceptance_rate": 0.18, "region": "Midwest", "setting": "College Town", "enrollment": 31329,
    },
]

PROMPT_TECHNIQUES = [
    {
        "name":        "Zero-Shot",
        "emoji":       "1️⃣",
        "description": "Just ask directly, no examples given.",
        "example":     "Show a bar chart of match scores for my top colleges.",
        "best_for":    "Simple, well-understood tasks — fast to write, good for clear requests.",
        "generates":   "bar",
    },
    {
        "name":        "Role Prompting",
        "emoji":       "2️⃣",
        "description": "Give the system an identity or perspective.",
        "example":     "Act as a UX designer for a nervous 17-year-old. Show match scores in a way that feels encouraging, not overwhelming.",
        "best_for":    "When tone, style, and audience matter — shapes how the output 'feels'.",
        "generates":   "bar",
    },
    {
        "name":        "Few-Shot",
        "emoji":       "3️⃣",
        "description": "Show an example of what you want first.",
        "example":     "Like this: [MIT ████████ 88%]. Now create this for all my top results, sorted best to worst.",
        "best_for":    "When you have a specific visual format in mind — examples set the exact target.",
        "generates":   "bar",
    },
    {
        "name":        "Chain-of-Thought",
        "emoji":       "4️⃣",
        "description": "Walk the system through your reasoning step by step.",
        "example":     "Step 1: Rank colleges by match score. Step 2: Show each as a horizontal bar. Step 3: Highlight the top match differently. Step 4: Show SAT median and net cost below each bar.",
        "best_for":    "Complex, multi-part outputs — forces the system to think through each piece.",
        "generates":   "comparison",
    },
]

VIZ_EXAMPLES = [
    "Show a horizontal bar chart comparing match scores for all results",
    "Show a table with each college's score, SAT median, and net cost",
    "Show a side-by-side comparison of my SAT score vs each school's median",
    "Act as a data visualization expert. Show the results in a way that helps an anxious student compare their top 3 options at a glance.",
]


def render():
    student_id = st.session_state.get("student_id")
    if not student_id:
        st.warning("No student selected.")
        return
    student = get_student(student_id)
    if not student:
        st.error("Student not found.")
        return

    week3_done = student.get("week_progress", {}).get("week3", False)
    week_header(3, "Results Presentation Design",
                "Design what students see the moment their results load — this is the moment that makes your app matter.",
                week3_done)

    ex = student.get("week3_data", {})

    st.markdown("### 🎯 Week 3 Goals")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
- Apply design thinking to choose what information a student sees first
- Write a headline that feels personal, not robotic
- Use prompting techniques to generate chart code from plain English
- Preview what your real result cards will look like
        """)
    with c2:
        with st.container(border=True):
            st.markdown("**Data → Experience**")
            st.caption(
                "Week 2 built the scoring engine. Week 3 answers: "
                "*what does the user actually feel?* "
                "A match score is just a number until someone decides "
                "which numbers matter most, in what order, and how to say it."
            )

    st.divider()
    st.markdown("### 📝 Week 3 Tasks")

    tab1, tab2, tab3 = st.tabs([
        "🎨 Task 1 — Card Design",
        "📊 Task 2 — Visualization Prompt",
        "👁️ Task 3 — Preview",
    ])

    # ─── TAB 1: Design Thinking Card Designer ────────────────────────────────
    with tab1:
        st.markdown("## You're the product designer.")
        st.markdown(
            "A high school student just clicked 'Find My Match.' "
            "They're nervous, excited, maybe overwhelmed. "
            "**You have 3 seconds to show them something that makes them feel confident, not confused.**"
        )
        st.caption("Three design decisions stand between a data dump and a great experience.")

        st.divider()

        # ── STEP 1: The Hero Stat ─────────────────────────────────────────────
        with st.container(border=True):
            st.markdown("### 🥇 Step 1 — The First Impression")
            st.markdown(
                "**Choose the ONE number that hits the student first.** "
                "This is the 'hero stat' — the most prominent thing on the card."
            )

            with st.expander("🤔 Design question: What does a student *need* to feel right now?", expanded=True):
                st.markdown("""
Different data creates different emotional responses:
- **Match Score** → *"I belong here"* — gives confidence and direction
- **Acceptance Rate** → *"This is realistic"* — grounds excitement in reality
- **Net Cost** → *"I can actually afford this"* — removes a major anxiety
- **SAT Median** → *"I know where I stand"* — gives academic positioning

**The best hero stat is the one that answers the student's biggest unspoken question.**
                """)

            saved_hero = ex.get("hero_stat", "match_score")
            hero_options = {k: v["label"] for k, v in ALL_FIELDS.items()}
            hero_stat = st.radio(
                "Your hero stat:",
                options=list(hero_options.keys()),
                format_func=lambda k: f"{hero_options[k]}  —  creates: {ALL_FIELDS[k]['emotion']}",
                index=list(hero_options.keys()).index(saved_hero) if saved_hero in hero_options else 0,
                key="w3_hero",
            )
            st.caption(f"💡 Why this works: {ALL_FIELDS[hero_stat]['why']}")

        st.write("")

        # ── STEP 2: Supporting Context ────────────────────────────────────────
        with st.container(border=True):
            st.markdown("### 📋 Step 2 — The Supporting Story")
            st.markdown(
                "**Choose 2–3 facts that give the hero stat meaning.** "
                "If the hero is a match score, what question does '87%' raise in the student's mind next?"
            )

            with st.expander("🤔 Design question: What raises the next question?"):
                st.markdown("""
Good supporting data *resolves the hero stat's ambiguity*:

- Hero: Match Score (87%) → next question: "But can I get in? Can I afford it?"
  → Best support: **Acceptance Rate** + **Net Cost**

- Hero: Net Cost ($12,000) → next question: "Is this school actually a good academic fit?"
  → Best support: **Match Score** + **SAT Median**

- Hero: Acceptance Rate (4%) → next question: "Is this school even remotely right for me?"
  → Best support: **Match Score** + **Setting** + **Region**

**Great design anticipates the next question and answers it before it's asked.**
                """)

            remaining_fields = {k: v for k, v in ALL_FIELDS.items() if k != hero_stat}
            saved_support = [f for f in ex.get("show_fields", DEFAULT_FIELDS) if f != hero_stat]
            safe_default = [f for f in saved_support if f in remaining_fields][:3]
            support_fields = st.multiselect(
                "Supporting context fields (choose 2–3):",
                options=list(remaining_fields.keys()),
                format_func=lambda k: f"{ALL_FIELDS[k]['label']}",
                default=safe_default,
                max_selections=3,
                key="w3_support",
            )
            if len(support_fields) < 2:
                st.warning("Pick at least 2 supporting fields — context makes the hero stat meaningful.")
            elif len(support_fields) == 3:
                st.success("Good — a hero + 3 supporting fields creates a clear, complete picture.")

        st.write("")

        # ── STEP 3: The Headline ──────────────────────────────────────────────
        with st.container(border=True):
            st.markdown("### ✍️ Step 3 — The Headline")
            st.markdown(
                "**Write the one sentence that greets each student with their result.** "
                "This is not a label — it's a moment. Make it feel personal."
            )

            with st.expander("🤔 Design question: What's the difference between a label and a moment?"):
                st.markdown("""
**Label (robotic):** "Match Result: 91% — Reach"
> Technically accurate. Completely cold.

**Moment (personal):** "#1 — MIT is your dream school — and you have an 91% match."
> Same data. Completely different feeling.

**How to write a great headline:**
- Use the student's rank (makes it feel like *their* list)
- Name the school (it's not a number, it's a place)
- Include the match score (quantifies the feeling)
- Use human language — "your school," not just a category label

**Available tokens you can use:** `{rank}` `{college}` `{score}` `{tier}`
                """)

            saved_headline = ex.get("headline_template", "#{rank} — {college} is your {tier} match ({score}%)")
            headline = st.text_input(
                "Your headline template:",
                value=saved_headline,
                key="w3_headline",
                placeholder="e.g.  #{rank} — {college} is your {tier} match ({score}%)",
            )

            # Live headline preview
            preview_hl = (
                headline
                .replace("{rank}", "1")
                .replace("{college}", "Stanford University")
                .replace("{score}", "87")
                .replace("{tier}", "Reach")
            ) if headline else "#1 — Stanford University is your Reach match (87%)"

            with st.container(border=True):
                st.markdown("**Live preview:**")
                st.markdown(f"### {preview_hl}")

    # ─── TAB 2: Visualization Type + Prompt ──────────────────────────────────
    with tab2:
        st.markdown("## Choose a visualization type, then describe exactly what you want.")
        st.markdown(
            "Your choice of visualization type directly changes the Python code your app generates. "
            "Your prompt describes what data to show and how it should feel — "
            "together they produce unique, real code."
        )

        # ── Step 1: Pick the visualization type ──────────────────────────────
        with st.container(border=True):
            st.markdown("### Step 1 — Choose your visualization type")
            st.caption("Each type generates completely different code. Pick the one that best fits your app's purpose.")

            VIZ_TYPES = {
                "bar":           {"label": "📊 Match Score Bar Chart",      "desc": "Horizontal bars — one per college, length = match score. Fast, scannable, emotionally clear."},
                "table":         {"label": "📋 Data Table",                 "desc": "Grid with score, SAT median, and net cost per college. Best when students want to compare numbers."},
                "comparison":    {"label": "⚖️ Score vs SAT Comparison",    "desc": "Match score alongside academic positioning. Shows fit AND academic realism side-by-side."},
                "cost":          {"label": "💰 Cost Breakdown",             "desc": "Tuition vs net cost (after aid) per college. Removes sticker shock — shows what students actually pay."},
                "tier_summary":  {"label": "🎯 Safety / Match / Reach Summary", "desc": "Groups results into three buckets. Great for giving students a quick strategic overview."},
            }

            saved_viz_type = ex.get("viz_type", "bar")
            viz_type_keys = list(VIZ_TYPES.keys())
            viz_type_idx = viz_type_keys.index(saved_viz_type) if saved_viz_type in viz_type_keys else 0

            selected_viz_type = st.radio(
                "Visualization type:",
                options=viz_type_keys,
                format_func=lambda k: VIZ_TYPES[k]["label"],
                index=viz_type_idx,
                key="w3_viz_type",
                label_visibility="collapsed",
            )
            st.caption(VIZ_TYPES[selected_viz_type]["desc"])

        st.write("")

        # ── Step 2: Write the prompt ──────────────────────────────────────────
        with st.container(border=True):
            st.markdown("### Step 2 — Write your visualization prompt")
            st.markdown(
                "Your prompt describes **what the visualization should focus on and how it should feel**. "
                "The system uses your prompt to customize the code it generates — "
                "the same type can produce different results depending on how you describe it."
            )

            with st.expander("📚 The 4 Prompting Techniques", expanded=False):
                tech_cols = st.columns(2)
                for i, tech in enumerate(PROMPT_TECHNIQUES):
                    with tech_cols[i % 2]:
                        with st.container(border=True):
                            st.markdown(f"**{tech['emoji']} {tech['name']}**")
                            st.caption(tech["description"])
                            st.markdown("Example:")
                            st.code(tech["example"], language="text")
                            st.caption(f"Best for: {tech['best_for']}")

            saved_viz = ex.get("viz_prompt", "")
            viz_prompt = st.text_area(
                "Your prompt:",
                value=saved_viz,
                height=110,
                key="w3_viz_prompt",
                placeholder=_viz_placeholder(selected_viz_type),
                label_visibility="collapsed",
            )

            if viz_prompt.strip():
                technique = _detect_prompt_technique(viz_prompt)
                st.info(f"Prompt technique detected: **{technique}**")

            st.write("")
            if st.button("🤖 Generate Code with AI", use_container_width=True, type="primary"):
                if not viz_prompt.strip():
                    st.warning("Write a prompt above first, then click Generate.")
                else:
                    with st.spinner("AI is writing your visualization code…"):
                        ai_code = _generate_viz_code_with_ai(selected_viz_type, viz_prompt)
                    if ai_code:
                        st.session_state["w3_viz_code"] = ai_code
                        # Auto-save immediately so "My Code So Far" picks it up
                        current = _collect(ex)
                        current["viz_code"] = ai_code
                        save_week_data(student_id, "week3", current)
                        st.success("✅ Code generated and saved! See Step 3 below and My Code So Far.")
                        st.rerun()
                    else:
                        st.error("❌ Generation failed. Check the OPENAI_API_KEY secret and try again.")

        st.write("")

        # ── Step 3: AI-generated code ─────────────────────────────────────────
        with st.container(border=True):
            st.markdown("### Step 3 — Your AI-generated visualization code")
            generated_code = st.session_state.get("w3_viz_code", ex.get("viz_code", ""))
            if generated_code:
                st.caption(
                    "This is the actual Python code your app will run — written by AI "
                    "based on the type and prompt you chose. It will be embedded into your app."
                )
                st.code(generated_code, language="python")
                if st.button("🗑️ Clear & Regenerate", key="w3_clear_viz"):
                    st.session_state["w3_viz_code"] = ""
                    st.rerun()
            else:
                st.caption(
                    "No code generated yet. Select a visualization type and write a prompt above, "
                    "then click **Generate Code with AI**."
                )
                st.info("👆 Fill in Steps 1 and 2 above, then click **Generate Code with AI**.")

    # ─── TAB 3: Preview ──────────────────────────────────────────────────────
    with tab3:
        st.markdown("## What a student will actually see.")
        st.caption("Live preview using sample college data with your current design choices from Tasks 1 and 2.")

        headline_val  = st.session_state.get("w3_headline", ex.get("headline_template", "#{rank} — {college} is your {tier} match ({score}%)"))
        hero          = st.session_state.get("w3_hero", ex.get("hero_stat", "match_score"))
        support       = st.session_state.get("w3_support", [f for f in ex.get("show_fields", DEFAULT_FIELDS) if f != hero])
        all_fields    = [hero] + [f for f in support if f != hero]

        for college in SAMPLE_COLLEGES:
            _render_card(college, headline_val, all_fields, hero)

        st.write("")
        st.caption("Both cards use the same design — your choices apply to every result.")

    st.divider()

    if st.button("💾 Save Week 3 Progress", use_container_width=True):
        save_week_data(student_id, "week3", _collect(ex))
        st.success("Week 3 progress saved!")
        st.rerun()

    st.divider()

    # ── Code Panel ─────────────────────────────────────────────────────────────
    with st.expander("📟 My Code So Far", expanded=True):
        st.caption(
            "Section 9 unlocks after you pick fields and write a headline (Task 1). "
            "Section 9b shows a TODO stub until you click **Generate Code with AI** in Task 2 — "
            "after that, the actual AI-written show_visual() function appears here."
        )
        preview_student = get_student(student_id) or {}
        preview_student["week3_data"] = _collect(ex)
        generated = generate_app_code(preview_student)
        st.code(generated, language="python")

        ca, cb = st.columns(2)
        with ca:
            if st.button("▶ Run This Code", key="run_w3", use_container_width=True, type="primary"):
                with st.spinner("Running your app with presentation layer..."):
                    result = run_code(generated)
                st.session_state["w3_run_result"] = result
        with cb:
            st.download_button(
                "⬇ Download .py", data=generated,
                file_name="my_app_week3.py", mime="text/plain",
                use_container_width=True,
            )
        if "w3_run_result" in st.session_state:
            r = st.session_state["w3_run_result"]
            if r.get("timed_out"):
                st.error(r["stderr"])
            elif r["exit_code"] == 0:
                st.success("✅ App with presentation layer working!")
                st.code(r["stdout"] or "(no output)", language="text")
            else:
                st.warning("⚠️ Errors found")
                if r["stderr"]:
                    st.code(r["stderr"], language="text")

    st.divider()
    if complete_week_button("week3"):
        save_week_data(student_id, "week3", _collect(ex))
        mark_week_complete(student_id, "week3")
        st.success("Week 3 complete! 🎉 Head to Week 4 — gap analysis and action plans!")
        st.balloons()
        st.rerun()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _collect(ex: dict) -> dict:
    hero    = st.session_state.get("w3_hero", ex.get("hero_stat", "match_score"))
    support = st.session_state.get("w3_support", [f for f in ex.get("show_fields", DEFAULT_FIELDS) if f != hero])
    all_fields = [hero] + [f for f in support if f != hero]
    return {
        "hero_stat":         hero,
        "show_fields":       all_fields,
        "headline_template": st.session_state.get("w3_headline",    ex.get("headline_template", "")),
        "viz_prompt":        st.session_state.get("w3_viz_prompt",   ex.get("viz_prompt", "")),
        "viz_type":          st.session_state.get("w3_viz_type",     ex.get("viz_type", "bar")),
        "viz_code":          st.session_state.get("w3_viz_code",     ex.get("viz_code", "")),
    }


def _detect_prompt_technique(prompt: str) -> str:
    p = prompt.lower()
    if any(w in p for w in ["step 1", "step 2", "first,", "then,", "finally,"]):
        return "Chain-of-Thought"
    if any(w in p for w in ["act as", "you are a", "imagine you are", "as a"]):
        return "Role Prompting"
    if any(w in p for w in ["like this", "for example:", "example:", "similar to"]):
        return "Few-Shot"
    return "Zero-Shot"


def _viz_placeholder(viz_type: str) -> str:
    return {
        "bar":        "Show a horizontal bar chart of match scores, sorted highest first. Highlight the top match.",
        "table":      "Show a clean data table with each college's score, SAT median, and net cost — easy to scan.",
        "comparison": "Act as a data designer. Show my match score vs the school's SAT median for each result side by side.",
        "cost":       "Step 1: Show each college's tuition. Step 2: Show what I'd actually pay after financial aid. Step 3: Highlight the most affordable option.",
        "tier_summary": "Group my results into Safety, Match, and Reach buckets. Show how many colleges are in each and their average match score.",
    }.get(viz_type, "Describe what you want to see...")


def _build_viz_code(viz_type: str, prompt: str) -> str:
    """Generate the actual Python code for this visualization type.
    The prompt is embedded as a docstring so students see the connection."""
    doc = (prompt.strip().replace('"""', "'\"'") if prompt.strip() else f"Show results as a {viz_type} visualization.").replace("\n", " ")

    if viz_type == "bar":
        return f'''\
def show_visual(results):
    """
    Student prompt: "{doc}"
    Visualization type: Match Score Bar Chart
    """
    print()
    print("  📊  Match Score Chart")
    print("  " + "─" * 54)
    # Sort highest score first
    for r in sorted(results, key=lambda x: x["score"], reverse=True):
        filled = "█" * (r["score"] // 5)
        empty  = "░" * (20 - r["score"] // 5)
        marker = " ◀ TOP MATCH" if r == sorted(results, key=lambda x: x["score"], reverse=True)[0] else ""
        print(f"  {{r['name'][:26]:<26}} [{{filled}}{{empty}}] {{r['score']}}%{{marker}}")
    print()'''

    elif viz_type == "table":
        return f'''\
def show_visual(results):
    """
    Student prompt: "{doc}"
    Visualization type: Data Table
    """
    print()
    print(f"  {{'College':<26}} {{'Score':>6}}  {{'SAT Median':>10}}  {{'Net Cost/yr':>12}}")
    print("  " + "─" * 60)
    for r in results:
        net = r["tuition"] - r["avg_financial_aid"]
        print(f"  {{r['name'][:25]:<26}} {{r['score']:>5}}%  {{r['sat_range']:>10}}  ${{net:>11,.0f}}")
    print()
    best_value = min(results, key=lambda x: x["tuition"] - x["avg_financial_aid"])
    print(f"  💰 Best value: {{best_value['name']}} (net ${{best_value['tuition']-best_value['avg_financial_aid']:,.0f}}/yr)")
    print()'''

    elif viz_type == "comparison":
        return f'''\
def show_visual(results):
    """
    Student prompt: "{doc}"
    Visualization type: Score vs SAT Comparison
    """
    print()
    print("  ⚖️   Match Score  vs  SAT Median")
    print("  " + "─" * 54)
    for r in results:
        score_bar = "█" * (r["score"] // 10)
        sat_bar   = "█" * min(r["sat_range"] // 160, 10)
        print(f"  {{r['name'][:22]:<22}}")
        print(f"    Match  [{{score_bar:<10}}] {{r['score']}}%")
        print(f"    SAT    [{{sat_bar:<10}}] {{r['sat_range']}} median")
        accept = r.get('acceptance_rate', 0)
        print(f"    Admit  {{accept*100:.0f}}% acceptance rate")
        print()'''

    elif viz_type == "cost":
        return f'''\
def show_visual(results):
    """
    Student prompt: "{doc}"
    Visualization type: Cost Breakdown
    """
    print()
    print("  💰  Tuition vs What You Actually Pay (after aid)")
    print("  " + "─" * 58)
    print(f"  {{'College':<24}} {{'Sticker':>10}}  {{'Aid':>10}}  {{'You Pay':>10}}")
    print("  " + "─" * 58)
    for r in sorted(results, key=lambda x: x["tuition"] - x["avg_financial_aid"]):
        net = r["tuition"] - r["avg_financial_aid"]
        savings_bar = "▓" * min(int(r["avg_financial_aid"] / 5000), 10)
        print(f"  {{r['name'][:23]:<24}} ${{r['tuition']:>9,.0f}}  ${{r['avg_financial_aid']:>9,.0f}}  ${{net:>9,.0f}}")
        print(f"  {{'':<24}}  Aid: [{{savings_bar:<10}}]")
    print()
    best = min(results, key=lambda x: x["tuition"] - x["avg_financial_aid"])
    print(f"  ✅ Most affordable: {{best['name']}} — net ${{best['tuition']-best['avg_financial_aid']:,.0f}}/yr")
    print()'''

    elif viz_type == "tier_summary":
        return f'''\
def show_visual(results):
    """
    Student prompt: "{doc}"
    Visualization type: Safety / Match / Reach Summary
    """
    tiers = {{"Safety": [], "Match": [], "Reach": []}}
    for r in results:
        t = r.get("tier", "Match")
        if t in tiers:
            tiers[t].append(r)
    print()
    print("  🎯  Your College List — Strategic Overview")
    print("  " + "─" * 52)
    for tier_name, colleges in tiers.items():
        if not colleges:
            continue
        avg_score = sum(c["score"] for c in colleges) / len(colleges)
        emoji = {{"Safety": "🟢", "Match": "🟡", "Reach": "🔴"}}.get(tier_name, "⚪")
        print(f"  {{emoji}} {{tier_name}} ({{len(colleges)}} school(s) — avg {{avg_score:.0f}}% match)")
        for c in colleges:
            print(f"     • {{c['name']}} — {{c['score']}}%")
        print()'''

    else:
        return f'''\
def show_visual(results):
    """
    Student prompt: "{doc}"
    """
    print()
    for r in results:
        print(f"  {{r['name']}} — {{r['score']}}% match")
    print()'''


_DATA_SCHEMA = """\
results is a list of dicts. Each dict has:
  name            (str)   college name
  score           (int)   match score 0-100
  category        (str)   "Safety", "Match", or "Reach"
  tier            (str)   same as category
  sat_range       (int)   SAT median (e.g. 1200)
  gpa_range       (str)   median GPA string (e.g. "3.5-3.9")
  tuition         (int)   annual sticker tuition in USD
  avg_financial_aid (int) average annual financial aid in USD
  acceptance_rate (float) fraction 0.0-1.0 (e.g. 0.12 = 12%)
  region          (str)   US region (e.g. "Northeast")
  setting         (str)   "Urban", "Suburban", or "Rural"
  enrollment      (int)   total undergraduate enrollment
  research_score  (int)   research strength 0-100
  campus_energy   (int)   campus social energy 0-100
  support_score   (int)   student support strength 0-100\
"""


def _generate_viz_code_with_ai(viz_type: str, viz_prompt: str) -> str:
    """Call OpenAI to generate a real show_visual(results) Plotly + Streamlit function."""
    import os
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", ""))

        system_msg = (
            "You are an expert Python developer writing code for a high school AI bootcamp. "
            "Generate a single Python function `show_visual(results)` that creates a real interactive chart "
            "for a college recommender Streamlit app using Plotly.\n\n"
            "STRICT RULES:\n"
            "1. Use plotly.graph_objects (import plotly.graph_objects as go) and streamlit (import streamlit as st)\n"
            "2. Create a plotly Figure, then display it with: st.plotly_chart(fig, use_container_width=True)\n"
            "3. Function signature must be exactly: def show_visual(results):\n"
            "4. Use .get() for all dict access — never assume a key exists\n"
            "5. 'results' is a list of dicts with keys: name, score, category, region, tuition, avg_financial_aid, acceptance_rate, sat_range\n"
            "6. Handle empty results gracefully with an early return\n"
            "7. Return ONLY the function code — no markdown, no backticks, no extra text\n"
            "8. Honor any color, style, or design preferences from the student's prompt\n"
            "9. Make the chart look polished and informative for high school students\n"
            "10. net cost = tuition - avg_financial_aid\n"
        )

        user_msg = (
            f"Visualization type chosen: {viz_type}\n\n"
            f"Student's design prompt:\n\"{viz_prompt}\"\n\n"
            f"Available data fields in each result dict:\n{_DATA_SCHEMA}\n\n"
            "Generate the show_visual(results) function now using plotly and streamlit."
        )

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.4,
            max_tokens=900,
        )
        raw = resp.choices[0].message.content.strip()
        # Strip markdown fences if GPT wraps in ```python
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(l for l in lines if not l.startswith("```"))
        return raw.strip()
    except Exception as e:
        return ""


def _render_card(college: dict, headline_template: str, show_fields: list, hero_stat: str):
    headline = (
        headline_template
        .replace("{rank}", str(college["rank"]))
        .replace("{college}", college["name"])
        .replace("{score}", str(college["score"]))
        .replace("{tier}", college["tier"])
    ) if headline_template else f"#{college['rank']} — {college['name']}"

    net_cost = college["tuition"] - college["avg_financial_aid"]

    field_values = {
        "match_score":     f"**Match Score:** {college['score']}%",
        "sat_median":      f"**SAT Median:** {college['sat_range']}",
        "net_cost":        f"**Est. Net Cost:** ${net_cost:,.0f}/yr",
        "acceptance_rate": f"**Acceptance Rate:** {college['acceptance_rate']*100:.0f}%",
        "region":          f"**Region:** {college['region']}",
        "setting":         f"**Setting:** {college['setting']}",
        "enrollment":      f"**Enrollment:** {college['enrollment']:,}",
        "financial_aid":   f"**Avg Aid:** ${college['avg_financial_aid']:,}",
    }

    with st.container(border=True):
        st.markdown(f"### {headline}")

        # Hero stat (full width, prominent)
        if hero_stat in field_values:
            st.markdown(f"#### {field_values[hero_stat]}")

        # Supporting fields (2-column grid)
        support = [f for f in show_fields if f != hero_stat and f in field_values]
        if support:
            c1, c2 = st.columns(2)
            for i, f in enumerate(support):
                (c1 if i % 2 == 0 else c2).markdown(field_values[f])
