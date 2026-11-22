import re

from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from tools import web_search, scrape_url
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# MODEL SETUP
# ============================================================

MODEL_NAME = "openai/gpt-oss-20b"

# Search / reader agents: deterministic tool use.
llm = ChatGroq(
    model=MODEL_NAME,
    temperature=0,
    max_tokens=2000,
)

# Writer: more room so the report is not cut off before the
# Conclusion and Sources sections.
writer_llm = ChatGroq(
    model=MODEL_NAME,
    temperature=0.2,
    max_tokens=3500,
)

# Critic: a little randomness so scores are not locked to one value.
critic_llm = ChatGroq(
    model=MODEL_NAME,
    temperature=0.4,
    max_tokens=2000,
)


# ============================================================
# 1st AGENT - SEARCH AGENT
# ============================================================

def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search]
    )


# ============================================================
# 2nd AGENT - READER AGENT
# ============================================================

def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url]
    )


# ============================================================
# WRITER CHAIN
# ============================================================

writer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are an expert research writer.

Write a clear, factual and well-structured research report.

IMPORTANT FORMATTING RULES:
- Do NOT use Markdown tables.
- Write the report mainly in normal paragraphs.
- Use headings and subheadings where appropriate.
- Use bullet points only when they genuinely improve readability.
- Explain each important finding in complete paragraphs.
- Do not invent facts that are not supported by the research.
- Keep the writing natural, professional and easy to read.
- Do not repeat the same information unnecessarily.
"""
    ),
    (
        "human",
        """
Write a detailed research report on the topic below.

Topic:
{topic}

Research Gathered:
{research}

Structure the report as:

# Research Report

## 1. Introduction
Explain the topic and provide relevant background.

## 2. Key Findings
Discuss at least 3 important findings.

For each finding:
- Use a clear subheading.
- Explain the finding in one or more detailed paragraphs.
- Explain why the finding is important.

## 3. Recent Developments
Explain important recent developments, discoveries, technologies,
companies, studies, or trends mentioned in the research.

## 4. Challenges and Limitations
Explain the major challenges, limitations, risks, or uncertainties
mentioned in the research.

## 5. Conclusion
Summarize the main insights in a few clear paragraphs.

## 6. Sources
List the URLs found in the research.

IMPORTANT:
- Do NOT use Markdown tables anywhere in the report.
- Use paragraphs instead of tables.
- Use complete sentences.
- Do not create unsupported facts.
- Base the report on the research provided.
- Keep the report informative and professional.
"""
    ),
])


writer_chain = writer_prompt | writer_llm | StrOutputParser()


# ============================================================
# CRITIC CHAIN
# ============================================================
#
# How scoring works:
#   1. The critic rates five criteria separately (1-10 each).
#   2. Python computes the final score as a weighted average,
#      so the headline number comes from the breakdown and the
#      model is not asked to pick one "overall" number itself.
#   3. The final text starts with "Score: X.X/10", so the
#      Streamlit app's score extraction keeps working.

# criterion label -> weight
CRITERIA = {
    "Factual grounding": 0.30,
    "Completeness": 0.20,
    "Depth of analysis": 0.20,
    "Organization and clarity": 0.15,
    "Use of sources": 0.15,
}

RESEARCH_CHAR_LIMIT = 6000   # keeps the critic prompt small enough for Groq limits


critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You are a demanding, evidence-driven research report critic.
Your job is to tell the difference between strong and weak reports,
so you must use the whole 1-10 scale.

SCORING SCALE (apply it to every criterion):
- 9-10: Exceptional. Almost no flaws. This should be rare.
- 7-8 : Good, with only minor gaps.
- 5-6 : Adequate, but with clear gaps or weak spots.
- 3-4 : Weak. Major problems.
- 1-2 : Poor or unusable.

CRITERIA:
1. Factual grounding: Are the claims supported by the research provided?
   Look for unsupported numbers, names, dates or claims that do not
   appear in the research notes.
2. Completeness: Are all required sections present and fully developed
   (Introduction, Key Findings with at least 3 findings, Recent
   Developments, Challenges and Limitations, Conclusion, Sources)?
   Is any section thin, missing, or cut off mid-sentence?
3. Depth of analysis: Does the report explain WHY findings matter, or
   does it only list generic statements?
4. Organization and clarity: Logical flow, clear headings, readable
   paragraphs, no repetition.
5. Use of sources: Does the report draw on several different sources,
   and does the Sources section list real URLs from the research?

RULES:
- Judge each criterion on its own. Different criteria should often
  get different scores.
- Deduct points for specific problems you can point to.
- Do not round up to be polite, and do not default to a "safe" middle score.
- Do not use tables.
- Be specific: refer to actual sections or sentences of the report.

OUTPUT FORMAT (follow exactly, replacing N with your own number
for each criterion; do NOT output an overall score):

Score breakdown:
- Factual grounding: N/10
- Completeness: N/10
- Depth of analysis: N/10
- Organization and clarity: N/10
- Use of sources: N/10

Strengths:
- <specific strength from this report>
- <specific strength from this report>
- <specific strength from this report>

Areas to Improve:
- <specific, actionable weakness from this report>
- <specific, actionable weakness from this report>
- <specific, actionable weakness from this report>

Verdict:
<one sentence>
"""
    ),
    (
        "human",
        """
RESEARCH NOTES (what the writer was given; use these to check facts):
{research}

REPORT TO REVIEW:
{report}

Review the report using the scale and output format from your instructions.
"""
    ),
])


def _prepare_critic_input(inputs: dict) -> dict:
    """Accepts {"report": ...} and optionally {"research": ...}."""
    research = (inputs.get("research") or "").strip()

    if research:
        research = research[:RESEARCH_CHAR_LIMIT]
    else:
        research = (
            "Not provided. Judge factual grounding from internal "
            "consistency, specificity, and whether claims are tied to sources."
        )

    return {"report": inputs["report"], "research": research}


def _finalize_critic_output(text: str) -> str:
    """Compute the overall score from the per-criterion scores."""
    scores = {}

    for line in (text or "").splitlines():
        cleaned = line.strip().lstrip("-*•").replace("*", "").strip()

        for label in CRITERIA:
            m = re.match(
                rf"{re.escape(label)}\s*:\s*(\d+(?:\.\d+)?)\s*/\s*10",
                cleaned,
                re.IGNORECASE,
            )
            if m and label not in scores:
                scores[label] = max(1.0, min(10.0, float(m.group(1))))

    # Need most of the criteria to trust the average.
    if len(scores) >= 3:
        total_weight = sum(CRITERIA[k] for k in scores)
        overall = sum(scores[k] * CRITERIA[k] for k in scores) / total_weight
        return f"Score: {overall:.1f}/10\n\n{text.strip()}"

    # Fallback: keep whatever the model wrote.
    return text.strip()


critic_chain = (
    RunnableLambda(_prepare_critic_input)
    | critic_prompt
    | critic_llm
    | StrOutputParser()
    | RunnableLambda(_finalize_critic_output)
)