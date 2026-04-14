# DataNativ Studio

  A multi-page Streamlit app for a 4-week high school AI bootcamp where students design and build a real **College Recommender App** using actual 42-college data.

  ## What Students Build

  Students progress through 4 guided weeks to create a complete, AI-powered college recommendation engine:

  | Week | Focus | What gets built |
  |------|-------|-----------------|
  | **Week 1** | Problem & User Definition | App name, tagline, target user, recommendation categories |
  | **Week 2** | Scoring Engine | Standardized inputs (GPA, SAT, class rank, rigor) + custom passion questions with AI semantic scoring |
  | **Week 3** | Presentation Layer | AI-generated Plotly visualizations, result card design, custom headline templates |
  | **Week 4** | Gap Analysis & Action Plans | Gap rules, AI prompt-driven action plans with real web-searched local opportunities |

  ## Key Features

  - **Real data**: 42 real colleges with CDS (Common Data Set) data
  - **AI scoring**: Passion questions scored with GPT-4o-mini semantic matching
  - **AI visualization**: GPT writes real Plotly chart code from a student's natural language prompt
  - **AI action plans**: GPT generates personalized, location-aware improvement plans using live web search for local resources
  - **Live preview**: Students can test their app with any simulated student profile

  ## Setup

  ```bash
  pip install streamlit openai openpyxl plotly
  streamlit run app.py --server.port 5000
  ```

  Set your `OPENAI_API_KEY` environment variable before running.

  ## Tech Stack

  - Python + Streamlit
  - OpenAI GPT-4o-mini
  - Plotly for interactive charts
  - SQLite via custom storage layer
  