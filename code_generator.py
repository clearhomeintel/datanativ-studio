"""
code_generator.py
Converts a student's DataNativ project data into a real, runnable Python script.
All six project types use the college Excel as their data source.
The generated script grows each week as the student completes more tasks.
"""

import re
import json
import os


# ── helpers ──────────────────────────────────────────────────────────────────

def _to_var(label: str) -> str:
    """'GPA (weighted)' → 'gpa_weighted'"""
    s = label.lower()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    s = re.sub(r"_+", "_", s).strip("_")
    if not s:
        return "input_var"
    if s[0].isdigit():
        s = "q_" + s
    return s[:28]


def _to_const(label: str) -> str:
    """'Academic Fit' → 'ACADEMIC_FIT_WEIGHT'"""
    s = label.upper()
    s = re.sub(r"[^A-Z0-9\s]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    s = re.sub(r"_+", "_", s).strip("_")
    return (s or "FACTOR")[:26] + "_WEIGHT"


def _parse_inputs(week2_data: dict) -> list:
    """Parse only what the student actually typed. Never use template defaults."""
    raw = week2_data.get("input_questions", "")
    if not raw or not raw.strip():
        return []
    lines = [l.strip().lstrip("-•*0123456789.)").strip() for l in raw.split("\n") if l.strip()]
    if len(lines) >= 2:
        return [l for l in lines if l][:6]
    # Comma-separated single line
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts[:6]


def _parse_factors(week2_data: dict) -> dict:
    """Parse only what the student actually typed. Never use template defaults."""
    raw = week2_data.get("scoring_factors", "")
    if not raw or not raw.strip():
        return {}
    factors = {}
    for line in raw.strip().split("\n"):
        line = line.strip()
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            try:
                factors[k] = int(float(v.strip().replace("%", "")))
            except Exception:
                pass
    if not factors:
        return {}
    # Normalise to 100 if needed
    total = sum(factors.values())
    if total > 0 and total != 100:
        scale = 100 / total
        factors = {k: round(v * scale) for k, v in factors.items()}
        diff = 100 - sum(factors.values())
        if diff != 0:
            first = next(iter(factors))
            factors[first] += diff
    return factors


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "")


def _sanitize_action_plan_prompt(prompt: str) -> str:
    """
    Auto-fix common bracket typos in action plan prompts so Python's str.format() works.
    Students often type (var), [var}, {var) instead of {var}.
    Recognizes the five supported placeholder names.
    """
    for var in ["college_name", "match_score", "acceptance_rate", "region", "gaps"]:
        prompt = re.sub(
            r'[\(\[\{]' + re.escape(var) + r'[\)\]\}]',
            '{' + var + '}',
            prompt,
        )
    return prompt


# ── real college data ─────────────────────────────────────────────────────────

def _load_college_data() -> list:
    """Load real college data from the JSON cache (built from the Excel file)."""
    cache_path = os.path.join(os.path.dirname(__file__), "college_data_cache.json")
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            return json.load(f)
    return []


def _colleges_as_python_literal(colleges: list, project_type: str) -> str:
    """
    Render the college list as a Python literal with pre-computed dimension scores
    relevant to the project type. All project types use the same 42-college dataset
    but score colleges on different attributes.
    """
    lines = ["COLLEGE_DATA = ["]
    for c in colleges:
        name            = c.get("name", "")
        acceptance_rate = c.get("acceptance_rate", 0.20)
        sat_range       = c.get("sat_range", 1200)
        act_range       = c.get("act_range", 28)
        tuition         = c.get("tuition", 55000)
        avg_aid         = c.get("avg_financial_aid", 30000)
        enrollment      = c.get("enrollment", 5000)
        region          = c.get("region", "")
        setting         = c.get("setting", "Suburban")
        cds             = c.get("cds_factors", {})

        # Derived scores 0-100 (used by all project types, weighted differently)
        # academic_selectivity: how demanding academically
        academic_selectivity = min(100, int((1 - acceptance_rate) * 80 + (sat_range - 900) / 8))
        academic_selectivity = max(0, academic_selectivity)

        # financial_accessibility: how affordable (higher = more accessible)
        net_cost = max(0, tuition - avg_aid)
        financial_accessibility = max(0, min(100, int(100 - net_cost / 700)))

        # campus_energy: vibrancy of campus life (large urban = higher)
        size_score = min(100, enrollment / 400)
        setting_bonus = {"Urban": 20, "Suburban": 10, "College Town": 15, "Rural": 0}.get(setting, 10)
        campus_energy = min(100, int(size_score + setting_bonus))

        # support_personalization: how much individual support students get (smaller schools score higher)
        support = max(0, min(100, int(100 - enrollment / 450 + avg_aid / 1000)))

        # research_reputation: selectivity × SAT proxy for research strength
        research_score = min(100, int(academic_selectivity * 0.7 + (sat_range - 900) / 10))
        research_score = max(0, research_score)

        # extracurricular_richness: based on enrollment size + CDS extracurriculars weight
        cds_ec = cds.get("extracurriculars", 2)  # 1=considered, 2=important, 3=very important
        extracurricular = min(100, int(size_score * 0.5 + cds_ec * 20 + setting_bonus * 0.5))

        lines.append(
            f'    {{'
            f'"name": "{_escape(name)}", '
            f'"region": "{region}", '
            f'"setting": "{setting}", '
            f'"sat_range": {sat_range}, '
            f'"act_range": {act_range}, '
            f'"acceptance_rate": {acceptance_rate}, '
            f'"tuition": {tuition}, '
            f'"avg_financial_aid": {avg_aid}, '
            f'"enrollment": {enrollment}, '
            f'"academic_selectivity": {academic_selectivity}, '
            f'"financial_accessibility": {financial_accessibility}, '
            f'"campus_energy": {campus_energy}, '
            f'"support_score": {support}, '
            f'"research_score": {research_score}, '
            f'"extracurricular_score": {extracurricular}'
            f'}},'
        )
    lines.append("]")
    return "\n".join(lines)


def _sample_user_dict(inputs: list) -> str:
    sample_vals = {
        "gpa": 3.7, "sat": 1250, "act": 28, "budget": 35000, "cost": 35000,
        "location": '"Northeast"', "region": '"Northeast"', "size": '"Medium"',
        "major": '"Computer Science"', "style": '"Visual"', "type": '"Research"',
        "hours": 10, "time": 10, "level": '"Intermediate"', "goal": '"College Prep"',
        "interest": '"STEM"', "personality": '"Introvert"', "score": 1200,
    }
    lines = []
    for inp in inputs:
        key = _to_var(inp)
        matched = False
        for hint, val in sample_vals.items():
            if hint in key:
                lines.append(f'    "{key}": {val},')
                matched = True
                break
        if not matched:
            lines.append(f'    "{key}": "sample value",')
    return "{\n" + "\n".join(lines) + "\n}"


# ── project-type-specific scoring logic ──────────────────────────────────────

