PROJECT_TEMPLATES = {
    "College Recommender": {
        "title": "My College Match Finder",
        "description": "Help students find the right college based on their academic profile, goals, and budget.",
        "target_user": "High school juniors and seniors overwhelmed by college choices",
        "problem": "Students apply to colleges based on rankings alone, missing schools that actually fit their goals and lifestyle.",
        "recommended_inputs": [
            "GPA (weighted)",
            "SAT/ACT Score",
            "Preferred Location (region)",
            "Campus Size Preference",
            "Intended Major",
            "Budget / Financial Aid Need",
            "Campus Culture (Greek life, sports, arts)"
        ],
        "example_output": "Top 3 college matches with fit score, key strengths, financial aid estimate, and why each is a strong match for you.",
        "scoring_dimensions": {
            "Academic Fit": 35,
            "Financial Fit": 30,
            "Culture Match": 20,
            "Location Match": 15
        },
        "recommendation_categories": ["Safety", "Match", "Reach"],
        "tone_options": ["Friendly & Direct", "Professional", "Motivating"],
        "default_tone": "Friendly & Direct",
        "intro_text": "Tell us about yourself and we'll find your best-fit colleges.",
        "data_source": "college_data"
    },
    "Extracurricular Finder": {
        "title": "My Activity Match",
        "description": "Match students with extracurricular activities that fit their personality, goals, and schedule.",
        "target_user": "9th and 10th graders looking for meaningful activities",
        "problem": "Students pick random clubs without knowing what fits their personality and long-term goals.",
        "recommended_inputs": [
            "Personality Type (introvert/extrovert/ambivert)",
            "Interests (arts, STEM, sports, service, etc.)",
            "Time Available Per Week",
            "College-related Goals",
            "Team vs Solo Preference",
            "Leadership Interest"
        ],
        "example_output": "Top 3 activity recommendations with match score, why it fits you, and tips for joining or starting.",
        "scoring_dimensions": {
            "Personality Match": 35,
            "Goal Alignment": 30,
            "Time Fit": 20,
            "Leadership Potential": 15
        },
        "recommendation_categories": ["Worth Exploring", "Good Fit", "Best Fit"],
        "tone_options": ["Energetic & Fun", "Friendly & Direct", "Professional"],
        "default_tone": "Energetic & Fun",
        "intro_text": "Let's find activities you'll actually love—not just fill your resume."
    },
    "Study Strategy Coach": {
        "title": "My Study Strategy Coach",
        "description": "Give students personalized study strategies based on their learning style and subjects.",
        "target_user": "Students who study hard but don't get the grades they want",
        "problem": "Generic study advice fails students because every learner is different.",
        "recommended_inputs": [
            "Learning Style (visual/auditory/kinesthetic/reading)",
            "Current GPA",
            "Hardest Subjects",
            "Study Hours Per Day",
            "Test Anxiety Level",
            "Preferred Study Environment"
        ],
        "example_output": "3 personalized study strategies with step-by-step instructions, a sample weekly schedule, and subject-specific tips.",
        "scoring_dimensions": {
            "Learning Style Alignment": 40,
            "Subject-Technique Fit": 35,
            "Time Availability": 25
        },
        "recommendation_categories": ["Supplementary Method", "Secondary Strategy", "Primary Strategy"],
        "tone_options": ["Serious & Motivating", "Friendly & Direct", "Professional"],
        "default_tone": "Serious & Motivating",
        "intro_text": "Answer a few questions and get your personalized study playbook."
    },
    "Habit Builder": {
        "title": "My Habit Builder",
        "description": "Recommend sustainable habits based on student goals and current lifestyle.",
        "target_user": "Students who want to improve but struggle to stick to routines",
        "problem": "Most habit advice is generic—it doesn't account for a student's specific schedule, goals, and energy patterns.",
        "recommended_inputs": [
            "Main Life Goal",
            "Current Energy Level (morning/evening person)",
            "Time Available Per Day",
            "Biggest Challenge",
            "Support System",
            "Motivation Style (rewards/progress/accountability)"
        ],
        "example_output": "3 recommended habits with implementation guide, why they fit your lifestyle, and a 30-day challenge plan.",
        "scoring_dimensions": {
            "Goal Alignment": 40,
            "Lifestyle Fit": 35,
            "Sustainability": 25
        },
        "recommendation_categories": ["Optional Habit", "Supporting Habit", "Core Habit"],
        "tone_options": ["Motivating", "Calm & Supportive", "Friendly & Direct"],
        "default_tone": "Motivating",
        "intro_text": "Build habits that actually stick—tailored to your life."
    },
    "Summer Program Matcher": {
        "title": "My Summer Program Finder",
        "description": "Match students with summer programs that fit their interests, budget, and goals.",
        "target_user": "High school students looking for meaningful summer experiences",
        "problem": "Finding the right summer program is overwhelming—there are thousands of options and no clear guide.",
        "recommended_inputs": [
            "Area of Interest (STEM, arts, business, service, etc.)",
            "Budget Range",
            "Preferred Location (local/national/international)",
            "Duration Preference",
            "Program Type (research/internship/camp/travel)",
            "College Application Goal"
        ],
        "example_output": "Top 3 summer program matches with fit score, key benefits, application tips, and cost breakdown.",
        "scoring_dimensions": {
            "Interest Match": 35,
            "Budget Fit": 25,
            "Location Preference": 20,
            "College Impact": 20
        },
        "recommendation_categories": ["Backup Choice", "Strong Option", "Best Fit"],
        "tone_options": ["Energetic & Fun", "Professional", "Friendly & Direct"],
        "default_tone": "Energetic & Fun",
        "intro_text": "Find your perfect summer—experiences that change everything."
    },
    "Passion Project Idea Generator": {
        "title": "My Project Idea Generator",
        "description": "Suggest meaningful passion project ideas based on a student's skills, interests, and goals.",
        "target_user": "High school students who want to build something real but don't know where to start",
        "problem": "Students have ideas but don't know how to turn interests into actionable, college-worthy projects.",
        "recommended_inputs": [
            "Strongest Skills",
            "Top 3 Interests",
            "Available Time Per Week",
            "Resources/Tools Access",
            "College/Career Goal",
            "Preferred Output (app/research/nonprofit/art/etc.)"
        ],
        "example_output": "3 project ideas with concept description, why it fits you, difficulty level, timeline, and first steps.",
        "scoring_dimensions": {
            "Skill Alignment": 35,
            "Interest Match": 30,
            "Feasibility": 20,
            "Impact Potential": 15
        },
        "recommendation_categories": ["Starter Project", "Main Project", "Ambitious Reach"],
        "tone_options": ["Energetic & Fun", "Motivating", "Professional"],
        "default_tone": "Energetic & Fun",
        "intro_text": "Turn your interests into a project that gets noticed."
    }
}

