from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from Backend.config.classes import ModelConfig
from Backend.config.constants import MAIN_PROMPT
from Backend.services.openai_service import build_prompt, build_llm
from Backend.utils.tools import build_sql_tool, make_chart
from Backend.utils.validators import language_filter


def create_agent(
    model: ModelConfig,
    clinic_code: str
):
    try:
        llm = build_llm(model)
        sql_tool = build_sql_tool(llm, clinic_code)
        schema = sql_tool("What tables are there? And what are their schemas?")["output"]
        tools = [sql_tool, make_chart] # Add tools if needed

        final_prompt = f"{MAIN_PROMPT}\n{schema}\n"
        prompt_template = build_prompt(final_prompt)

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
            memory=memory
        )

        def chat_with_agent(query: str) -> str:
            try:
                if not query or not query.strip():
                    raise ValueError(
                        "Providing an empty input is not supported.")

                if language_filter(query):
                    return "Please use a respectful language."

                inp = query.strip()
                otp = executor.invoke({"input": inp})
                return otp["output"].strip()

            except Exception as chatError:
                return f"Error appeared at conversation level: {chatError}."

        return chat_with_agent

    except Exception as factoryError:
        def dead_chatbot(_: str, err=factoryError):
            return f"Error appeared at factory level: {err}."
        return dead_chatbot
