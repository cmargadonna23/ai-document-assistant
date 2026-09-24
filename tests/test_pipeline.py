from src.config import AppConfig
from src.rag.pipeline import DocumentAssistant


class FakeEmbeddings:
    def embed_texts(self, texts):
        return [self._vector(text) for text in texts]

    def embed_query(self, text):
        return self._vector(text)

    @staticmethod
    def _vector(text):
        lower = text.lower()
        return [
            float("pto" in lower or "vacation" in lower),
            float("security" in lower or "password" in lower),
            0.1,
        ]


class FakeTextService:
    def answer(self, *, question, sources, history=None):
        return f"Grounded answer from {sources[0].chunk.source} [S1]"

    def summarize(self, *, source_name, context):
        return f"Summary of {source_name}: {context[:20]}"

    def compare(self, *, first_name, first_context, second_name, second_context):
        return f"Compare {first_name} vs {second_name}"


def test_pipeline_indexes_and_answers_without_cloud_calls():
    assistant = DocumentAssistant(
        api_key="not-used",
        config=AppConfig(chunk_size=300, chunk_overlap=30),
        embedding_provider=FakeEmbeddings(),
        text_service=FakeTextService(),
    )
    assistant.index_documents(
        [
            ("handbook.txt", b"PTO vacation policy gives employees fifteen days."),
            ("security.txt", b"Security policy requires strong passwords."),
        ]
    )
    answer = assistant.ask("What is the PTO vacation policy?")
    assert "handbook.txt" in answer.text
    assert answer.sources[0].chunk.source == "handbook.txt"
    assert len(assistant.records) == 2
