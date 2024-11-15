from config import settings
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini", temperature=1, max_retries=2, api_key=settings.OPENAI_API_KEY
)


def generate_summary(user_query: str, rag_context: str) -> str:
    messages = [
        (
            "system",
            f"""\
You are an environment restoration expert. Users come to you with questions about the environment \
and how to restore it.
Using the context provided answer the users question
if no context is provided, answer the question as best as you can.

Output should be in markdown format.

Output format:
#### Answer
Answer to the primary question.
#### Explanation
Summary of how you arrived at the answer

context: {rag_context}
""",
        ),
        ("human", user_query),
    ]

    ai_msg = llm.invoke(messages)
    return ai_msg.content
