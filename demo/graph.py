"""Lapis LangGraph: alur agent sebagai state machine.

Kenapa graph, bukan chain? Karena agent perlu LOOP: model minta tool -> jalankan
tool -> balik ke model. Graph bikin loop itu eksplisit, bisa di-limit, di-resume,
dan tiap node bisa dipantau.

Alur:
    START -> agent -> (ada tool_calls & langkah < MAX ?) -> tools -> agent -> ... -> END
"""
from typing import Annotated, TypedDict

from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from .llm import make_llm
from .tools import TOOLS

MAX_LANGKAH = 4  # guard: maksimal 4 putaran agent->tools, biar tidak loop abadi

SISTEM = SystemMessage(
    "Kamu asisten yang memakai tool bila perlu. "
    "Untuk aritmetika WAJIB pakai tool tambah, jangan hitung sendiri. "
    "Untuk menghitung kata WAJIB pakai tool hitung_kata. "
    "Jawab akhir dengan bahasa Indonesia yang singkat."
)

llm_with_tools = make_llm().bind_tools(TOOLS)


class State(TypedDict):
    messages: Annotated[list, add_messages]  # add_messages = append, bukan timpa
    langkah: int


def agent(state: State) -> dict:
    """Node: satu panggilan LLM (bisa minta tool, bisa langsung jawab)."""
    jawab = llm_with_tools.invoke([SISTEM, *state["messages"]])
    return {"messages": [jawab], "langkah": state.get("langkah", 0) + 1}


def lanjut(state: State) -> str:
    """Conditional edge: ke 'tools', atau selesai."""
    if state.get("langkah", 0) >= MAX_LANGKAH:
        return END
    return tools_condition(state)  # "tools" kalau ada tool_calls, else END


def build_graph():
    g = StateGraph(State)
    g.add_node("agent", agent)
    g.add_node("tools", ToolNode(TOOLS))

    g.add_edge(START, "agent")
    g.add_conditional_edges("agent", lanjut, {"tools": "tools", END: END})
    g.add_edge("tools", "agent")  # hasil tool balik ke model

    # checkpointer = state disimpan per thread_id -> bisa lanjut percakapan
    return g.compile(checkpointer=MemorySaver())


def run(pertanyaan: str, tracer=None, thread_id: str = "demo-1") -> tuple[str, list]:
    """Jalankan graph. Return (jawaban_akhir, semua_message)."""
    graph = build_graph()
    config = {"configurable": {"thread_id": thread_id}}
    if tracer:
        config["callbacks"] = [tracer]

    hasil = graph.invoke({"messages": [("user", pertanyaan)], "langkah": 0}, config=config)
    pesan = hasil["messages"]
    jawaban = next(
        (m.content for m in reversed(pesan) if m.type == "ai" and m.content), ""
    )
    return jawaban, pesan
