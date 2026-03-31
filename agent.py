import os
import logging
import google.cloud.logging
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.tool_context import ToolContext

# --- Setup Logging and Environment ---
cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

load_dotenv()
model_name = os.getenv("MODEL", "gemini-2.5-flash")

# ─────────────────────────────────────────────
# TOOLS
# ─────────────────────────────────────────────

def save_original_prompt(tool_context: ToolContext, prompt: str) -> dict[str, str]:
    """Saves the user's raw prompt to agent state so downstream agents can access it."""
    tool_context.state["ORIGINAL_PROMPT"] = prompt
    logging.info(f"[State updated] ORIGINAL_PROMPT: {prompt}")
    return {"status": "success", "saved_prompt": prompt}


# ─────────────────────────────────────────────
# AGENT 1 — Prompt Analyst
# ─────────────────────────────────────────────
prompt_analyst = Agent(
    name="prompt_analyst",
    model=model_name,
    description="Analyses the original prompt and identifies its weaknesses.",
    instruction="""
You are an expert prompt engineering analyst.

Your job is to analyse the following raw prompt submitted by a user and identify exactly
what is weak, ambiguous, missing, or could be improved. Be specific and concise.

Focus on:
- Clarity: Is the intent clear?
- Specificity: Is it too vague? Missing context, constraints, or expected output format?
- Role/Persona: Would adding a role or persona help?
- Output format: Is the desired format (bullet list, JSON, paragraph, code, etc.) specified?
- Tone/style: Should a tone or style be stated?
- Missing constraints: Length, language, audience, etc.

ORIGINAL_PROMPT:
{ ORIGINAL_PROMPT }

Output a structured diagnosis listing the weaknesses. Be brief — one sentence per issue.
""",
    output_key="prompt_diagnosis",
)


# ─────────────────────────────────────────────
# AGENT 2 — Prompt Rewriter
# ─────────────────────────────────────────────
prompt_rewriter = Agent(
    name="prompt_rewriter",
    model=model_name,
    description="Rewrites the original prompt into an improved, more effective version.",
    instruction="""
You are a world-class prompt engineer specialising in crafting highly effective prompts
for large language models like Gemini and GPT-4.

You have been given:
1. The ORIGINAL_PROMPT that a user wrote.
2. A PROMPT_DIAGNOSIS listing specific weaknesses in that prompt.

Your task is to rewrite the original prompt into a significantly improved version that:
- Addresses every weakness identified in the diagnosis.
- Adds a clear role/persona for the AI if relevant.
- Specifies the desired output format explicitly.
- Adds sensible constraints (length, tone, audience) where helpful.
- Is clear, specific, and actionable.
- Preserves the original intent — do NOT change what the user is trying to achieve.

ORIGINAL_PROMPT:
{ ORIGINAL_PROMPT }

PROMPT_DIAGNOSIS:
{ prompt_diagnosis }

Output ONLY the improved prompt text. Do not add commentary, labels, or preamble.
""",
    output_key="improved_prompt",
)


# ─────────────────────────────────────────────
# AGENT 3 — Response Formatter
# ─────────────────────────────────────────────
response_formatter = Agent(
    name="response_formatter",
    model=model_name,
    description="Formats the final output into a clean, user-friendly response.",
    instruction="""
You are a friendly assistant presenting prompt improvement results to a user.

You have:
- ORIGINAL_PROMPT: the raw prompt the user submitted.
- PROMPT_DIAGNOSIS: the list of issues found.
- IMPROVED_PROMPT: the rewritten, improved prompt.

Present the results in this exact format:

---
## 🔍 Original Prompt
[paste the ORIGINAL_PROMPT here]

## ⚠️ Issues Found
[paste the PROMPT_DIAGNOSIS here as a bullet list]

## ✅ Improved Prompt
[paste the IMPROVED_PROMPT here]

## 💡 Why It's Better
Write 2–3 sentences explaining the key improvements made, in plain friendly language.
---

ORIGINAL_PROMPT: { ORIGINAL_PROMPT }
PROMPT_DIAGNOSIS: { prompt_diagnosis }
IMPROVED_PROMPT: { improved_prompt }
""",
)


# ─────────────────────────────────────────────
# SEQUENTIAL WORKFLOW
# ─────────────────────────────────────────────
improvement_workflow = SequentialAgent(
    name="improvement_workflow",
    description="Runs the full prompt improvement pipeline: analyse → rewrite → format.",
    sub_agents=[
        prompt_analyst,    # Step 1: diagnose weaknesses
        prompt_rewriter,   # Step 2: rewrite the prompt
        response_formatter,  # Step 3: present the results
    ],
)


# ─────────────────────────────────────────────
# ROOT AGENT (entry point)
# ─────────────────────────────────────────────
root_agent = Agent(
    name="prompt_improver_greeter",
    model=model_name,
    description="Entry point for the Prompt Improver. Greets the user and collects their prompt.",
    instruction="""
You are the Prompt Improver — an AI assistant that helps users write better prompts
for large language models.

When the conversation starts:
- Greet the user warmly and briefly explain what you do.
- Ask them to share the prompt they want improved.

When the user provides a prompt:
- Use the 'save_original_prompt' tool to save it.
- After the tool confirms success, immediately hand off to the 'improvement_workflow' agent.

Do not attempt to improve the prompt yourself — that is the workflow's job.
""",
    tools=[save_original_prompt],
    sub_agents=[improvement_workflow],
)