def _scoring_body(project_type: str, factors: dict) -> str:
    """
    Generate the body of calculate_score() for each project type.
    Uses real college attributes (academic_selectivity, financial_accessibility, etc.)
    weighted by whatever weights the student defined in Week 2.
    """
    factor_items = list(factors.items())
    consts = [_to_const(k) for k, _ in factor_items]
    factor_names = [k for k, _ in factor_items]

    # Map the student's factor names to real college attributes
    ATTR_MAP = {
        # Academic / selectivity keywords → academic_selectivity
        "academic": "academic_selectivity",
        "gpa": "academic_selectivity",
        "sat": "academic_selectivity",
        "test": "academic_selectivity",
        "rigor": "academic_selectivity",
        "grade": "academic_selectivity",
        "selectiv": "academic_selectivity",
        # Financial keywords → financial_accessibility
        "financ": "financial_accessibility",
        "budget": "financial_accessibility",
        "cost": "financial_accessibility",
        "afford": "financial_accessibility",
        "aid": "financial_accessibility",
        "tuition": "financial_accessibility",
        # Culture / campus life keywords → campus_energy
        "culture": "campus_energy",
        "campus": "campus_energy",
        "life": "campus_energy",
        "vibe": "campus_energy",
        "energy": "campus_energy",
        "social": "campus_energy",
        "activit": "campus_energy",
        # Size / support keywords → support_score
        "size": "support_score",
        "support": "support_score",
        "personal": "support_score",
        "mentor": "support_score",
        "small": "support_score",
        "time": "support_score",
        # Research / innovation → research_score
        "research": "research_score",
        "innovat": "research_score",
        "passion": "research_score",
        "project": "research_score",
        # Extracurricular → extracurricular_score
        "extracurric": "extracurricular_score",
        "club": "extracurricular_score",
        "activit": "extracurricular_score",
        "leader": "extracurricular_score",
        "goal": "extracurricular_score",
        # Location → location match
        "location": "location",
        "region": "location",
        "geographic": "location",
    }

    def best_attr(factor_name: str) -> str:
        fn_lower = factor_name.lower()
        for keyword, attr in ATTR_MAP.items():
            if keyword in fn_lower:
                return attr
        return "academic_selectivity"  # default fallback

    lines = [
        "    score = 0.0",
        "",
    ]

    for (factor_name, weight), const in zip(factor_items, consts):
        attr = best_attr(factor_name)
        if attr == "location":
            lines += [
                f"    # {factor_name} ({weight}%)",
                f"    user_region = user_input.get(\"region\", user_input.get(\"location\", \"\"))",
                f"    location_score = 100 if college.get(\"region\", \"\") == user_region else 50",
                f"    score += location_score * ({const} / 100)",
                "",
            ]
        else:
            lines += [
                f"    # {factor_name} ({weight}%)",
                f"    score += college.get(\"{attr}\", 50) * ({const} / 100)",
                "",
            ]

    lines += [
        "    return round(min(score, 100))",
    ]
    return "\n".join(lines)


# ── AI prompts section ────────────────────────────────────────────────────────

def _ai_prompts_section(project_type: str) -> str:
    return f'''# {"─"*56}
# SECTION 9  AI PROMPTS  (optional — requires OpenAI API key)
#   These are the exact prompts sent to the AI model.
#   Edit them to change how the AI explains recommendations
#   to your users. The prompts are plain text — no special syntax.
# {"─"*56}

AI_ENABLED = False   # Set to True and add your API key below

AI_API_KEY = "YOUR_OPENAI_API_KEY_HERE"   # Replace with your key

AI_EXPLAIN_PROMPT = """
You are a helpful advisor for a {project_type} recommendation app.
A student received this recommendation: {{result_name}} (match score: {{score}}%).
Their answers were: {{user_inputs}}.

Write 2-3 friendly sentences explaining WHY this is a great match.
Be specific — mention their actual inputs. Sound like a knowledgeable friend.
Keep it under 80 words.
"""

AI_NO_KEY_FALLBACK = "{{result_name}} scored {{score}}% — a strong match based on your profile."


def get_ai_explanation(result: dict, user_input: dict) -> str:
    """
    Optional: Generate an AI explanation for a recommendation.
    Set AI_ENABLED = True and fill in AI_API_KEY to use this.
    Students: edit AI_EXPLAIN_PROMPT above to change what the AI says.
    """
    if not AI_ENABLED:
        # Use the fallback text when AI is off
        return AI_NO_KEY_FALLBACK.format(
            result_name=result.get("name", "this option"),
            score=result.get("score", 0)
        )
    try:
        import openai
        client = openai.OpenAI(api_key=AI_API_KEY)
        prompt = AI_EXPLAIN_PROMPT.format(
            result_name=result.get("name", ""),
            score=result.get("score", 0),
            user_inputs=str(user_input)
        )
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{{"role": "user", "content": prompt}}],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI explanation unavailable: {{e}}"
'''


# ── main generator ────────────────────────────────────────────────────────────

