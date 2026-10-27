"""Lapis LangChain: rangkai komponen jadi pipeline sederhana.

Pola khas:  prompt template  |  model  |  output parser
Ini cara paling dasar; agent yang lebih rumit ada di graph.py.
"""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .llm import make_llm

PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Kamu asisten riset yang singkat. Jawab maksimal 3 kalimat, bahasa Indonesia.",
        ),
        ("human", "Jelaskan singkat: {topik}"),
    ]
)

# chain = prompt | model | parser  (LCEL: tanda | menyambung output->input)
chain = PROMPT | make_llm() | StrOutputParser()


def jelaskan(topik: str, tracer=None) -> str:
    """Jalankan chain. `tracer` = Langfuse callback (opsional)."""
    config = {"callbacks": [tracer]} if tracer else {}
    return chain.invoke({"topik": topik}, config=config)
