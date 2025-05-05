import ast
import json

from langchain.agents import AgentExecutor, tool
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from qdrant_client import QdrantClient
from server.core.config import settings
from server.entities.chat import ChatMessage, Actor

llm = ChatOpenAI(model="gpt-4o-mini", temperature=1, api_key=settings.OPENAI_API_KEY)

vectordb_client = QdrantClient(
    url=settings.QDRANT_URL,
    https=True,
    api_key=settings.QDRANT_API_KEY
)

embedding_model = HuggingFaceEmbedding(model_name=settings.EMBEDDING_MODEL_NAME)


@tool
def get_restoration_context_for_message(country: str, message: str) -> int:
    """Returns the restoration context for a message"""
    # Embed query
    query_embedding = embedding_model.get_text_embedding(message)

    # Search in vector store
    results = vectordb_client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=query_embedding,
        limit=3,
    )

    rag_context = []
    for res in results.points:
        sources = ast.literal_eval(res.payload["sources"].split(";{")[0])
        rag_context.append(
            {
                "title": res.payload["title"],
                "url": sources["link"],
                "score": res.score,
                "text": json.loads(res.payload["_node_content"])["text"],
            }
        )

    print(f"RAG Context: {json.dumps(rag_context, indent=2)}")
    return json.dumps(rag_context)


MEMORY_KEY = "chat_history"
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """\
* Role *
You are an environment restoration expert. \
Users come to you with questions about the environment and how to restore it.

* Steps *
1. Understand the following details -
    a. country,city, or region where the restoration is needed.
    b. ecosystem type (e.g. forest, wetland, grassland, etc.)
    c. The primary problem they are facing.
2. Fetch the restoration context for the message once you have all the details.
2. Provide a response that includes -
    a. Answer to the primary question in 2 sections -
        i. Answer with context.
        ii. Answer without using context.
    b. Show the context of the restoration in a professional markdown format that includes
        i. Score.
        ii. Link.
        iii. Text from source.

* Conversation style/inputs *
1. Be professional and follow blazon style.
2. *Important* Always return in markdown so that its easy to read.
3. Include relevant links only from the restoration context.
4. If you dont know the answer, You can say you dont know the answer.
""",
        ),
        MessagesPlaceholder(variable_name=MEMORY_KEY),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


tools = [get_restoration_context_for_message]

llm_with_tools = llm.bind_tools(tools)


agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
        "chat_history": lambda x: x["chat_history"],
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


def get_chat_response(message: str, chat_history: list[ChatMessage]) -> str:
    chat_history_messages = [
        (
            AIMessage(content=chat_message.message)
            if chat_message.message_from == Actor.AGENT
            else HumanMessage(content=chat_message.message)
        )
        for chat_message in chat_history
    ]
    result = agent_executor.invoke(
        {"input": message, "chat_history": chat_history_messages}
    )
    return result["output"]
