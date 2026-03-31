# Prompt Improver Agent
### Gen AI Academy APAC — Project Submission | Amaresh Pal

An AI agent built with **Google ADK** and **Gemini 2.5 Flash**, deployed on **Cloud Run**.
It accepts any poorly written prompt and returns a professionally improved version with a diagnosis of what was weak.

---

## 🏗️ Agent Architecture

```
User Input
    │
    ▼
┌─────────────────────────────┐
│  prompt_improver_greeter    │  ← root_agent (entry point)
│  Greets user, saves prompt  │
│  Tool: save_original_prompt │
└─────────────┬───────────────┘
              │ hands off to
              ▼
┌─────────────────────────────────────────────────┐
│           improvement_workflow                  │  ← SequentialAgent
│                                                 │
│  1. prompt_analyst    → prompt_diagnosis        │
│  2. prompt_rewriter   → improved_prompt         │
│  3. response_formatter → final formatted reply  │
└─────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
prompt_improver_agent/
├── .env                  # your environment variables (from setup below)
├── __init__.py           # tells Python this is a package
├── agent.py              # all agent logic
├── requirements.txt      # dependencies
└── README.md             # this file
```

---

## 🚀 Deployment (Cloud Run via ADK CLI)

### 1. Prerequisites
Follow steps 1–8 from the lab guide (Google Account, billing, project, APIs enabled).
### https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/5-deploying-agents/deploy-an-adk-agent-to-cloud-run#2
### 2. Clone / copy this folder
```bash
cd && cp -r /path/to/prompt_improver_agent . && cd prompt_improver_agent
```

### 3. Set up environment variables
```bash
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SA_NAME=prompt-improver-sa

cat <<EOF > .env
PROJECT_ID=$PROJECT_ID
PROJECT_NUMBER=$PROJECT_NUMBER
SA_NAME=$SA_NAME
SERVICE_ACCOUNT=${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
MODEL="gemini-2.5-flash"
EOF
```

### 4. Create virtual environment and install dependencies
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 5. Test locally (optional)
```bash
adk web
```
Open http://localhost:8000 to interact with the agent locally.

### 6. Set up IAM
```bash
source .env

gcloud iam service-accounts create ${SA_NAME} \
    --display-name="Service Account for Prompt Improver"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/aiplatform.user"
```

### 7. Deploy to Cloud Run
```bash
uvx --from google-adk==1.14.0 \
  adk deploy cloud_run \
  --project=$PROJECT_ID \
  --region=us-central1 \
  --service_name=prompt-improver \
  --with_ui \
  . \
  -- \
  --service-account=$SERVICE_ACCOUNT
```
When prompted, type `Y` (create Artifact Registry repo) and `y` (allow unauthenticated access).

---

## 🧪 Testing the Deployed Agent

1. Open the Cloud Run URL in your browser (e.g. https://prompt-improver-1021684856488.europe-west1.run.app)
2. Toggle **Token Streaming** ON (top right)
3. Type `hello` → the agent introduces itself
4. Paste a weak prompt, e.g.:

   > `write something about AI`

5. The agent will return:
   - 🔍 **Original Prompt** — your input
   - ⚠️ **Issues Found** — specific weaknesses diagnosed
   - ✅ **Improved Prompt** — the rewritten version
   - 💡 **Why It's Better** — plain-language explanation

---

## 💡 Example

**Input:**
> `write something about AI`

**Improved Output:**
> You are an expert technology writer. Write a 300-word informative blog introduction about
> the current state of artificial intelligence in 2025, targeting a non-technical audience.
> Use a conversational tone, avoid jargon, and end with a thought-provoking question.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | Google ADK 1.14.0 |
| LLM | Gemini 2.5 Flash |
| Hosting | Google Cloud Run |
| Container Registry | Artifact Registry |
| Logging | Google Cloud Logging |
| Runtime | Python 3.11+ |
