"""
CrewAI Orchestration for Decision Miner

This module wires up the Friction Listener and Decision Mapper agents
into a sequential workflow for discovering decision debt.
"""

from crewai import Crew, Task, Process
from typing import Optional

from .agents.friction_listener import create_friction_listener
from .agents.decision_mapper import create_decision_mapper
from .tools.tavily_search import tavily_search_tool, search_subreddit
from .models.decision_pattern import DecisionBottleneckReport


def create_scan_task(target: str, friction_listener) -> Task:
    """Create task for Friction Listener to scan for high-signal threads."""
    return Task(
        description=f"""Search and scan online discussions in {target} to find threads
that reveal decision debt and process frustration.

Your goal is to find 3-5 high-signal threads where people are venting about:
- Policy vs reality gaps
- Unofficial workarounds they've developed
- Judgment calls they have to make
- Missing guidelines or training
- Shadow systems (personal spreadsheets, side chats)

For each thread found, extract:
1. The source URL
2. Key quotes that reveal friction
3. Signal type (policy_gap, workaround, judgment_call, etc.)
4. Intensity score (0-1)

Focus on specificity - vague complaints are less valuable than detailed descriptions
of actual decision scenarios.""",
        expected_output="""A list of 3-5 high-signal friction signals, each containing:
- Source URL
- Key quotes (the actual text revealing the friction)
- Signal type classification
- Intensity score with justification""",
        agent=friction_listener,
    )


def create_analyze_task(decision_mapper, context_task: Task) -> Task:
    """Create task for Decision Mapper to analyze friction signals."""
    return Task(
        description="""Analyze each friction signal from the previous task and extract
structured decision patterns.

For each friction signal, determine:
1. **Ambiguous Trigger**: What specific situation created decision ambiguity?
2. **Manual Judgment**: What human judgment is required that a rule couldn't handle?
3. **Shadow Tool**: What workaround or informal system do they use? (if mentioned)
4. **Downstream Risk**: What are the consequences of making the wrong decision?

Assign a confidence score (0-1) based on:
- 0.8-1.0: All four elements explicitly described
- 0.5-0.7: Clear trigger and judgment, some inference needed
- 0.3-0.4: Strong signal but requires interpretation
- <0.3: Too vague, skip this signal

Synthesize your findings into 2-3 key insights about the decision debt in this domain.""",
        expected_output="""A structured analysis containing:
1. List of DecisionPattern objects with all fields
2. Summary of key findings (2-3 bullet points)
3. Total patterns found and average confidence score""",
        agent=decision_mapper,
        context=[context_task],
    )


def create_decision_miner_crew(
    target: str,
    llm=None,
    verbose: bool = True
) -> Crew:
    """
    Create the full Decision Miner crew.

    Args:
        target: The subreddit, forum, or search query to analyze
        llm: Optional LLM to use (defaults to CrewAI's default)
        verbose: Whether to show detailed output

    Returns:
        Configured Crew ready to kickoff
    """
    # Create agents with tools
    friction_listener = create_friction_listener(
        llm=llm,
        tools=[tavily_search_tool, search_subreddit]
    )
    decision_mapper = create_decision_mapper(llm=llm)

    # Create tasks
    scan_task = create_scan_task(target, friction_listener)
    analyze_task = create_analyze_task(decision_mapper, scan_task)

    # Assemble crew
    crew = Crew(
        agents=[friction_listener, decision_mapper],
        tasks=[scan_task, analyze_task],
        process=Process.sequential,
        verbose=verbose,
    )

    return crew


def run_decision_miner(
    target: str,
    llm=None,
    verbose: bool = True
) -> str:
    """
    Run the full Decision Miner pipeline.

    Args:
        target: The subreddit or search query to analyze
        llm: Optional LLM override
        verbose: Show detailed output

    Returns:
        Analysis results as string
    """
    crew = create_decision_miner_crew(target, llm, verbose)
    result = crew.kickoff()
    return str(result)
