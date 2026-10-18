# Decision Miner

Discover **decision debt** by mining online discussions where people vent about ambiguity, workarounds, and process friction.

Decision Miner uses AI agents to scan Reddit threads and forums, find high-signal frustration posts, and extract structured decision patterns — the invisible micro-decisions employees make daily without clear guidance.

**Who it's for:** operations, product, and process-improvement researchers looking for undocumented decision-making inside an industry or role.

**Stack:** Python 3.10–3.13, CrewAI, Tavily, OpenAI, Pydantic.

## How It Works

Two AI agents work in sequence via [CrewAI](https://www.crewai.com/):

1. **Friction Listener** — Scouts Reddit/forums for threads revealing policy-reality gaps, shadow systems, and judgment calls
2. **Decision Mapper** — Transforms raw frustration into structured `DecisionPattern` objects with triggers, required judgment, workarounds, and downstream risks

```
Search query → Tavily Search → Reddit Thread Fetch → Friction Analysis → Decision Patterns → Report
```

## Quick Start

### Prerequisites

- Python 3.10–3.13 (3.14 not supported by CrewAI)
- [Tavily API key](https://tavily.com) (free tier: 1000 searches/month)
- [OpenAI API key](https://platform.openai.com/api-keys)

### Setup

```bash
git clone https://github.com/kireland3517/decision-miner.git
cd decision-miner

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env and add your TAVILY_API_KEY and OPENAI_API_KEY
```

### Usage

**Analyze a subreddit:**
```bash
python main.py --subreddit socialwork --topic "documentation frustration"
python main.py --subreddit sysadmin --topic "approval process frustration"
python main.py --subreddit nursing --topic "charting workarounds"
```

**General search:**
```bash
python main.py --search "healthcare workers policy workaround reddit"
```

**Analyze a local text file (no API calls):**
```bash
python main.py --file data/samples/sample_reddit_thread.txt
```

**Quiet mode** (suppress verbose agent output):
```bash
python main.py --subreddit teachers --topic "grading policy" --quiet
```

## What It Finds

Decision Miner looks for these friction signals in discussions:

| Signal Type | Example Language |
|---|---|
| Policy-Reality Gap | "The policy says X, but in reality we do Y" |
| Unofficial Process | "There's no official process for..." |
| Judgment Calls | "I just make a judgment call..." |
| Forbidden Workarounds | "I know I'm not supposed to, but..." |
| Missing Guidelines | "Nobody ever trained me on..." |
| Shadow Systems | "I keep my own spreadsheet..." |

Each extracted pattern includes:

- **Ambiguous Trigger** — What situation created decision ambiguity
- **Manual Judgment** — Why a simple rule couldn't handle it
- **Shadow Tool** — The workaround used (spreadsheets, side chats, tribal knowledge)
- **Downstream Risk** — Consequences of getting the decision wrong
- **Confidence Score** — 0.0–1.0 based on how explicitly all elements appear

## Tools

The agents have access to four search/fetch tools:

| Tool | Purpose |
|---|---|
| Search Reddit and Forums | Tavily-powered web search with full content |
| Search Subreddit | Targeted search within a specific subreddit |
| Fetch Reddit Thread | Fetches full comment tree via Reddit's `.json` endpoint (no API key needed) |
| Extract Full Page Content | Tavily Extract for full page content from any URL |

## Project Structure

```
decision-miner/
├── main.py                         # CLI entry point
├── requirements.txt                # Dependencies
├── .env.example                    # API key template
├── prompts/
│   └── agent_personas.md           # Agent role definitions
├── data/
│   └── samples/
│       └── sample_reddit_thread.txt
├── scripts/
│   └── shadow_validator.py         # Local file analysis
└── src/
    ├── crew.py                     # CrewAI orchestration
    ├── agents/
    │   ├── friction_listener.py    # Thread scanner agent
    │   └── decision_mapper.py      # Pattern extraction agent
    ├── tools/
    │   ├── tavily_search.py        # Tavily search + extract tools
    │   └── reddit_json.py          # Reddit .json thread fetcher
    └── models/
        └── decision_pattern.py     # Pydantic data models
```

## License

MIT
