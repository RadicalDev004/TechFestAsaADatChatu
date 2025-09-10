import base64
import re
import duckdb
from typing import Callable
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain.tools import tool
import pandas as pd
import io
import matplotlib.pyplot as plt
from openai import OpenAI

from Backend.config.constants import DATA_PATH, DB_FILE

bots: dict[int, Callable] = {}

def is_image(s: str) -> bool:
    auxiliar = re.compile(r"^data:image/png;base64,", re.IGNORECASE)
    return bool(auxiliar.match(s.strip()))

def text_to_speech(s:str) -> str:
    client = OpenAI()

    try:
        with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=s
        ) as resp:
            audio_bytes = resp.read()
    except Exception:
        with client.audio.speech.with_streaming_response.create(
                model="gpt-4o-realtime-preview-2024-12-17",
                voice="alloy",
                input=s
        ) as resp:
            audio_bytes = resp.read()

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    helper = f'data:audio/mpeg;base64,{audio_b64}'
    return f'<audio>{helper}</audio>'


def build_sql_tool(llm, clinic_code, db_path=DATA_PATH):
    con = duckdb.connect(DB_FILE.as_posix())
    tables = con.execute("SHOW TABLES").fetchall()
    to_be_included = []
    for (t,) in tables:
        if t.startswith(clinic_code):
            to_be_included.append(t)
    con.close()

    db = SQLDatabase.from_uri(db_path, include_tables=to_be_included)
    sql_agent = create_sql_agent(llm, db=db, top_k=10)

    @tool("sql_query_tool")
    def run_sql(natural_language: str) -> str:
        """Ask natural language questions about the database and get structured results."""
        return sql_agent.invoke({"input": natural_language})
    return run_sql


@tool("make_chart", return_direct=True)
def make_chart(data_from_sql_query_tool: list, x: str, y: str, chart: str = "bar") -> str:

    """Create a chart from SQL results.
    Args:
        data_from_sql_query_tool: List of dicts containing query results.
        x: Column name for X-axis.
        y: Column name for Y-axis.
        chart: One of ["bar", "line", "pie", etc.]. Default is "bar".
    Returns:
        Raw PNG bytes.
    """
    df = pd.DataFrame(data_from_sql_query_tool)
    fig, ax = plt.subplots(figsize=(6, 4))

    if chart == "line":
        df.plot(x=x, y=y, kind="line", ax=ax)
    elif chart == "pie":
        df.set_index(x)[y].plot(kind="pie", ax=ax, autopct="%1.1f%%")
        ax.set_ylabel("")
    elif chart == "scatter":
        df.plot.scatter(x=x, y=y, ax=ax)
    elif chart == "histogram":
        ax.hist(df[x], weights=df[y], bins=30)
        ax.set_xlabel(x)
        ax.set_ylabel(y)
    elif chart == "box":
        df[[x, y]].plot.box(ax=ax)
    else:
        df.plot(x=x, y=y, kind="bar", ax=ax)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    return f"data:image/png;base64,{b64}"
