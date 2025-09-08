from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from Backend.config.classes import ModelConfig, PromptConfig
from Backend.services.openai_service import build_prompt, build_llm
from Backend.utils.tools import build_sql_tool, make_chart
from Backend.utils.validators import language_filter


def create_agent(
    model: ModelConfig,
    prompt: PromptConfig
):
    try:
        prompt_template = build_prompt(prompt)
        llm = build_llm(model)

        sql_tool = build_sql_tool(llm)
        tools = [sql_tool, make_chart] # Add tools if needed

        agent = create_openai_tools_agent(
            llm=llm,
            tools=tools,
            prompt=prompt_template
        )

        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True
        )

        def chat_with_agent(query: str) -> str:
            try:
                if not query or not query.strip():
                    raise ValueError(
                        "Providing an empty input is not supported.")

                if language_filter(query):
                    return "Please use a respectful language."

                user_input = query.strip()

                response = executor.invoke({"input": user_input})
                return response["output"].strip()

            except Exception as chatError:
                return f"Error appeared at conversation level: {chatError}."

        return chat_with_agent

    except Exception as factoryError:
        def dead_chatbot(_: str, err=factoryError):
            return f"Error appeared at factory level: {err}."
        return dead_chatbot

if __name__ == "__main__":
    # Minimal config for testing
    model_cfg = ModelConfig()
    prompt_cfg = PromptConfig()

    # Build the chat function
    chat = create_agent(model_cfg, prompt_cfg)

    print("💬 Agent is ready. Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower().strip() in {"exit", "quit"}:
            break
        response = chat(user_input)
        print("Bot :", response, "\n")
