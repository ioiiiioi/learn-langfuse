# 3 lapis yang dipakai bareng:
#   LangChain  -> komponen (prompt template, tool, model wrapper)
#   LangGraph  -> orkestrasi alur agent (state machine + loop)
#   Langfuse   -> observability (trace tiap step, token, cost, latency)
import os

from dotenv import load_dotenv

load_dotenv()

# OmniRoute lokal (OpenAI-compatible). Ganti ke OpenAI/Anthropic cukup ubah 2 env ini.
BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:20128/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "sk-local")
MODEL = os.getenv("MODEL", "deepseek/deepseek-flash")


def make_llm(**kwargs):
    """LangChain wrapper untuk model OpenAI-compatible."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=MODEL,
        base_url=BASE_URL,
        api_key=API_KEY,
        temperature=0,
        streaming=False,  # omniroute lokal tidak dukung stream
        **kwargs,
    )


def make_tracer():
    """Langfuse callback handler. Kalau key tidak ada, tracing dilewati."""
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        return None
    from langfuse.langchain import CallbackHandler

    return CallbackHandler()
