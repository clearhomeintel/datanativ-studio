from college_data import get_colleges

def recommend_colleges(inputs: dict) -> list:
    colleges = get_colleges()
    scored = []

    gpa = float(inputs.get("gpa", 3.5))
    sat = int(inputs.get("sat", 1200))
    budget = int(inputs.get("budget", 40000))
    pref_size = inputs.get("campus_size", "Medium")
    pref_location = inputs.get("location_pref", "Any")
    pref_setting = inputs.get("setting", "Any")
    aid_needed = inputs.get("aid_needed", "Yes") == "Yes"

    size_map = {"Small (< 5k)": (0, 5000), "Medium (5k-15k)": (5000, 15000), "Large (> 15k)": (15000, 999999), "Any": (0, 999999)}
    size_range = size_map.get(pref_size, (0, 999999))

    for college in colleges:
        score = 0.0
        reasons = []

        # --- Academic Fit (35%) ---
        college_sat = college.get("sat_range", 1100)
        sat_diff = abs(sat - college_sat)
        if sat_diff <= 60:
            academic_score = 100
        elif sat_diff <= 150:
            academic_score = 80
        elif sat_diff <= 250:
            academic_score = 60
        elif sat > college_sat:
            academic_score = 90
        else:
            academic_score = 30

        gpa_required = max(0.0, 4.0 - (college.get("acceptance_rate", 0.5) * 4))
        if gpa >= gpa_required:
            academic_score = min(100, academic_score + 10)
            reasons.append(f"Your GPA is competitive for this school")

        score += academic_score * 0.35

        # --- Financial Fit (30%) ---
        tuition = college.get("tuition", 35000)
        avg_aid = college.get("avg_financial_aid", 10000)
        net_cost = tuition - (avg_aid if aid_needed else 0)

        if net_cost <= budget:
            fin_score = 100
            reasons.append(f"Net cost (~${net_cost:,}/yr) fits your budget")
        elif net_cost <= budget * 1.2:
            fin_score = 70
            reasons.append(f"Net cost is slightly above budget but manageable")
        elif net_cost <= budget * 1.5:
            fin_score = 40
        else:
            fin_score = 10

        score += fin_score * 0.30

        # --- Campus Size Match (15%) ---
        enrollment = college.get("enrollment", 5000)
        if size_range[0] <= enrollment <= size_range[1]:
            size_score = 100
            reasons.append(f"Campus size matches your preference")
        else:
            size_score = 40
        score += size_score * 0.15

        # --- Location / Region Match (20%) ---
        if pref_location == "Any":
            loc_score = 80
        else:
            region = college.get("region", "").lower()
            location = college.get("location", "").lower()
            pref = pref_location.lower()
            if pref in region or pref in location:
                loc_score = 100
                reasons.append(f"Located in your preferred region")
            elif pref == "northeast" and region in ["northeast", "new england"]:
                loc_score = 100
            elif pref == "west" and region in ["west", "pacific"]:
                loc_score = 100
            else:
                loc_score = 50
        score += loc_score * 0.20

        acceptance_rate = college.get("acceptance_rate", 0.5)
        if acceptance_rate < 0.10:
            category = "Reach"
        elif acceptance_rate < 0.40:
            category = "Match"
        else:
            category = "Safety"

        scored.append({
            "college": college,
            "score": round(score, 1),
            "category": category,
            "reasons": reasons[:3],
            "net_cost": max(0, int(tuition - (avg_aid if aid_needed else 0))),
            "academic_score": round(academic_score, 0),
            "financial_score": round(fin_score, 0),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:10]
    top_by_cat = {"Safety": None, "Match": None, "Reach": None}
    for s in top:
        cat = s["category"]
        if top_by_cat[cat] is None:
            top_by_cat[cat] = s

    results = []
    for cat in ["Safety", "Match", "Reach"]:
        if top_by_cat[cat]:
            results.append(top_by_cat[cat])

    while len(results) < 3 and scored:
        candidate = scored.pop(0)
        if candidate not in results:
            results.append(candidate)

    return results[:3]


def recommend_extracurriculars(inputs: dict) -> list:
    personality = inputs.get("personality", "Ambivert")
    interests = inputs.get("interests", [])
    time_hrs = int(inputs.get("time_per_week", 5))
    leadership = inputs.get("leadership", "Yes") == "Yes"
    goal = inputs.get("goal", "College Application")

    activities = [
        {"name": "Student Government", "type": "Leadership", "interests": ["politics","leadership","community"], "time": 5, "leadership": True},
        {"name": "Robotics Club", "type": "STEM", "interests": ["engineering","tech","stem","robotics"], "time": 8, "leadership": False},
        {"name": "Debate Team", "type": "Communication", "interests": ["debate","law","politics","public speaking"], "time": 6, "leadership": True},
        {"name": "Varsity Sports", "type": "Athletics", "interests": ["sports","fitness","teamwork"], "time": 12, "leadership": False},
        {"name": "School Newspaper", "type": "Writing/Media", "interests": ["writing","journalism","media","communication"], "time": 4, "leadership": False},
        {"name": "Drama / Theater", "type": "Performing Arts", "interests": ["theater","acting","arts","performance"], "time": 8, "leadership": False},
        {"name": "Math Olympiad", "type": "Academic", "interests": ["math","stem","competition"], "time": 4, "leadership": False},
        {"name": "Community Service Club", "type": "Service", "interests": ["service","community","volunteering","social justice"], "time": 4, "leadership": True},
        {"name": "Model UN", "type": "Diplomacy", "interests": ["politics","international","debate","public policy"], "time": 5, "leadership": True},
        {"name": "Art Club", "type": "Visual Arts", "interests": ["art","design","creativity","visual"], "time": 3, "leadership": False},
        {"name": "Science Olympiad", "type": "STEM Competition", "interests": ["science","stem","competition","biology","chemistry"], "time": 6, "leadership": False},
        {"name": "Entrepreneurship Club", "type": "Business", "interests": ["business","entrepreneurship","startups","finance"], "time": 5, "leadership": True},
        {"name": "Coding Club / Hackathons", "type": "Technology", "interests": ["coding","programming","tech","cs","ai"], "time": 5, "leadership": False},
        {"name": "Environmental Club", "type": "Advocacy", "interests": ["environment","sustainability","science","activism"], "time": 3, "leadership": True},
        {"name": "Music Ensemble", "type": "Performing Arts", "interests": ["music","band","orchestra","arts"], "time": 6, "leadership": False},
    ]

    scored = []
    for act in activities:
        score = 0.0
        reasons = []

        interest_overlap = sum(1 for i in interests if any(i.lower() in ai for ai in act["interests"]))
        if interest_overlap > 0:
            score += min(40, interest_overlap * 15)
            reasons.append(f"Aligns with your {interests[0] if interests else 'interests'} interest")

        if act["time"] <= time_hrs:
            score += 25
            reasons.append(f"Fits your {time_hrs} hr/week schedule")
        elif act["time"] <= time_hrs + 3:
            score += 10

        if leadership and act["leadership"]:
            score += 20
            reasons.append("Offers strong leadership opportunities")

        if "college" in goal.lower() and act["type"] in ["Leadership","Academic","Service","Technology"]:
            score += 15

        scored.append({
            "activity": act,
            "score": round(score, 1),
            "reasons": reasons[:2],
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:3]


def recommend_study_strategies(inputs: dict) -> list:
    learning_style = inputs.get("learning_style", "Visual")
    subjects = inputs.get("hardest_subjects", [])
    hours = int(inputs.get("study_hours", 2))
    anxiety = inputs.get("test_anxiety", "Medium")

    strategies_db = {
        "Visual": [
            {"name": "Mind Mapping", "description": "Draw visual diagrams connecting key ideas. Use color coding.", "time_needed": 1, "subjects": ["all"]},
            {"name": "Flashcard Systems", "description": "Create visual flashcards with images and diagrams using Anki.", "time_needed": 1, "subjects": ["vocab","science","history"]},
            {"name": "Video Summarizing", "description": "Watch Khan Academy or YouTube, then pause and draw what you learned.", "time_needed": 2, "subjects": ["math","science"]},
        ],
        "Auditory": [
            {"name": "Teach-Back Method", "description": "Explain concepts out loud as if teaching someone. Record yourself.", "time_needed": 1, "subjects": ["all"]},
            {"name": "Study Groups", "description": "Discuss material with peers—hearing others' explanations cements concepts.", "time_needed": 2, "subjects": ["all"]},
            {"name": "Podcast Review", "description": "Listen to subject-related podcasts or record your own voice notes.", "time_needed": 1, "subjects": ["history","english","science"]},
        ],
        "Kinesthetic": [
            {"name": "Practice Problems First", "description": "Jump into problems immediately, then look up what you need to know.", "time_needed": 2, "subjects": ["math","science","coding"]},
            {"name": "Pomodoro Method", "description": "25-min focused study blocks with 5-min movement breaks. Stay active.", "time_needed": 1, "subjects": ["all"]},
            {"name": "Real-World Application", "description": "Find real-world examples of what you're studying and build or try them.", "time_needed": 2, "subjects": ["science","economics","history"]},
        ],
        "Reading/Writing": [
            {"name": "Cornell Note Method", "description": "Structured notes with summaries and review questions in margins.", "time_needed": 1, "subjects": ["all"]},
            {"name": "Rewriting Summaries", "description": "After each section, close the book and write a summary in your own words.", "time_needed": 1, "subjects": ["all"]},
            {"name": "Essay Outlining Practice", "description": "Write detailed outlines before full essays. Outline, refine, then write.", "time_needed": 2, "subjects": ["english","history","social studies"]},
        ]
    }

    selected = strategies_db.get(learning_style, strategies_db["Visual"])
    results = []
    for s in selected:
        if s["time_needed"] <= hours:
            score = 80
        else:
            score = 50
        results.append({
            "strategy": s,
            "score": score,
            "learning_style": learning_style,
            "reasons": [f"Perfect for {learning_style} learners", f"Works in {s['time_needed']}hr sessions"],
        })
    return results[:3]


def get_recommendation(project_type: str, inputs: dict) -> list:
    if project_type == "College Recommender":
        return recommend_colleges(inputs)
    elif project_type == "Extracurricular Finder":
        return recommend_extracurriculars(inputs)
    elif project_type == "Study Strategy Coach":
        return recommend_study_strategies(inputs)
    else:
        return [
            {"name": "Option A", "score": 85, "reasons": ["Strong match for your goals"], "category": "Best Fit"},
            {"name": "Option B", "score": 72, "reasons": ["Worth exploring"], "category": "Good Option"},
            {"name": "Option C", "score": 61, "reasons": ["Stretch opportunity"], "category": "Reach"},
        ]
