from rag.pipeline import ask_question


class FakeChain:
    def invoke(self, question):
        return "The delegate refused the application because the requirements were not satisfied."


class FakeRetriever:
    def invoke(self, question):
        return [
            type(
                "FakeDoc",
                (),
                {
                    "metadata": {
                        "source": "test_case.pdf",
                        "page": 7
                    },
                    "page_content": "The delegate considered the evidence provided."
                }
            )()
        ]


def test_ask_question_returns_answer_and_sources():
    chain = FakeChain()
    retriever = FakeRetriever()

    result = ask_question(
        (chain, retriever),
        "Why did the delegate refuse the application?"
    )

    assert "delegate refused" in result["answer"]
    assert len(result["sources"]) == 1
    assert result["sources"][0]["case"] == "test_case.pdf"
    assert result["sources"][0]["page"] == 8
    assert "evidence provided" in result["sources"][0]["excerpt"]


def test_ask_question_returns_multiple_sources():
    class MultiSourceRetriever:
        def invoke(self, question):
            return [
                type(
                    "FakeDoc",
                    (),
                    {
                        "metadata": {"source": "case_a.pdf", "page": 0},
                        "page_content": "First relevant legal passage."
                    }
                )(),
                type(
                    "FakeDoc",
                    (),
                    {
                        "metadata": {"source": "case_b.pdf", "page": 4},
                        "page_content": "Second relevant legal passage."
                    }
                )()
            ]

    result = ask_question(
        (FakeChain(), MultiSourceRetriever()),
        "What evidence was considered?"
    )

    assert len(result["sources"]) == 2
    assert result["sources"][0]["case"] == "case_a.pdf"
    assert result["sources"][1]["case"] == "case_b.pdf"