def generate_app_code(student: dict) -> str:
    """
    Generate the full Python app code from a student's project data.
    Routes to the new format generator for Week 2-redesigned students.
    """
    from project_templates import PROJECT_TEMPLATES

    week2 = student.get("week2_data", {})
    if isinstance(week2, str):
        try:
            week2 = json.loads(week2)
        except Exception:
            week2 = {}

    # ── Route to new-format generator ────────────────────────────────────────
    if _is_new_format(week2):
        # Ensure all week data is parsed from JSON if stored as strings
        _student = dict(student)
        for wk in ("week1_data", "week2_data", "week3_data", "week4_data", "config"):
            val = _student.get(wk, {})
            if isinstance(val, str):
                try:
                    _student[wk] = json.loads(val)
                except Exception:
                    _student[wk] = {}
        _student["week2_data"] = week2
        return _generate_new_format_code(_student)

    # ── Legacy path (old format with input_questions / scoring_factors) ───────
    project_type = student.get("project_type", "Recommender App")
    template     = PROJECT_TEMPLATES.get(project_type, {})
    config       = student.get("config", {})
    week1        = student.get("week1_data", {})
    week3        = student.get("week3_data", {})
    progress     = student.get("week_progress", {})
    features     = student.get("features", [])
    if isinstance(features, str):
        try:
            features = json.loads(features)
        except Exception:
            features = []

    name         = student.get("name", "Student")
    app_title    = config.get("app_title", template.get("title", f"My {project_type}"))
    target_user  = student.get("target_user", template.get("target_user", "students"))
    tone         = student.get("tone", template.get("default_tone", "Friendly & Direct"))
    intro_text   = config.get("intro_text", template.get("intro_text", "Answer a few questions to get started."))
    problem      = week1.get("problem_statement", student.get("problem", template.get("problem", "")))
    categories   = template.get("recommendation_categories", ["Best Fit", "Good Option", "Backup"])

    w3_done = progress.get("week3", False)

    # ── Content-based checks: sections only appear when the student typed them ──
    # We NEVER use template defaults as "the student's code."
    inputs  = _parse_inputs(week2)    # [] if student hasn't typed anything yet
    factors = _parse_factors(week2)   # {} if student hasn't typed anything yet
    has_inputs      = bool(inputs)
    has_factors     = bool(factors)
    show_full_logic = has_inputs and has_factors   # need both for scoring engine

    # Load real college data from the Excel cache
    colleges = _load_college_data()

    lines = []

    # ─── HEADER ───────────────────────────────────────────────────────────────
    lines += [
        f'# {"="*58}',
        f'#  {_escape(app_title)}',
        f'#  Built with DataNativ Studio — AI Bootcamp Project',
        f'# {"="*58}',
        f'# Builder      : {_escape(name)}',
        f'# Project type : {_escape(project_type)}',
        f'# Data source  : Real college data — 42 colleges from the CDS Excel',
        f'# Problem solved:',
        f'#   {_escape(problem[:120]) if problem else "(complete Week 1 to define your problem)"}',
        f'# Who it helps : {_escape(target_user[:80])}',
        f'# Tone / Voice : {_escape(tone)}',
        f'# {"="*58}',
        f'',
    ]

    # ─── SECTION 1 · APP CONFIGURATION ───────────────────────────────────────
    lines += [
        f'# {"─"*56}',
        f'# SECTION 1  APP CONFIGURATION',
        f'#   From your project setup (Week 1).',
        f'#   Edit the strings in quotes to change what users see.',
        f'# {"─"*56}',
        f'APP_TITLE   = "{_escape(app_title)}"',
        f'TARGET_USER = "{_escape(target_user[:100])}"',
        f'TONE        = "{_escape(tone)}"',
        f'APP_TAGLINE = "{_escape(intro_text[:120])}"',
        f'PROJECT_TYPE = "{_escape(project_type)}"',
        f'',
    ]

    # ─── SECTION 2 · INPUT LABELS ─────────────────────────────────────────────
    if has_inputs:
        # Student typed their questions in Week 2
        override_block = week3.get("input_labels_block") if w3_done else None
        lines += [
            f'# {"─"*56}',
            f'# SECTION 2  INPUT LABELS',
            f'#   One variable per question your app asks users.',
            f'#   You defined these in Week 2, Task 1.',
            f'#   Edit the strings in quotes to change what users see.',
            f'# {"─"*56}',
        ]
        if override_block:
            lines += override_block.split("\n")
        else:
            for inp in inputs:
                var = _to_var(inp)
                clean = _escape(inp)
                lines.append(f'{var}_label = "{clean}"')
        lines.append("")
    else:
        lines += [
            f'# {"─"*56}',
            f'# SECTION 2  INPUT LABELS',
            f'#   ➡  TODO Week 2, Task 1: Define the questions your app asks users.',
            f'#   Example format (one per line):',
            f'#     What is your GPA?',
            f'#     What is your SAT score?',
            f'#     What region do you prefer?',
            f'#   Once you save Task 1, these will appear here as real Python variables.',
            f'# {"─"*56}',
            f'',
        ]

    # ─── SECTION 3 · SCORING WEIGHTS ─────────────────────────────────────────
    if has_factors:
        # Student typed their scoring factors in Week 2
        override_block = week3.get("scoring_block") if w3_done else None
        consts = []
        lines += [
            f'# {"─"*56}',
            f'# SECTION 3  SCORING WEIGHTS',
            f'#   You defined these in Week 2, Task 3.',
            f'#   These control how much each factor matters — must add up to 100.',
            f'# {"─"*56}',
        ]
        if override_block:
            lines += override_block.split("\n")
            for ln in override_block.split("\n"):
                m = re.match(r"([A-Z_]+_WEIGHT)\s*=", ln)
                if m:
                    consts.append(m.group(1))
        else:
            for factor, weight in factors.items():
                const = _to_const(factor)
                consts.append(const)
                lines.append(f'{const} = {weight}   # {_escape(factor)}')
        lines += [
            f'',
            f'# Sanity-check: weights should sum to 100',
            f'_weight_total = {" + ".join(consts) if consts else "100"}',
            f'if abs(_weight_total - 100) > 1:',
            f'    print(f"⚠️  Weights sum to {{_weight_total}}, not 100. Fix them above.")',
            f'',
        ]
    else:
        lines += [
            f'# {"─"*56}',
            f'# SECTION 3  SCORING WEIGHTS',
            f'#   ➡  TODO Week 2, Task 3: Define your scoring factors and weights.',
            f'#   Example format (one per line, must total 100):',
            f'#     Academic Fit: 35%',
            f'#     Financial Fit: 30%',
            f'#     Campus Culture: 20%',
            f'#     Location: 15%',
            f'#   Once you save Task 3, these will appear here as Python constants.',
            f'# {"─"*56}',
            f'',
        ]

    # ─── SECTION 4 · RECOMMENDATION CATEGORIES ───────────────────────────────
    # Categories come from your project template — always visible to rename.
    override_block = week3.get("categories_block") if w3_done else None
    lines += [
        f'# {"─"*56}',
        f'# SECTION 4  RECOMMENDATION CATEGORIES',
        f'#   Labels for grouping your results (from your project template).',
        f'#   Rename the strings to match your app\'s voice.',
        f'# {"─"*56}',
    ]
    if override_block:
        lines += override_block.split("\n")
    else:
        for i, cat in enumerate(categories[:3], 1):
            lines.append(f'CATEGORY_{i} = "{_escape(cat)}"')
    lines.append("")

    # ─── SECTION 5 · REAL COLLEGE DATA ───────────────────────────────────────
    # Only embed full college data once student has defined their scoring logic.
    if show_full_logic:
        if colleges:
            lines += [
                f'# {"─"*56}',
                f'# SECTION 5  COLLEGE DATA  (42 real colleges from the CDS Excel)',
                f'#   This is the dataset your app scores and recommends from.',
                f'#   Each college has: SAT range, acceptance rate, tuition, aid,',
                f'#   enrollment, region, setting, and pre-computed dimension scores.',
                f'#   Do NOT edit this section — it comes from the real Excel file.',
                f'# {"─"*56}',
            ]
            lines.append(_colleges_as_python_literal(colleges, project_type))
            lines.append("")
        else:
            lines += [
                f'# {"─"*56}',
                f'# SECTION 5  COLLEGE DATA',
                f'#   (college_data_cache.json not found — restart the app to generate it)',
                f'# {"─"*56}',
                f'COLLEGE_DATA = []',
                f'',
            ]
    else:
        lines += [
            f'# {"─"*56}',
            f'# SECTION 5  COLLEGE DATA',
            f'#   ➡  This section will appear after you complete both',
            f'#      Week 2 Task 1 (input questions) AND Task 3 (scoring factors).',
            f'#   The 42 real colleges from the Excel will be embedded here.',
            f'# {"─"*56}',
            f'',
        ]

    # ─── SECTION 6 · SCORING FUNCTION ────────────────────────────────────────
    if show_full_logic:
        override_block = week3.get("scoring_function_block") if w3_done else None
        lines += [
            f'# {"─"*56}',
            f'# SECTION 6  SCORING FUNCTION',
            f'#   Built from your Week 2 scoring factors.',
            f'#   It scores each college against the user\'s answers.',
            f'#   Each factor uses real college attributes, weighted by',
            f'#   the constants you set in Section 3.',
            f'# {"─"*56}',
            f'def calculate_score(user_input: dict, college: dict) -> int:',
            f'    """',
            f'    Returns a match score 0-100 for how well this college fits',
            f'    the user\'s profile. Higher = better match.',
            f'    """',
        ]
        if override_block:
            lines += override_block.split("\n")
        else:
            lines += _scoring_body(project_type, factors).split("\n")
        lines += [
            f'',
            f'',
            f'def get_category(score: int) -> str:',
            f'    """Map a score to a recommendation category."""',
            f'    if score >= 75:',
            f'        return CATEGORY_{min(3, len(categories))}   # top tier',
            f'    elif score >= 50:',
            f'        return CATEGORY_2   # mid tier',
            f'    else:',
            f'        return CATEGORY_1   # starter tier',
            f'',
        ]
    else:
        lines += [
            f'# {"─"*56}',
            f'# SECTION 6  SCORING FUNCTION',
            f'#   ➡  TODO Week 2: Complete both Task 1 and Task 3 to generate',
            f'#      your scoring function. It will use your actual factors and weights.',
            f'# {"─"*56}',
            f'',
        ]

    # ─── SECTION 7 · RECOMMEND FUNCTION ──────────────────────────────────────
    if show_full_logic:
        lines += [
            f'# {"─"*56}',
            f'# SECTION 7  RECOMMEND FUNCTION',
            f'#   Loops over all 42 colleges, scores each one,',
            f'#   and returns the top 3 ranked by match score.',
            f'# {"─"*56}',
            f'def recommend(user_input: dict, colleges: list = COLLEGE_DATA) -> list:',
            f'    results = []',
            f'    for college in colleges:',
            f'        score    = calculate_score(user_input, college)',
            f'        category = get_category(score)',
            f'        results.append({{',
            f'            "name"             : college["name"],',
            f'            "score"            : score,',
            f'            "category"         : category,',
            f'            "region"           : college.get("region", ""),',
            f'            "tuition"          : college.get("tuition", 0),',
            f'            "avg_financial_aid": college.get("avg_financial_aid", 0),',
            f'            "acceptance_rate"  : college.get("acceptance_rate", 0),',
            f'            "sat_range"        : college.get("sat_range", 0),',
            f'        }})',
            f'    results.sort(key=lambda x: x["score"], reverse=True)',
            f'    return results[:3]',
            f'',
        ]
    else:
        lines += [
            f'# {"─"*56}',
            f'# SECTION 7  RECOMMEND FUNCTION',
            f'#   ➡  Will be generated after Week 2 Tasks 1 and 3 are complete.',
            f'# {"─"*56}',
            f'',
        ]

    # ─── SECTION 8 · OUTPUT TEXT ──────────────────────────────────────────────
    output_desc_typed = week2.get("output_description", "").strip()
    if has_inputs or has_factors:
        override_block = week3.get("output_text_block") if w3_done else None
        results_header  = f"Your Top {project_type} Matches"
        results_subtext = output_desc_typed if output_desc_typed else "Based on your answers, here are your best matches."
        lines += [
            f'# {"─"*56}',
            f'# SECTION 8  OUTPUT / RESULTS TEXT',
            f'#   What users read after getting their results.',
            f'#   Edit the strings in quotes to match your app\'s voice.',
            f'# {"─"*56}',
        ]
        if override_block:
            lines += override_block.split("\n")
        else:
            lines += [
                f'results_header  = "{_escape(results_header)}"',
                f'results_subtext = "{_escape(results_subtext[:120])}"',
                f'no_results_text = "Try adjusting your answers — we\'ll find better matches!"',
            ]
        lines.append("")
    else:
        lines += [
            f'# {"─"*56}',
            f'# SECTION 8  OUTPUT / RESULTS TEXT',
            f'#   ➡  TODO Week 2, Task 4: Describe what users see after getting results.',
            f'# {"─"*56}',
            f'',
        ]

    # ─── SECTION 9 · AI PROMPTS ──────────────────────────────────────────────
    if show_full_logic:
        lines += [""]
        lines += _ai_prompts_section(project_type).split("\n")
        lines.append("")
    else:
        lines += [
            f'# {"─"*56}',
            f'# SECTION 9  AI PROMPTS',
            f'#   ➡  Will appear after Week 2 is complete.',
            f'#   You\'ll be able to edit the exact prompt the AI uses to explain results.',
            f'# {"─"*56}',
            f'',
        ]

    # ─── SECTION 10 · SAMPLE USER + MAIN ─────────────────────────────────────
    if show_full_logic:
        sample_user_str = _sample_user_dict(inputs)
        lines += [
            f'# {"─"*56}',
            f'# SECTION 10  SAMPLE USER INPUT + TEST RUN',
            f'#   Edit sample_user to test different scenarios.',
            f'#   In your Streamlit app, these values come from',
            f'#   real st.text_input() / st.slider() widgets.',
            f'# {"─"*56}',
            f'sample_user = {sample_user_str}',
            f'',
            f'# ─────────────────────────────────────',
            f'# MAIN  Run the recommendation engine',
            f'# ─────────────────────────────────────',
            f'if __name__ == "__main__":',
            f'    print()',
            f'    print("=" * 56)',
            f'    print(f"  {{APP_TITLE}}")',
            f'    print("=" * 56)',
            f'    print(f"  {{APP_TAGLINE}}")',
            f'    print()',
            f'    print(f"  Built for: {{TARGET_USER}}")',
            f'    print(f"  Data: {{len(COLLEGE_DATA)}} real colleges from the CDS Excel")',
            f'    print()',
            f'    print("  Scoring with sample user profile...")',
            f'    print()',
            f'',
            f'    results = recommend(sample_user)',
            f'',
            f'    print("─" * 56)',
            f'    print("  TOP RECOMMENDATIONS")',
            f'    print("─" * 56)',
            f'    for i, r in enumerate(results, 1):',
            f'        filled = "█" * (r["score"] // 10)',
            f'        empty  = "░" * (10 - r["score"] // 10)',
            f'        net_cost = r["tuition"] - r["avg_financial_aid"]',
            f'        print()',
            f'        print(f"  #{{i}}  {{r[\'name\']}}")',
            f'        print(f"      Score    : [{{filled}}{{empty}}] {{r[\'score\']}}%  |  Category: {{r[\'category\']}}")',
            f'        print(f"      Region   : {{r[\'region\']}}")',
            f'        print(f"      Net Cost : ${{net_cost:,.0f}} / yr  |  SAT range: {{r[\'sat_range\']}}")',
            f'        print(f"      Acceptance: {{r[\'acceptance_rate\']*100:.0f}}%")',
            f'        print(f"      AI note  : {{get_ai_explanation(r, sample_user)}}")',
            f'',
            f'    print()',
            f'    print("─" * 56)',
            f'    print(f"  {{results_subtext}}")',
            f'    print("─" * 56)',
            f'    print()',
        ]
    elif has_inputs or has_factors:
        # Week 2 partially complete — show what exists
        lines += [
            f'# {"─"*56}',
            f'# MAIN',
            f'# {"─"*56}',
            f'if __name__ == "__main__":',
            f'    print()',
            f'    print("=" * 56)',
            f'    print(f"  {{APP_TITLE}}")',
            f'    print("=" * 56)',
            f'    print(f"  {{APP_TAGLINE}}")',
            f'    print()',
            f'    print(f"  Built to help: {{TARGET_USER}}")',
            f'    print()',
            f'    print("  ✅ Week 2 in progress — keep going!")',
            ('    print("  ✅ Input labels defined (Task 1 done)")' if has_inputs
             else '    print("  ➡  Task 1: Define your input questions")'),
            ('    print("  ✅ Scoring weights defined (Task 3 done)")' if has_factors
             else '    print("  ➡  Task 3: Define your scoring factors and weights")'),
            f'    print()',
            f'    print("  Complete both Tasks 1 and 3 to unlock your scoring engine.")',
            f'    print()',
        ]
    else:
        # Only Week 1 done
        lines += [
            f'# {"─"*56}',
            f'# MAIN',
            f'# {"─"*56}',
            f'if __name__ == "__main__":',
            f'    print()',
            f'    print("=" * 56)',
            f'    print(f"  {{APP_TITLE}}")',
            f'    print("=" * 56)',
            f'    print(f"  {{APP_TAGLINE}}")',
            f'    print()',
            f'    print(f"  Built to help: {{TARGET_USER}}")',
            f'    print()',
            f'    print("  ✅ Week 1 complete — your app skeleton is ready!")',
            f'    print("  ➡  Head to Week 2 to define your input questions and scoring logic.")',
            f'    print()',
        ]

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# NEW FORMAT SUPPORT  (Week 2 redesign: std inputs + passion + pool weights)
# ═══════════════════════════════════════════════════════════════════════════════