TONE_DESCRIPTIONS = {
    "Friendly & Direct": "Clear, warm, and to the point. Like advice from a smart older sibling.",
    "Professional": "Polished and formal. Like a guidance counselor report.",
    "Energetic & Fun": "Upbeat, enthusiastic, with personality. Like a great coach.",
    "Serious & Motivating": "Focused and inspiring. Takes your goals seriously.",
    "Motivating": "Encouraging and ambitious. Pushes you forward.",
    "Calm & Supportive": "Gentle and reassuring. No pressure, just progress.",
}

CORE_FEATURES_OPTIONS = {
    "College Recommender": [
        "Academic Fit Score", "Financial Aid Estimator", "Campus Culture Match",
        "Location Filter", "Major Alignment", "Admission Chance Estimate",
        "Student Life Preview", "Career Path Alignment"
    ],
    "Extracurricular Finder": [
        "Personality Match", "Goal Alignment", "Time Commitment Filter",
        "Leadership Track", "College Impact Score", "Interest Category Filter",
        "Team vs Solo Preference", "How-to-Join Guide"
    ],
    "Study Strategy Coach": [
        "Learning Style Detection", "Subject-Specific Tips", "Weekly Study Plan",
        "Test Prep Mode", "Focus Timer Suggestions", "Stress Level Check",
        "Grade Improvement Tracker", "Accountability Mode"
    ],
    "Habit Builder": [
        "Goal-Based Habit Match", "Energy Pattern Alignment", "Habit Difficulty Level",
        "30-Day Challenge Plan", "Accountability Tracker", "Progress Visualization",
        "Lifestyle Fit Score", "Science-Backed Techniques"
    ],
    "Summer Program Matcher": [
        "Interest Category Match", "Budget Filter", "Location Preference",
        "Application Difficulty Level", "College Admissions Impact", "Program Duration Options",
        "Scholarship Finder", "Application Deadline Tracker"
    ],
    "Passion Project Idea Generator": [
        "Skill-Based Matching", "Feasibility Score", "Impact Potential Rating",
        "Step-by-Step Roadmap", "Resource Requirements", "Timeline Estimator",
        "Portfolio Value Rating", "Similar Successful Projects"
    ]
}
