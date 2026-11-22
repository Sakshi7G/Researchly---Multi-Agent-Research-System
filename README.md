# 🔎 Researchly – Multi-Agent Research System

**A multi-agent AI research workspace that automates web research, extracts relevant information, generates structured reports, and evaluates report quality using specialized AI components.**

Researchly is a LangChain-powered research application built using Groq LLMs and Tavily Search. It follows a multi-stage workflow in which research information is gathered from the web, relevant content is extracted, a structured research report is generated, and the final report is reviewed by an AI critic.

The application provides an interactive Streamlit interface where users can enter a research topic, monitor the research process, read generated reports, review quality feedback, and export reports as PDF files.

---

## ✨ Key Features

- **AI-Powered Web Research:** Searches the web for recent and relevant information using Tavily.
- **Content Extraction:** Scrapes web pages and extracts readable text for deeper research.
- **Automated Report Generation:** Uses Groq-powered LLMs to generate detailed, structured research reports.
- **AI-Based Report Evaluation:** A Critic component evaluates the generated report across multiple quality criteria.
- **Weighted Quality Scoring:** Calculates an overall score based on individual evaluation criteria.
- **PDF Export:** Download generated research reports as PDF documents.
- **Interactive Dashboard:** Streamlit-based interface for entering topics, viewing reports, and accessing research history.
- **Source References:** Includes source URLs gathered during the research process.

### Workflow Explanation

**1. Search Agent**

- Receives the research topic from the user.
- Uses the Tavily search tool to find relevant web information.
- Retrieves search results containing titles, URLs, and information snippets.

**2. Reader / Content Extraction**

- Identifies a URL from the search results.
- Uses a custom scraping tool built with Requests and BeautifulSoup.
- Extracts readable webpage content for the Writer component.

**3. Writer**

- Receives the search results and extracted webpage content.
- Uses a Groq-powered LLM to generate a structured research report.
- Organizes the report into sections such as Introduction, Key Findings, Recent Developments, Challenges and Limitations, Conclusion, and Sources.

**4. Critic**

- Reviews the generated report.
- Evaluates its quality using five criteria.
- Identifies strengths and areas that need improvement.
- Calculates a weighted overall score based on the individual criterion scores.

---

## 📊 Report Evaluation Criteria

The Critic evaluates each generated report using the following criteria:

| Evaluation Criteria | Weight |
|---|---:|
| Factual Grounding | 30% |
| Completeness | 20% |
| Depth of Analysis | 20% |
| Organization and Clarity | 15% |
| Use of Sources | 15% |

The final score is calculated using a weighted average of the available criterion scores.

---

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| AI / LLM Framework | LangChain |
| Large Language Model | Groq – GPT-OSS 20B |
| Web Search | Tavily Search API |
| Web Scraping | BeautifulSoup, Requests |
| Frontend | Streamlit |
| PDF Generation | ReportLab |
| Environment Management | Python Dotenv |
| Deployment | Streamlit Community Cloud |
| Version Control | Git, GitHub |

---

## 📁 Project Structure

```text
Researchly/
│
├── app.py              # Streamlit application and user interface
├── agents.py           # Search agent, Writer and Critic components
├── pipeline.py         # Research workflow orchestration
├── tools.py            # Web search and webpage scraping tools
├── requirements.txt    # Project dependencies
├── .gitignore          # Excludes secrets and unnecessary files
└── README.md           # Project documentation
```

---

## ⚙️ Installation and Setup

Follow these steps to run Researchly locally.

### 1. Clone the Repository

```bash
git clone https://github.com/Sakshi7G/Researchly---Multi-Agent-Research-System.git
```

### 2. Navigate to the Project Directory

```bash
cd Researchly---Multi-Agent-Research-System
```

### 3. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the environment:

**Windows:**
```bash
.venv\Scripts\activate
```

**Mac / Linux:**
```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the root directory and add your API keys:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

You can obtain API keys from:

- Groq: https://console.groq.com/keys
- Tavily: https://app.tavily.com/

**Important:** Never upload your `.env` file or expose your API keys in a public repository.

### 6. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser.

---

## ☁️ Deployment

Researchly is deployed using **Streamlit Community Cloud**.

The deployment process involves:

1. Pushing the project source code to GitHub.
2. Connecting the GitHub repository to Streamlit Community Cloud.
3. Selecting `app.py` as the main application file.
4. Configuring `GROQ_API_KEY` and `TAVILY_API_KEY` through Streamlit Secrets.
5. Deploying the application.

For more information, visit:

https://docs.streamlit.io/deploy/streamlit-community-cloud

---

## 🚀 Future Enhancements

- Implement parallel research across multiple sources.
- Add support for multiple document formats and uploaded research materials.
- Improve source verification and factual consistency.
- Introduce persistent research history and report storage.
- Add user-configurable research depth and report formats.

---

## 👩‍💻 Author

**Sakshi Vijay Gharge**

B.Tech – Artificial Intelligence  
Usha Mittal Institute of Technology, SNDT Women's University

[GitHub](https://github.com/Sakshi7G)

---

⭐ If you find this project interesting, consider giving the repository a star!
