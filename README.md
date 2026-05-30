# HITL Memory Assistant

A robust, multi-agent conversational assistant powered by Google's Agent Development Kit (ADK) and Vertex AI Memory Bank. This agent remembers user preferences across sessions and features a **Human-in-the-Loop (HITL)** architecture to safely manage long-term behavioral rules.

---

## ✨ Key Features

- **Persistent Memory Bank Integration:** Uses Vertex AI Agent Engine to store, retrieve, and automatically inject long-term user preferences (rules) into the chat context at every turn.
- **Human-in-the-Loop (HITL) Guardrails:** Critical memory modification operations (`save_rule_to_memory`, `forget_rule`) require explicit user confirmation before execution, preventing accidental or unwanted behavioral shifts.
- **Hierarchical Multi-Agent Design:**
  - **`hitl_memory_assistant` (Root Agent):** Handles general conversations, automatically queries preloaded facts, and delegates rule management.
  - **`rule_manager_agent` (Sub-Agent):** Dedicated to securely handling the creation, reading, and deletion of user rules.
- **Implicit & Explicit Memory:** Captures explicit user instructions via tools, while automatically snapshotting entire conversations to the memory bank via after-agent callbacks.
- **Telemetry Integration:** Pre-configured with **Langfuse** for observability and tracing.

---

## 🏗️ Architecture

1. **PreloadMemoryTool:** Fires at the beginning of the root agent's turn. Fetches facts from the user-scoped Vertex AI Memory Bank and prepends them to the LLM prompt.
2. **Delegation:** If a user says *"Remember that I like concise answers"*, the root agent delegates the task to the `rule_manager_agent`.
3. **HITL Tools:** The sub-agent reformats the rule and invokes `save_rule_to_memory`. The ADK pauses execution, prompting the user for approval. If approved (`confirmed=true`), the memory is saved.
4. **Session Snapshotting:** The `_persist_session_to_memory` callback captures the full session trace upon completion to enable deeper LLM preference extraction later.

---

## ⚙️ Setup & Configuration

### Prerequisites
- Python 3.10+
- [Google ADK](https://github.com/google/google-adk) installed
- A Google Cloud Project with Vertex AI enabled
- An initialized Vertex AI Agent Engine instance

### 1. Environment Variables
Create a `.env` file in the root directory (make sure this is in your `.gitignore`):


```

```text
Created README.md

```env
# Model Configuration (Gemini 3.1 Flash Lite default)
GOOGLE_API_KEY=your_google_api_key_here

# Vertex AI ADC / Memory Bank Configuration
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id
GOOGLE_CLOUD_LOCATION=us-central1
AGENT_ENGINE_ID=your_agent_engine_id

```

### 2. Install Dependencies

```bash
pip install python-dotenv google-adk
# Install any additional required memory/telemetry modules related to your project

```

---

## 🚀 Usage

To start the interactive web interface with the Vertex AI Memory service attached, run the following command using the ADK CLI:

```bash
adk web agent --memory_service_uri="agentengine://${AGENT_ENGINE_ID}"

```

*(Ensure the `AGENT_ENGINE_ID` environment variable is exported in your terminal session before running this command).*

---

## 🧠 How the Memory Tools Work

* **`save_rule_to_memory`**: Rewrites user input as a first-person preference (e.g., *"I prefer Python code snippets"*). Pauses for HITL confirmation.
* **`list_rules`**: A read-only tool that queries the memory bank and displays all actively enforced rules for the current user. No HITL confirmation needed.
* **`forget_rule`**: Searches for a stored rule using a distinctive substring and removes it from the memory bank. Pauses for HITL confirmation.