def _is_new_format(week2_data: dict) -> bool:
    return (
        "std_gpa_enabled" in week2_data
        or "academic_pool_weight" in week2_data
        or "passion_inputs_text" in week2_data
        or "passion_questions" in week2_data
    )


def _parse_passion_inputs(week2_data: dict) -> list:
    # New structured passion_questions format (from redesigned Task 2)
    if "passion_questions" in week2_data:
        raw = week2_data["passion_questions"]
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = []
        result = []
        for q in (raw or []):
            kw_map = q.get("active_keywords", {})
            if isinstance(kw_map, dict) and kw_map and q.get("question"):
                result.append({"question": q["question"], "keyword_map": kw_map})
        return result

    # Legacy passion_inputs_text format
    text = week2_data.get("passion_inputs_text", "")
    questions, current_q, current_map = [], None, {}
    for line in text.split("\n"):
        s = line.strip()
        if s.lower().startswith("question:"):
            if current_q:
                questions.append({"question": current_q, "keyword_map": current_map})
            current_q, current_map = s.split(":", 1)[1].strip(), {}
        elif "→" in s and current_q:
            parts = s.split("→", 1)
            kw, attr = parts[0].strip().lstrip("-• "), parts[1].strip()
            if kw and attr:
                current_map[kw] = attr
    if current_q:
        questions.append({"question": current_q, "keyword_map": current_map})
    return questions


def _std_input_defaults():
    return [
        {"key": "gpa",        "label": "GPA (unweighted, 0–4.0)",          "default_weight": 35, "on": True},
        {"key": "sat",        "label": "SAT Composite Score (400–1600)",    "default_weight": 30, "on": True},
        {"key": "act",        "label": "ACT Composite Score (1–36)",        "default_weight": 0,  "on": False},
        {"key": "class_rank", "label": "Class Rank Percentile (1=top 1%)", "default_weight": 20, "on": True},
        {"key": "rigor",      "label": "Course Rigor (AP/IB count, 0–10)", "default_weight": 15, "on": True},
    ]


def _detect_viz_type_new(prompt: str) -> str:
    p = (prompt or "").lower()
    if any(w in p for w in ["scatter", "dot plot"]):
        return "scatter"
    if any(w in p for w in ["table", "grid"]):
        return "table"
    if any(w in p for w in ["compare", "comparison", "side by side", "side-by-side"]):
        return "comparison"
    return "bar"


