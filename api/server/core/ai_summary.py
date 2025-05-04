from langchain_openai import ChatOpenAI
from openai import APIError
from server.core.config import settings

llm = ChatOpenAI(model="gpt-4o-mini", temperature=1, max_retries=2, api_key=settings.OPENAI_API_KEY)


def generate_summary(user_query: str, rag_context: str) -> str:
    messages = [
        (
            "system",
            f"""\
You are an environment restoration expert. Users come to you with questions about the environment \
and how to restore it.
Using the context provided answer the users question

Output should be in markdown format.

Output format:
#### Answer with context
Answer to the primary question only using the context provided,
dont answer anything without using the context provided.
#### Answer without using context.
Answer to the primary question without using the context provided.

context: {rag_context}
""",
        ),
        ("human", user_query),
    ]

    try:
        ai_msg = llm.invoke(messages)
        return ai_msg.content
    except APIError as e:
        print(f"Call to OpenAPI failed, returning empty summary: message={e.message}")
        return ""
