from langchain.agents import AgentExecutor, tool
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

if __name__ == "__main__":
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=1)

    @tool
    def get_word_length(word: str) -> int:
        """Returns the length of a word."""
        return len(word)

    MEMORY_KEY = "chat_history"
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are very powerful assistant, but bad at calculating lengths of words.",
            ),
            MessagesPlaceholder(variable_name=MEMORY_KEY),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    tools = [get_word_length]

    llm_with_tools = llm.bind_tools(tools)

    chat_history = []

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

    input1 = "how many letters in the word educa?"
    result = agent_executor.invoke({"input": input1, "chat_history": chat_history})

    chat_history.extend(
        [
            HumanMessage(content=input1),
            AIMessage(content=result["output"]),
        ]
    )
    agent_executor.invoke(
        {"input": "is that a real word?", "chat_history": chat_history}
    )