def _gen_viz_function(viz_type: str, viz_prompt: str = "") -> str:
    doc = (viz_prompt.strip().replace('"""', "''") if viz_prompt.strip()
           else f"Show results as a {viz_type} visualization.").replace("\n", " ")[:120]

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
    best = min(results, key=lambda x: x["tuition"] - x["avg_financial_aid"])
    print(f"  💰 Best value: {{best['name']}} — net ${{best['tuition']-best['avg_financial_aid']:,.0f}}/yr")
    print()'''

    elif viz_type == "comparison":
        return f'''\
def show_visual(results):
    """
    Student prompt: "{doc}"
    Visualization type: Score vs SAT Comparison
    """
    print()
    print("  ⚖️   Match Score  vs  SAT Median  vs  Acceptance Rate")
    print("  " + "─" * 58)
    for r in results:
        score_bar = "█" * (r["score"] // 10)
        sat_bar   = "█" * min(r["sat_range"] // 160, 10)
        accept    = r.get("acceptance_rate", 0)
        print(f"  {{r['name'][:22]:<22}}")
        print(f"    Match  [{{score_bar:<10}}] {{r['score']}}%")
        print(f"    SAT    [{{sat_bar:<10}}] {{r['sat_range']}} median")
        print(f"    Admit  {{accept*100:.0f}}% acceptance rate")
        print()'''

    elif viz_type == "cost":
        return f'''\
def show_visual(results):
    """
    Student prompt: "{doc}"
    Visualization type: Cost Breakdown (tuition vs net cost after aid)
    """
    print()
    print("  💰  What You Actually Pay — Tuition vs Net Cost After Aid")
    print("  " + "─" * 62)
    print(f"  {{'College':<24}} {{'Sticker':>10}}  {{'Aid':>10}}  {{'You Pay':>10}}")
    print("  " + "─" * 62)
    for r in sorted(results, key=lambda x: x["tuition"] - x["avg_financial_aid"]):
        net = r["tuition"] - r["avg_financial_aid"]
        print(f"  {{r['name'][:23]:<24}} ${{r['tuition']:>9,.0f}}  ${{r['avg_financial_aid']:>9,.0f}}  ${{net:>9,.0f}}")
    print()
    best = min(results, key=lambda x: x["tuition"] - x["avg_financial_aid"])
    print(f"  ✅ Most affordable: {{best['name']}} (net ${{best['tuition']-best['avg_financial_aid']:,.0f}}/yr)")
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
        t = r.get("category", "Match")
        tiers.setdefault(t, []).append(r)
    print()
    print("  🎯  Your College List — Strategic Overview")
    print("  " + "─" * 52)
    for tier_name, tier_emoji in [("Safety","🟢"),("Match","🟡"),("Reach","🔴")]:
        colleges = tiers.get(tier_name, [])
        if not colleges:
            continue
        avg_score = sum(c["score"] for c in colleges) / len(colleges)
        print(f"  {{tier_emoji}} {{tier_name}} — {{len(colleges)}} school(s), avg {{avg_score:.0f}}% match")
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


def _generate_new_format_code(student: dict) -> str:
    """Generate the full app code for the redesigned 4-week college recommender."""
    week1  = student.get("week1_data", {})
    week2  = student.get("week2_data", {})
    week3  = student.get("week3_data", {})
    week4  = student.get("week4_data", {})
    config = student.get("config", {})

    name        = student.get("name", "Student")
    app_title   = config.get("app_title", "My College Match Finder")
    target_user = student.get("target_user", "high school students")
    tone        = student.get("tone", "Friendly & Direct")
    intro_text  = config.get("intro_text", "Tell us about yourself to find your best-fit colleges.")
    problem     = week1.get("problem_statement", student.get("problem", ""))
    categories  = config.get("recommendation_categories", ["Safety", "Match", "Reach"])

    std_defs    = _std_input_defaults()
    enabled_std = [d for d in std_defs if week2.get(f"std_{d['key']}_enabled", d["on"])]
    passion_qs  = _parse_passion_inputs(week2)
    acad_pct    = int(week2.get("academic_pool_weight", 70))
    passion_pct = int(week2.get("passion_pool_weight",  30))

    has_std      = bool(enabled_std)
    has_passion  = bool(passion_qs)
    has_display  = bool(week3.get("show_fields") or week3.get("headline_template"))
    has_gaps     = bool(week4.get("gap_rules_text", "").strip())
    has_plan     = bool(
        week4.get("action_plan_prompt","").strip()
        or week4.get("plan_60_day","").strip()
        or week4.get("plan_90_day","").strip()
    )
    show_engine  = has_std

    colleges = _load_college_data()
    L = []

    # ── HEADER ────────────────────────────────────────────────────────────────
    L += [
        f'# {"="*58}',
        f'#  {_escape(app_title)}',
        f'#  Built with DataNativ Studio — AI Bootcamp',
        f'# {"="*58}',
        f'# Builder : {_escape(name)}',
        f'# Type    : College Recommender',
        f'# Data    : 42 real colleges (CDS Excel)',
        f'# Problem : {_escape((problem or "(fill in Week 1)")[:110])}',
        f'# {"="*58}',
        f'',
    ]

    # SECTION 1
    L += [
        f'# {"─"*56}',
        f'# SECTION 1  APP CONFIGURATION  (Week 1)',
        f'# {"─"*56}',
        f'APP_TITLE   = "{_escape(app_title)}"',
        f'TARGET_USER = "{_escape(target_user[:100])}"',
        f'TONE        = "{_escape(tone)}"',
        f'APP_TAGLINE = "{_escape(intro_text[:120])}"',
        f'',
    ]

    # SECTION 2 — Standardized Inputs
    if has_std:
        en_consts = []
        L += [
            f'# {"─"*56}',
            f'# SECTION 2  STANDARDIZED ACADEMIC INPUTS  (Week 2, Task 1)',
            f'# {"─"*56}',
        ]
        for d in std_defs:
            k = d["key"]
            c_en = f"STD_{k.upper()}_ENABLED"
            c_wt = f"STD_{k.upper()}_WEIGHT"
            is_on = bool(week2.get(f"std_{k}_enabled", d["on"]))
            wt    = int(week2.get(f"std_{k}_weight",   d["default_weight"]))
            L.append(f'{c_en:<28} = {str(is_on):<5}   # {d["label"]}')
            L.append(f'{c_wt:<28} = {wt}')
            if is_on:
                en_consts.append(c_wt)
        wt_expr = " + ".join(en_consts) if en_consts else "0"
        L += [
            f'',
            f'_acad_weight_sum = {wt_expr}',
            f'if abs(_acad_weight_sum - 100) > 1:',
            f'    print(f"⚠️  Academic weights sum to {{_acad_weight_sum}}, not 100.")',
            f'',
        ]
    else:
        L += [
            f'# {"─"*56}',
            f'# SECTION 2  STANDARDIZED INPUTS',
            f'#   ➡  TODO Week 2, Task 1: Enable academic inputs.',
            f'# {"─"*56}',
            f'',
        ]

    # SECTION 3 — Passion Inputs
    if has_passion:
        L += [
            f'# {"─"*56}',
            f'# SECTION 3  PASSION INPUTS  (Week 2, Task 2)',
            f'#   User text answers → AI semantic scoring → college fit score.',
            f'#   (keyword_map shown for reference; actual scoring uses OpenAI)',
            f'# {"─"*56}',
            f'PASSION_INPUTS = [',
        ]
        for q in passion_qs:
            L.append(f'    {{')
            L.append(f'        "question": "{_escape(q["question"])}",')
            L.append(f'        "keyword_map": {{')
            for kw, attr in q["keyword_map"].items():
                L.append(f'            "{_escape(kw)}": "{_escape(attr)}",')
            L.append(f'        }},')
            L.append(f'    }},')
        L += [f']', f'']
    else:
        L += [
            f'# {"─"*56}',
            f'# SECTION 3  PASSION INPUTS',
            f'#   ➡  TODO Week 2, Task 2: Add keyword-mapped passion questions.',
            f'# {"─"*56}',
            f'PASSION_INPUTS = []',
            f'',
        ]

    # SECTION 4 — Pool Weights
    if has_std:
        L += [
            f'# {"─"*56}',
            f'# SECTION 4  SCORING POOL WEIGHTS  (Week 2, Task 3)',
            f'#   final = (academic × {acad_pct}%) + (passion × {passion_pct}%)',
            f'# {"─"*56}',
            f'ACADEMIC_POOL_WEIGHT = {acad_pct}',
            f'PASSION_POOL_WEIGHT  = {passion_pct}',
            f'if abs(ACADEMIC_POOL_WEIGHT + PASSION_POOL_WEIGHT - 100) > 1:',
            f'    print(f"⚠️  Pool weights sum to {{ACADEMIC_POOL_WEIGHT + PASSION_POOL_WEIGHT}}, not 100.")',
            f'',
        ]
    else:
        L += [
            f'# {"─"*56}',
            f'# SECTION 4  POOL WEIGHTS',
            f'#   ➡  Will appear after Week 2 Task 1 is complete.',
            f'# {"─"*56}',
            f'',
        ]

    # SECTION 5 — Categories
    L += [
        f'# {"─"*56}',
        f'# SECTION 5  RECOMMENDATION CATEGORIES',
        f'# {"─"*56}',
    ]
    for i, cat in enumerate(categories[:3], 1):
        L.append(f'CATEGORY_{i} = "{_escape(cat)}"')
    L.append('')

    # SECTION 6 — College Data
    if show_engine:
        L += [
            f'# {"─"*56}',
            f'# SECTION 6  COLLEGE DATA  (42 real colleges from CDS Excel)',
            f'# {"─"*56}',
        ]
        L.append(_colleges_as_python_literal(colleges, "College Recommender") if colleges else 'COLLEGE_DATA = []')
        L.append('')
    else:
        L += [
            f'# {"─"*56}',
            f'# SECTION 6  COLLEGE DATA',
            f'#   ➡  Unlocks after Week 2 Task 1.',
            f'# {"─"*56}',
            f'',
        ]

    # SECTION 7 — Scoring Functions
    if show_engine:
        L += [
            f'# {"─"*56}',
            f'# SECTION 7  SCORING FUNCTIONS  (built from Week 2)',
            f'# {"─"*56}',
            f'',
            f'def score_academic(user_gpa, user_sat, user_act, user_class_rank, user_rigor, college):',
            f'    """Score academic fit. Returns 0-100."""',
            f'    score, total_w = 0.0, 0.0',
            f'    sel = college.get("academic_selectivity", 50)',
            f'    sat_med = college.get("sat_range", 1200)',
            f'',
        ]
        score_blocks = {
            "gpa":
                ['    if STD_GPA_ENABLED:',
                 '        d = abs(user_gpa - (2.5 + (sel / 100) * 1.5)) / 4.0',
                 '        score += (1 - min(1.0, d * 1.5)) * 100 * STD_GPA_WEIGHT',
                 '        total_w += STD_GPA_WEIGHT'],
            "sat":
                ['    if STD_SAT_ENABLED:',
                 '        d = abs(user_sat - sat_med) / 1200.0',
                 '        score += (1 - min(1.0, d * 1.5)) * 100 * STD_SAT_WEIGHT',
                 '        total_w += STD_SAT_WEIGHT'],
            "act":
                ['    if STD_ACT_ENABLED:',
                 '        d = abs(user_act * 45 - sat_med) / 1200.0',
                 '        score += (1 - min(1.0, d * 1.5)) * 100 * STD_ACT_WEIGHT',
                 '        total_w += STD_ACT_WEIGHT'],
            "class_rank":
                ['    if STD_CLASS_RANK_ENABLED:',
                 '        ideal = 100 - (sel / 100) * 80',
                 '        d = abs(user_class_rank - ideal) / 100.0',
                 '        score += (1 - min(1.0, d * 1.5)) * 100 * STD_CLASS_RANK_WEIGHT',
                 '        total_w += STD_CLASS_RANK_WEIGHT'],
            "rigor":
                ['    if STD_RIGOR_ENABLED:',
                 '        d = abs(user_rigor - (sel / 100) * 10) / 10.0',
                 '        score += (1 - min(1.0, d * 1.5)) * 100 * STD_RIGOR_WEIGHT',
                 '        total_w += STD_RIGOR_WEIGHT'],
        }
        for d in std_defs:
            block = score_blocks.get(d["key"], [])
            L.extend(block)
        L += [
            f'    return score / max(1.0, total_w)',
            f'',
            f'',
            f'import os as _os, json as _json',
            f'from openai import OpenAI as _OpenAI',
            f'_passion_client = _OpenAI(api_key=_os.environ.get("OPENAI_API_KEY", ""))',
            f'# Cache: (question_key, answer_key) -> attribute preference dict',
            f'# GPT runs ONCE per unique answer — not once per college.',
            f'_passion_pref_cache = {{}}',
            f'',
            f'',
            f'def _get_passion_prefs(question: str, answer: str) -> dict:',
            f'    """Ask GPT what college attributes this answer signals — cached per unique answer."""',
            f'    key = (question[:60], answer[:120])',
            f'    if key in _passion_pref_cache:',
            f'        return _passion_pref_cache[key]',
            f'    try:',
            f'        resp = _passion_client.chat.completions.create(',
            f'            model="gpt-4o-mini",',
            f'            messages=[',
            f'                {{"role":"system","content":(',
            f'                    "You are a college admissions counselor. "',
            f'                    "Given a student\'s answer to a question, estimate how strongly they prefer each college attribute. "',
            f'                    "Return ONLY a JSON object with scores 0-100: "',
            f'                    "{{\\\"research_score\\\": N, \\\"campus_energy\\\": N, \\\"support_score\\\": N, \\\"academic_selectivity\\\": N}} "',
            f'                    "where 100 = strongly prefers colleges HIGH in this attribute, 50 = neutral, 0 = prefers LOW."',
            f'                )}},',
            f'                {{"role":"user","content":(',
            f'                    f"Question: {{question}}\\n"',
            f'                    f"Student answer: {{answer}}\\n"',
            f'                    "What college attributes does this student value? Return JSON scores 0-100."',
            f'                )}},',
            f'            ],',
            f'            temperature=0.2,',
            f'            max_tokens=80,',
            f'        )',
            f'        raw = resp.choices[0].message.content.strip()',
            f'        prefs = _json.loads(raw)',
            f'    except Exception:',
            f'        prefs = {{"research_score": 50, "campus_energy": 50, "support_score": 50, "academic_selectivity": 50}}',
            f'    _passion_pref_cache[key] = prefs',
            f'    return prefs',
            f'',
            f'',
            f'def score_passion(user_answers, college):',
            f'    """AI-informed passion scoring: GPT runs once per answer (cached), then math per college."""',
            f'    if not PASSION_INPUTS:',
            f'        return 50.0',
            f'    total, count = 0.0, 0',
            f'    for p in PASSION_INPUTS:',
            f'        question = p["question"]',
            f'        answer = str(user_answers.get(question, "")).strip()',
            f'        if not answer:',
            f'            total += 50.0; count += 1; continue',
            f'        # GPT returns what attributes this answer signals (cached after first call)',
            f'        prefs = _get_passion_prefs(question, answer)',
            f'        # Score this college against preferences analytically (no extra API calls)',
            f'        scores = []',
            f'        for attr, pref_val in prefs.items():',
            f'            college_val = float(college.get(attr, 50))',
            f'            similarity = 100.0 - abs(float(pref_val) - college_val)',
            f'            scores.append(max(0.0, similarity))',
            f'        total += (sum(scores) / len(scores)) if scores else 50.0',
            f'        count += 1',
            f'    return total / count if count else 50.0',
            f'',
            f'',
            f'def get_category(score: int) -> str:',
            f'    return CATEGORY_3 if score >= 75 else (CATEGORY_2 if score >= 50 else CATEGORY_1)',
            f'',
            f'',
            f'def calculate_score(user_inputs: dict, college: dict) -> int:',
            f'    academic = score_academic(',
            f'        user_gpa=float(user_inputs.get("gpa", 3.5)),',
            f'        user_sat=float(user_inputs.get("sat", 1200)),',
            f'        user_act=float(user_inputs.get("act", 27)),',
            f'        user_class_rank=float(user_inputs.get("class_rank", 50)),',
            f'        user_rigor=float(user_inputs.get("rigor", 4)),',
            f'        college=college,',
            f'    )',
            f'    passion  = score_passion(user_inputs, college)',
            f'    combined = (academic * ACADEMIC_POOL_WEIGHT / 100) + (passion * PASSION_POOL_WEIGHT / 100)',
            f'    return round(min(100.0, max(0.0, combined)))',
            f'',
        ]
    else:
        L += [
            f'# {"─"*56}',
            f'# SECTION 7  SCORING FUNCTIONS',
            f'#   ➡  Unlocks after Week 2 Task 1.',
            f'# {"─"*56}',
            f'',
        ]

    # SECTION 8 — Recommend
    if show_engine:
        L += [
            f'# {"─"*56}',
            f'# SECTION 8  RECOMMEND FUNCTION',
            f'# {"─"*56}',
            f'def recommend(user_inputs: dict, colleges=None) -> list:',
            f'    if colleges is None:',
            f'        colleges = COLLEGE_DATA',
            f'    results = []',
            f'    for college in colleges:',
            f'        score = calculate_score(user_inputs, college)',
            f'        results.append({{',
            f'            "name":             college["name"],',
            f'            "score":            score,',
            f'            "category":         get_category(score),',
            f'            "region":           college.get("region", ""),',
            f'            "setting":          college.get("setting", ""),',
            f'            "tuition":          college.get("tuition", 0),',
            f'            "avg_financial_aid":college.get("avg_financial_aid", 0),',
            f'            "acceptance_rate":  college.get("acceptance_rate", 0),',
            f'            "sat_range":        college.get("sat_range", 0),',
            f'            "enrollment":       college.get("enrollment", 0),',
            f'        }})',
            f'    results.sort(key=lambda x: x["score"], reverse=True)',
            f'    return results[:3]',
            f'',
        ]

    # SECTION 9 — Display
    if has_display and show_engine:
        headline = _escape(week3.get("headline_template", "#{rank} — {college} — {tier} match ({score}%)"))
        show_fields = week3.get("show_fields", ["match_score", "sat_median", "net_cost", "acceptance_rate", "region"])
        viz_prompt = week3.get("viz_prompt", "").strip()
        # Use explicit selection from Task 2 first; fall back to prompt detection
        viz_type   = week3.get("viz_type") or (_detect_viz_type_new(viz_prompt) if viz_prompt else None)

        L += [
            f'# {"─"*56}',
            f'# SECTION 9  RESULTS DISPLAY  (Week 3)',
            f'# {"─"*56}',
            f'HEADLINE_TEMPLATE = "{headline}"',
            f'SHOW_FIELDS = {show_fields!r}',
            f'',
            f'def format_headline(rank, name, score, category):',
            f'    return (HEADLINE_TEMPLATE',
            f'        .replace("{{rank}}", str(rank))',
            f'        .replace("{{college}}", name)',
            f'        .replace("{{score}}", str(score))',
            f'        .replace("{{tier}}", category))',
            f'',
            f'',
            f'def display_results(results):',
            f'    print()',
            f'    print("─" * 58)',
            f'    print("  TOP COLLEGE MATCHES")',
            f'    print("─" * 58)',
            f'    for i, r in enumerate(results, 1):',
            f'        net = r["tuition"] - r["avg_financial_aid"]',
            f'        print()',
            f'        print(f"  {{format_headline(i, r[\'name\'], r[\'score\'], r[\'category\'])}}")',
            f'        if "match_score"     in SHOW_FIELDS: print(f"    Match Score  : {{r[\'score\']}}%")',
            f'        if "sat_median"      in SHOW_FIELDS: print(f"    SAT Median   : {{r[\'sat_range\']}}")',
            f'        if "net_cost"        in SHOW_FIELDS: print(f"    Est Net Cost : ${{net:,.0f}}/yr")',
            f'        if "acceptance_rate" in SHOW_FIELDS: print(f"    Acceptance   : {{r[\'acceptance_rate\']*100:.0f}}%")',
            f'        if "region"          in SHOW_FIELDS: print(f"    Region       : {{r[\'region\']}}")',
            f'        if "setting"         in SHOW_FIELDS: print(f"    Setting      : {{r[\'setting\']}}")',
            f'        if "enrollment"      in SHOW_FIELDS: print(f"    Enrollment   : {{r[\'enrollment\']:,}}")',
            f'        if "financial_aid"   in SHOW_FIELDS: print(f"    Avg Aid      : ${{r[\'avg_financial_aid\']:,}}")',
            f'',
        ]
        viz_code = week3.get("viz_code", "").strip()
        prompt_comment = _escape(viz_prompt[:80]) if viz_prompt else f"{viz_type or 'bar'} visualization"
        L += [
            f'# {"─"*56}',
            f'# SECTION 9b  VISUALIZATION  (Week 3, Task 2)',
            f'#   Type: {viz_type or "bar"}',
            f'#   Prompt: "{prompt_comment}"',
            f'# {"─"*56}',
        ]
        if viz_code:
            # AI-generated code from the student's "Generate Code with AI" click
            L.extend(viz_code.split("\n"))
        else:
            # No AI code yet — show a stub so the app still runs
            L += [
                f'# ➡  TODO: Click "Generate Code with AI" in Week 3 → Task 2.',
                f'# Once you generate it, your custom visualization code appears here.',
                f'def show_visual(results):',
                f'    print()',
                f'    print("  ⚠️  Visualization not generated yet.")',
                f'    print("  Go to Week 3 → Task 2 → write a prompt → Generate Code with AI.")',
                f'    print()',
            ]
        L.append("")
    elif show_engine:
        L += [
            f'# {"─"*56}',
            f'# SECTION 9  RESULTS DISPLAY',
            f'#   ➡  TODO Week 3: Design your result card and visualization.',
            f'# {"─"*56}',
            f'',
            f'def display_results(results):',
            f'    for i, r in enumerate(results, 1):',
            f'        net = r["tuition"] - r["avg_financial_aid"]',
            f'        print(f"  #{{i}} {{r[\'name\']}} — {{r[\'score\']}}% ({{r[\'category\']}}) | Net: ${{net:,.0f}}")',
            f'',
        ]

    # SECTION 10 — Gap Analysis
    if has_gaps and show_engine:
        gap_rules = week4.get("gap_rules_text", "")
        parsed_rules = [l.strip() for l in gap_rules.split("\n") if l.strip().lower().startswith("if ")]
        L += [
            f'# {"─"*56}',
            f'# SECTION 10  GAP ANALYSIS  (Week 4, Task 1)',
            f'# {"─"*56}',
            f'def analyze_gaps(user_inputs: dict, college: dict) -> list:',
            f'    """Return list of gap strings for this college."""',
            f'    gaps = []',
            f'    gpa        = float(user_inputs.get("gpa",        3.5))',
            f'    sat        = float(user_inputs.get("sat",        1200))',
            f'    class_rank = float(user_inputs.get("class_rank", 50))',
            f'    rigor      = float(user_inputs.get("rigor",      4))',
            f'    sat_med    = float(college.get("sat_range",      1200))',
            f'    sel        = float(college.get("academic_selectivity", 50))',
            f'    acc_rate   = float(college.get("acceptance_rate", 0.2))',
            f'    score      = calculate_score(user_inputs, college)',
            f'',
        ]
        for rule in parsed_rules[:8]:
            rl = rule.lower()
            L.append(f'    # Rule: {_escape(rule[:80])}')
            if "sat" in rl and ("200" in rl or "below" in rl):
                L += ['    if sat_med - sat > 200:',
                      '        gaps.append(f"SAT gap: your {sat:.0f} is {sat_med - sat:.0f} pts below {college[\'name\']} median ({sat_med:.0f})")']
            elif "gpa" in rl and "below" in rl:
                L += ['    expected_gpa = 2.5 + (sel / 100) * 1.5',
                      '    if expected_gpa - gpa >= 0.3:',
                      '        gaps.append(f"GPA gap: expected {expected_gpa:.1f} for {college[\'name\']}, you have {gpa:.2f}")']
            elif any(x in rl for x in ["ap", "ib", "rigor"]):
                L += ['    if rigor < 3 and sel > 80:',
                      '        gaps.append(f"Rigor gap: {college[\'name\']} expects strong coursework; you have {rigor:.0f} AP/IB")']
            elif any(x in rl for x in ["accept", "reach"]):
                L += ['    if acc_rate < 0.10 and score < 70:',
                      '        gaps.append(f"Reach gap: {college[\'name\']} accepts {acc_rate*100:.0f}%; your {score}% match is a stretch")']
        L += ['    return gaps', '']
    elif show_engine:
        L += [
            f'# {"─"*56}',
            f'# SECTION 10  GAP ANALYSIS',
            f'#   ➡  TODO Week 4, Task 1: Define your gap rules.',
            f'# {"─"*56}',
            f'def analyze_gaps(user_inputs, college):',
            f'    return []',
            f'',
        ]

    # SECTION 11 — Action Plan
    action_plan_prompt = week4.get("action_plan_prompt", "").strip()
    # Legacy support
    p60_legacy = week4.get("plan_60_day", "").strip()
    p90_legacy = week4.get("plan_90_day", "").strip()

    if has_plan and show_engine:
        if action_plan_prompt:
            # Sanitize prompt — fix common bracket typos like (var), [var}, {var)
            clean_prompt = _sanitize_action_plan_prompt(action_plan_prompt)
            escaped_prompt = _escape(clean_prompt)
            L += [
                f'# {"─"*56}',
                f'# SECTION 11  ACTION PLAN  (Week 4, Task 2)',
                f'# {"─"*56}',
                f'# This is YOUR prompt — it drives every personalized AI plan your app generates.',
                f'# The variables in {{curly_braces}} get filled in with real student + college data,',
                f'# then the filled prompt is sent to GPT to write an actual action plan.',
                f'import openai as _action_openai',
                f'import os as _action_os',
                f'_action_client = _action_openai.OpenAI(api_key=_action_os.environ.get("OPENAI_API_KEY",""))',
                f'ACTION_PLAN_PROMPT = """{escaped_prompt}"""',
                f'',
                f'def generate_action_plan(gaps: list, college: dict, user_inputs: dict) -> str:',
                f'    college_name    = college.get("name", "")',
                f'    match_score     = user_inputs.get("_last_score", 0)',
                f'    region          = college.get("region", "your area")',
                f'    rate            = college.get("acceptance_rate", 0)',
                f'    acceptance_rate = f"{{rate*100:.0f}}%" if rate else "unknown"',
                f'    gaps_text       = ", ".join(gaps) if gaps else "none identified"',
                f'    if not gaps:',
                f'        return "No major gaps — keep up your current trajectory!"',
                f'    try:',
                f'        filled = ACTION_PLAN_PROMPT.format(',
                f'            college_name=college_name,',
                f'            match_score=match_score,',
                f'            region=region,',
                f'            acceptance_rate=acceptance_rate,',
                f'            gaps=gaps_text,',
                f'        )',
                f'        resp = _action_client.chat.completions.create(',
                f'            model="gpt-4o-mini",',
                f'            messages=[{{"role":"user","content":filled}}],',
                f'            max_tokens=350,',
                f'        )',
                f'        return resp.choices[0].message.content.strip()',
                f'    except Exception:',
                f'        return f"📋 Plan for {{college_name}} ({{len(gaps)}} gap(s)): {{gaps_text}}"',
                f'',
            ]
        else:
            # Legacy 60/90-day format
            p60 = _escape(p60_legacy.replace("\n"," ")[:120])
            p90 = _escape(p90_legacy.replace("\n"," ")[:120])
            L += [
                f'# {"─"*56}',
                f'# SECTION 11  ACTION PLAN  (Week 4, Task 2)',
                f'# {"─"*56}',
                f'PLAN_60_DAY = "{p60}"',
                f'PLAN_90_DAY = "{p90}"',
                f'',
                f'def generate_action_plan(gaps: list, college: dict, user_inputs: dict) -> str:',
                f'    college_name = college.get("name", "")',
                f'    if not gaps:',
                f'        return f"No major gaps for {{college_name}} — keep up your trajectory!"',
                f'    lines = [f"📋 Plan for {{college_name}} ({{len(gaps)}} gap(s) found):"]',
                f'    for g in gaps:',
                f'        lines.append(f"   • {{g}}")',
                f'    lines.append("")',
                f'    lines.append(f"📅 Next 60 Days: {{PLAN_60_DAY}}")',
                f'    lines.append(f"📅 60–90 Days  : {{PLAN_90_DAY}}")',
                f'    return "\\n".join(lines)',
                f'',
            ]
    elif show_engine:
        L += [
            f'# {"─"*56}',
            f'# SECTION 11  ACTION PLAN',
            f'#   ➡  TODO Week 4, Task 2: Write your action plan prompt.',
            f'# {"─"*56}',
            f'def generate_action_plan(gaps, college, user_inputs):',
            f'    return "Complete Week 4 to generate action plans."',
            f'',
        ]

    # SECTION 12 — Main
    if show_engine:
        sample_parts = []
        for d in std_defs:
            if week2.get(f"std_{d['key']}_enabled", d["on"]):
                sample_vals = {"gpa":"3.7","sat":"1280","act":"29","class_rank":"15","rigor":"5"}
                sample_parts.append(f'    "{d["key"]}": {sample_vals.get(d["key"], "0")}')
        for q in passion_qs:
            first_kw = next(iter(q["keyword_map"]), "science")
            sample_parts.append(f'    "{_escape(q["question"])}": "I am interested in {_escape(first_kw)}"')
        sample_dict = "{\n" + ",\n".join(sample_parts) + "\n}"

        L += [
            f'# {"─"*56}',
            f'# SECTION 12  SAMPLE USER + TEST RUN',
            f'#   Edit sample_user to test different student profiles.',
            f'# {"─"*56}',
            f'sample_user = {sample_dict}',
            f'',
            f'if __name__ == "__main__":',
            f'    print()',
            f'    print("=" * 58)',
            f'    print(f"  {{APP_TITLE}}")',
            f'    print("=" * 58)',
            f'    print(f"  {{APP_TAGLINE}}")',
            f'    print()',
            f'    print(f"  Built for: {{TARGET_USER}}")',
            f'    print(f"  Scoring {{len(COLLEGE_DATA)}} real colleges...")',
            f'    print()',
            f'    results = recommend(sample_user)',
            f'    display_results(results)',
        ]
        if has_gaps or has_plan:
            L += [
                f'    print()',
                f'    print("─" * 58)',
                f'    print("  GAP ANALYSIS & ACTION PLANS")',
                f'    print("─" * 58)',
                f'    for r in results:',
                f'        college = next((c for c in COLLEGE_DATA if c["name"] == r["name"]), {{}})',
                f'        gaps = analyze_gaps(sample_user, college)',
                f'        plan = generate_action_plan(gaps, college, sample_user)',
                f'        print()',
                f'        print(plan)',
            ]
        if week3.get("viz_code", "").strip() or week3.get("viz_prompt", "").strip() or week3.get("viz_type"):
            L += [f'    show_visual(results)']
        L += [f'    print()', f'    print("─" * 58)', f'']
    else:
        L += [
            f'',
            f'if __name__ == "__main__":',
            f'    print()',
            f'    print("=" * 58)',
            f'    print(f"  {{APP_TITLE}}")',
            f'    print("=" * 58)',
            f'    print()',
            f'    print(f"  Built for: {{TARGET_USER}}")',
            f'    print()',
            f'    print("  ✅ Week 1 skeleton ready!")',
            f'    print("  ➡  Week 2: configure academic inputs + scoring.")',
            f'    print()',
        ]

    return "\n".join(L)
