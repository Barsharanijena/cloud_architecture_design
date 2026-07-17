from google.adk.agents import LlmAgent, LoopAgent, SequentialAgent
from google.adk.tools.tool_context import ToolContext

GEMINI_MODEL = "gemini-2.5-flash"

STATE_CURRENT_DOC = "current_document"
STATE_CRITICISM = "criticism"
# NOTE: this exact string must match what the CriticAgent is instructed to output
# when it finds no more issues — verify against the video if the loop never exits.
COMPLETION_PHRASE = "No major issues found."


def exit_loop(tool_context: ToolContext):
    """Call this function ONLY when the critique indicates no further changes are needed,
    signaling the iterative process should end."""
    tool_context.actions.escalate = True
    return {}


# STEP 1: Initial Writer Agent (Runs ONCE at the beginning)
initial_writer_agent = LlmAgent(
    name="InitialWriterAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    # MODIFIED Instruction: Ask for a slightly more developed start
    instruction=f"""You are a cloud architect. Based ONLY on the user's requirements,
draft an initial cloud architecture..
Output must include:
- Key components & services
- Deployment topology (regions, zones, network layout)
- Security considerations
- Cost levers (main drivers)
- HA/Resilience notes

Output ONLY the design text, no explanations.
""",
    description="Generates initial draft of cloud architecture",
    output_key=STATE_CURRENT_DOC
)

# STEP 2a: Critic Agent (Inside the Refinement Loop)
critic_agent_in_loop = LlmAgent(
    name="CriticAgent",
    model=GEMINI_MODEL,
    include_contents='none',
    # MODIFIED Instruction: More nuanced completion criteria, look for clear improvements
    instruction=f"""You are a senior cloud reviewer. Review the given design.

    **Document to Review:**
    ```
    {STATE_CURRENT_DOC}
    ```

    **Task:**
Evaluate the proposed architecture for only using Google Cloud services. Identify any potential
- Best practices
- Security
- Cost efficiency
- High availability

Rules for response:
1. If you find 1-3 clear issues, list them briefly as critique points.
2. If the design is sound, coherent, addresses the topic adequately for its scope, and has no clear issues,
   respond *exactly* with the phrase "{COMPLETION_PHRASE}" and nothing else.
3. Do not suggest purely subjective or stylistic preferences if the architecture is functionally sound.
""",
    description="Reviews the architecture design.",
    output_key=STATE_CRITICISM
)

# STEP 2b: Refiner/Exiter Agent (Inside the Refinement Loop)
refiner_agent_in_loop = LlmAgent(
    name="RefinerAgent",
    model=GEMINI_MODEL,
    # Relies solely on state via placeholders
    include_contents='none',
    instruction=f"""You are a Senior Cloud Architect refining a document based on feedback.
    **Current Document:**
    ```
    {STATE_CURRENT_DOC}
    ```

    **Critique/Suggestions:**
    ```
    {STATE_CRITICISM}
    ```

**Task:**
- If critique == "{COMPLETION_PHRASE}":
  Call the exit_loop tool (do not output any text).

- Else:
  Carefully apply the critique suggestions to improve the 'Current Document'.
  The refined design must include:
  - Key components & services
  - Deployment topology (regions, zones, network layout)
  - Security considerations
  - Cost levers (main drivers)
  - HA/Resilience notes

**Important:**
- Output *only* the refined document text
""",
    description="Refines the design based on critique",
    tools=[exit_loop],  # Provide the exit_loop tool
    output_key=STATE_CURRENT_DOC  # Overwrites state['current_document'] with the refined version
)

# STEP 2: Refinement Loop Agent
refinement_loop = LoopAgent(
    name="RefinementLoop",
    # Agent order is crucial: Critique first, then Refine/Exit
    sub_agents=[
        critic_agent_in_loop,
        refiner_agent_in_loop,
    ],
    max_iterations=2  # Limit loops (lowered from 5 to reduce LLM calls per run while testing quota limits)
)

# STEP 3: Overall Sequential Pipeline
# For ADK tools compatibility, the root agent must be named `root_agent`
root_agent = SequentialAgent(
    name="IterativeWritingPipeline",
    sub_agents=[
        initial_writer_agent,  # Run first to create initial doc
        refinement_loop        # Then run the critique/refine loop
    ],
    description="Iteratively generates and refines a cloud architecture until stable."
)
