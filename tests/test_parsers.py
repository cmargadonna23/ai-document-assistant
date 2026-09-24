import io

from docx import Document

from src.ingestion.parsers import DocumentParseError, parse_document


def test_txt_parser():
    sections = parse_document("notes.txt", b"First line\nSecond line")
    assert len(sections) == 1
    assert "Second line" in sections[0].text


def test_csv_parser_renders_named_columns():
    sections = parse_document("people.csv", b"name,role\nAva,Engineer\nLeo,Designer\n")
    combined = "\n".join(section.text for section in sections)
    assert "name: Ava" in combined
    assert "role: Designer" in combined


def test_docx_parser():
    document = Document()
    document.add_paragraph("Remote work requires manager approval.")
    buffer = io.BytesIO()
    document.save(buffer)
    sections = parse_document("policy.docx", buffer.getvalue())
    assert "manager approval" in sections[0].text


def test_unsupported_extension_is_rejected():
    try:
        parse_document("malware.exe", b"data")
    except DocumentParseError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("Expected DocumentParseError")
