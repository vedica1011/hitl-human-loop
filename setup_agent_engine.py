"""One-time: create a Vertex AI Agent Engine instance for Memory Bank.

Run once:  python setup_agent_engine.py
It will print and append AGENT_ENGINE_ID to your .env file.
"""
from __future__ import annotations

import os
from pathlib import Path

import vertexai
from dotenv import load_dotenv

load_dotenv()

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]


def main() -> None:
    client = vertexai.Client(project=PROJECT, location=LOCATION)

    agent_engine = client.agent_engines.create(
        config={"display_name": "hitl-memory-assistant"}
    )
    engine_name = agent_engine.api_resource.name
    engine_id = engine_name.split("/")[-1]
    print(f"Created Agent Engine: {engine_name}")
    print(f"AGENT_ENGINE_ID = {engine_id}")

    # Persist to .env
    env_path = Path(".env")
    text = env_path.read_text()
    if "AGENT_ENGINE_ID=" in text:
        new = []
        for line in text.splitlines():
            new.append(
                f"AGENT_ENGINE_ID={engine_id}"
                if line.startswith("AGENT_ENGINE_ID=")
                else line
            )
        env_path.write_text("\n".join(new) + "\n")
    else:
        with env_path.open("a") as f:
            f.write(f"\nAGENT_ENGINE_ID={engine_id}\n")
    print("Wrote AGENT_ENGINE_ID to .env")


if __name__ == "__main__":
    main()