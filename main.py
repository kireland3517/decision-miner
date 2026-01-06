#!/usr/bin/env python3
"""
Decision Miner - Entry Point

Discover decision debt by analyzing online discussions where people
vent about ambiguity, workarounds, and process friction.

Usage:
    # Analyze a subreddit
    python main.py --subreddit socialwork --topic "documentation frustration"

    # General search
    python main.py --search "healthcare workers policy workaround reddit"

    # Validate on local file (shadow script)
    python main.py --file data/samples/reddit_thread.txt
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

load_dotenv()
console = Console()


def run_subreddit_analysis(subreddit: str, topic: str, verbose: bool = True):
    """Analyze a specific subreddit for decision debt."""
    from src.crew import run_decision_miner

    target = f"r/{subreddit} discussions about {topic}"
    console.print(f"\n[bold blue]Analyzing:[/bold blue] {target}\n")

    result = run_decision_miner(target, verbose=verbose)

    console.print("\n")
    console.print(Panel(
        Markdown(result),
        title="[bold green]Decision Bottleneck Report[/bold green]",
        border_style="green"
    ))


def run_search_analysis(query: str, verbose: bool = True):
    """Run analysis on a general search query."""
    from src.crew import run_decision_miner

    console.print(f"\n[bold blue]Searching:[/bold blue] {query}\n")

    result = run_decision_miner(query, verbose=verbose)

    console.print("\n")
    console.print(Panel(
        Markdown(result),
        title="[bold green]Decision Bottleneck Report[/bold green]",
        border_style="green"
    ))


def run_file_analysis(file_path: str, verbose: bool = True):
    """Analyze a local text file (shadow validation)."""
    # Import here to avoid loading everything for simple runs
    from scripts.shadow_validator import run_analysis

    result = run_analysis(file_path, verbose=verbose)

    console.print("\n")
    console.print(Panel(
        Markdown(result["analysis"]),
        title="[bold green]Decision Pattern Analysis[/bold green]",
        border_style="green"
    ))


def main():
    parser = argparse.ArgumentParser(
        description="Decision Miner - Discover decision debt in online discussions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --subreddit socialwork --topic "documentation"
  python main.py --subreddit sysadmin --topic "approval process frustration"
  python main.py --search "nurses workaround policy reddit"
  python main.py --file data/samples/thread.txt
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--subreddit", "-r",
        help="Subreddit to analyze (without r/)"
    )
    group.add_argument(
        "--search", "-s",
        help="General search query"
    )
    group.add_argument(
        "--file", "-f",
        help="Local text file to analyze (shadow validation)"
    )

    parser.add_argument(
        "--topic", "-t",
        help="Topic to search within subreddit (required with --subreddit)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose crew output"
    )

    args = parser.parse_args()

    # Validate subreddit requires topic
    if args.subreddit and not args.topic:
        parser.error("--subreddit requires --topic")

    try:
        if args.subreddit:
            run_subreddit_analysis(args.subreddit, args.topic, verbose=not args.quiet)
        elif args.search:
            run_search_analysis(args.search, verbose=not args.quiet)
        elif args.file:
            run_file_analysis(args.file, verbose=not args.quiet)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        raise


if __name__ == "__main__":
    main()
