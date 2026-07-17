# Cloud Architecture Design Agent

A [Google ADK](https://google.github.io/adk-docs/) agent that drafts a Google Cloud architecture design, then iteratively critiques and refines it until the design is sound.

## How it works

1. **InitialWriterAgent** drafts a first-pass architecture from the user's requirements (components, deployment topology, security, cost, HA).
2. **RefinementLoop** alternates between:
   - **CriticAgent** — reviews the current draft and either flags issues or says "No major issues found."
   - **RefinerAgent** — applies the critique, or calls `exit_loop` once the critic is satisfied.
3. The loop runs for up to 2 iterations, producing a refined final design.

Built with `SequentialAgent` + `LoopAgent` to demonstrate an iterative generate-critique-refine pattern.

## Tech stack

- `google-adk` (`LlmAgent`, `LoopAgent`, `SequentialAgent`)
- Model: `gemini-2.5-flash`

## Setup

1. Copy `.env.example` to `.env` (not included in this repo) and set your Google Cloud / Vertex AI credentials.
2. Run with the ADK CLI: `adk run cloud_architecture_design`

## Note

This is a learning/demo project built while exploring the Google Agent Development Kit.
