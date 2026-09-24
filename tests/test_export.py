from src.services.export import build_transcript_markdown


def test_transcript_export_contains_messages_and_sources():
    messages = [
        {"role": "user", "content": "What is PTO?"},
        {
            "role": "assistant",
            "content": "Employees receive 15 days.",
            "sources": [{"label": "handbook.pdf — page 4", "score": 0.91}],
        },
    ]
    output = build_transcript_markdown(messages)
    assert "What is PTO?" in output
    assert "15 days" in output
    assert "handbook.pdf" in output
