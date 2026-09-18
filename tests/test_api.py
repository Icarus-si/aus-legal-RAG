from fastapi.testclient import TestClient
import app.main as main_module

client = TestClient(main_module.app)


def test_ingest_rejects_non_pdf():
    response = client.post(
        "/ingest",
        files={
            "files": (
                "sample.txt",
                b"This is not a PDF",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400
    assert "is not a PDF" in response.json()["detail"]


def test_ask_without_index_returns_400(monkeypatch):
    main_module.rag_chain = None

    def fake_load_vectorstore():
        raise FileNotFoundError("FAISS index not found")

    monkeypatch.setattr(
        main_module,
        "load_vectorstore",
        fake_load_vectorstore
    )

    response = client.post(
        "/ask",
        json={"question": "What is this case about?"}
    )

    assert response.status_code == 400
    assert "No documents indexed yet" in response.json()["detail"]


def test_question_input_validation():
    response = client.post(
        "/ask",
        json={}
    )

    assert response.status_code == 422
