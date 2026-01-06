#!/usr/bin/env python3
"""
Shadow Validator Script

Tests the Decision Mapper logic on manually exported text files (Reddit threads,
LinkedIn posts, etc.) before investing in scraping infrastructure.

Usage:
    python scripts/shadow_validator.py data/samples/reddit_thread.txt
    python scripts/shadow_validator.py data/samples/reddit_thread.txt --output json
"""

import sys
import json
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from crewai import Crew, Task, Process
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from src.agents.decision_mapper import create_decision_mapper
from src.models.decision_pattern import DecisionPattern, DecisionBottleneckReport

load_dotenv()
console = Console()


def load_text_file(file_path: str) -> str:
    """Load content from a text file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return path.read_text(encoding="utf-8")


def create_analysis_task(content: str, decision_mapper) -> Task:
    """Create a task for the Decision Mapper to analyze content."""
    return Task(
        description=f"""Analyze the following content from an online discussion and extract decision patterns.

For each distinct decision bottleneck you identify, provide:
1. **ambiguous_trigger**: What situation created the need for a decision?
2. **manual_judgment**: Why couldn't a simple rule handle this?
3. **shadow_tool**: What workaround did they use or mention? (if any)
4. **downstream_risk**: What happens if they get this decision wrong?
5. **source_context**: Quote the specific text that revealed this pattern
6. **confidence_score**: Rate 0.0-1.0 based on how explicitly all elements appear

Look for these signals:
- "The policy says X, but in reality we do Y"
- "I just make a judgment call..."
- "I know I'm not supposed to, but..."
- "There's no official process for..."
- Personal workarounds (spreadsheets, side-chats, sticky notes)

CONTENT TO ANALYZE:
---
{content}
---

Return your analysis as a structured list of decision patterns found.""",
        expected_output="""A detailed analysis containing:
1. Number of decision patterns found
2. For each pattern: all six fields (trigger, judgment, shadow_tool, risk, context, confidence)
3. Key findings summary (2-3 bullet points about the decision debt discovered)""",
        agent=decision_mapper,
    )


def run_analysis(file_path: str, verbose: bool = True) -> dict:
    """Run the Decision Mapper analysis on a text file."""
    console.print(f"\n[bold blue]Loading file:[/bold blue] {file_path}")
    content = load_text_file(file_path)
    console.print(f"[dim]Content length: {len(content)} characters[/dim]\n")

    # Create agent and task
    decision_mapper = create_decision_mapper()
    analysis_task = create_analysis_task(content, decision_mapper)

    # Create and run crew
    crew = Crew(
        agents=[decision_mapper],
        tasks=[analysis_task],
        process=Process.sequential,
        verbose=verbose,
    )

    console.print("[bold yellow]Running Decision Mapper analysis...[/bold yellow]\n")
    result = crew.kickoff()

    return {
        "file": file_path,
        "content_length": len(content),
        "analysis": str(result),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate Decision Mapper logic on text files"
    )
    parser.add_argument(
        "file",
        help="Path to text file containing discussion content to analyze"
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose crew output"
    )

    args = parser.parse_args()

    try:
        result = run_analysis(args.file, verbose=not args.quiet)

        if args.output == "json":
            print(json.dumps(result, indent=2))
        else:
            console.print("\n")
            console.print(Panel(
                Markdown(result["analysis"]),
                title="[bold green]Decision Pattern Analysis Results[/bold green]",
                border_style="green"
            ))

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error during analysis:[/bold red] {e}")
        raise


if __name__ == "__main__":
    main()
