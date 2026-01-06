from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DecisionPattern(BaseModel):
    """A structured representation of a decision bottleneck found in human discussions."""

    ambiguous_trigger: str = Field(
        description="What started the mess - the situation that created ambiguity"
    )
    manual_judgment: str = Field(
        description="Why a simple rule failed - what human judgment was required"
    )
    shadow_tool: Optional[str] = Field(
        default=None,
        description="Workaround used: sticky note, side-chat, personal spreadsheet, etc."
    )
    downstream_risk: str = Field(
        description="What happens if they get the decision wrong - consequences"
    )
    source_context: str = Field(
        description="Original quote or thread excerpt that revealed this pattern"
    )
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="Agent's confidence in this pattern extraction (0-1)"
    )


class FrictionSignal(BaseModel):
    """Raw frustration indicator detected in online discussions."""

    source_url: Optional[str] = Field(
        default=None,
        description="URL of the source thread/post"
    )
    source_text: str = Field(
        description="The raw text that triggered the friction detection"
    )
    signal_type: str = Field(
        description="Type of friction: policy_reality_gap, unofficial_process, judgment_call, workaround"
    )
    intensity: float = Field(
        ge=0.0, le=1.0,
        description="How strong the frustration signal is (0-1)"
    )
    detected_at: datetime = Field(
        default_factory=datetime.now,
        description="When this signal was detected"
    )


class DecisionBottleneckReport(BaseModel):
    """Aggregated output for demonstrating decision debt to organizations."""

    domain: str = Field(
        description="Industry/domain analyzed: healthcare, social work, finance, etc."
    )
    source_description: str = Field(
        description="Where the data came from: subreddit name, LinkedIn group, etc."
    )
    patterns: list[DecisionPattern] = Field(
        default_factory=list,
        description="List of decision patterns discovered"
    )
    total_signals_analyzed: int = Field(
        default=0,
        description="How many friction signals were processed"
    )
    key_findings: list[str] = Field(
        default_factory=list,
        description="Top-level insights for the executive summary"
    )

    @property
    def pattern_count(self) -> int:
        return len(self.patterns)

    def add_pattern(self, pattern: DecisionPattern) -> None:
        self.patterns.append(pattern)

    def generate_summary(self) -> str:
        """Generate a human-readable summary of the decision debt found."""
        if not self.patterns:
            return "No decision patterns found in the analyzed content."

        summary_lines = [
            f"## Decision Bottleneck Report: {self.domain}",
            f"**Source:** {self.source_description}",
            f"**Patterns Found:** {self.pattern_count}",
            f"**Signals Analyzed:** {self.total_signals_analyzed}",
            "",
            "### Key Findings",
        ]

        for i, finding in enumerate(self.key_findings, 1):
            summary_lines.append(f"{i}. {finding}")

        summary_lines.extend(["", "### Decision Patterns"])

        for i, pattern in enumerate(self.patterns, 1):
            summary_lines.extend([
                f"",
                f"**Pattern {i}** (confidence: {pattern.confidence_score:.0%})",
                f"- **Trigger:** {pattern.ambiguous_trigger}",
                f"- **Judgment Required:** {pattern.manual_judgment}",
                f"- **Shadow Tool:** {pattern.shadow_tool or 'None identified'}",
                f"- **Risk:** {pattern.downstream_risk}",
            ])

        return "\n".join(summary_lines)
