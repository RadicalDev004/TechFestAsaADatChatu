import base64
import re
from typing import Callable
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain.tools import tool
import pandas as pd
import io
import matplotlib.pyplot as plt
from Backend.config.constants import DATA_PATH

bots: dict[int, Callable] = {}

def is_image(s: str) -> bool:
    auxiliar = re.compile(r"^data:image/png;base64,", re.IGNORECASE)
    return bool(auxiliar.match(s.strip()))


def build_sql_tool(llm, db_path=DATA_PATH):
    db = SQLDatabase.from_uri(db_path)
    sql_agent = create_sql_agent(llm, db=db, top_k=100)

    @tool("sql_query_tool")
    def run_sql(query: str) -> str:
        """Ask natural language questions about the database and get structured results."""
        return sql_agent.invoke({"input": query})
    return run_sql


@tool("make_chart", return_direct=True)
def make_chart(data: list, x: str, y: str, chart: str = "bar") -> str:
    """Create a chart from SQL results.
    Args:
        data: List of dicts containing query results.
        x: Column name for X-axis.
        y: Column name for Y-axis.
        chart: One of ["bar", "line", "pie", etc.]. Default is "bar".
    Returns:
        Raw PNG bytes.
    """
    df = pd.DataFrame(data)
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
