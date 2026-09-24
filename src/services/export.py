"""Export helpers for chat transcripts."""

from __future__ import annotations

from datetime import datetime, timezone


def build_transcript_markdown(messages: list[dict]) -> str:
    """Convert Streamlit-style chat state into a readable Markdown transcript."""

    lines = [
        "# AI Document Assistant Transcript",
        "",
        f"Exported: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
    ]

    for message in messages:
        role = message.get("role", "user")
        heading = "You" if role == "user" else "Assistant"
        lines.extend([f"## {heading}", "", str(message.get("content", "")), ""])

        sources = message.get("sources") or []
        if sources:
            lines.append("**Sources**")
            for source in sources:
                lines.append(
                    f"- {source.get('label', 'Source')} (similarity {source.get('score', 0):.3f})"
                )
            lines.append("")

    return "\n".join(lines).strip() + "\n"
