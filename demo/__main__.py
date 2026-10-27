"""Demo CLI: satu pertanyaan, tiga lapis kelihatan.

    uv run python -m demo "berapa 17 + 25 dan berapa kata di kalimat ini"
    uv run python -m demo "..." --tanpa-trace
"""
import sys

from .chain import jelaskan
from .graph import run
from .llm import MODEL, make_tracer


def tampilkan_langkah(pesan: list) -> None:
    for i, m in enumerate(pesan, 1):
        if m.type == "human":
            print(f"{i}. [user]  {m.content}")
        elif m.type == "ai" and getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                print(f"{i}. [agent] minta tool {tc['name']}({tc['args']})")
        elif m.type == "tool":
            print(f"{i}. [tool]  hasil = {m.content}")
        elif m.type == "ai":
            print(f"{i}. [agent] {m.content}")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pertanyaan = args[0] if args else "Berapa 17 + 25? Lalu berapa kata di 'agent itu belajar graph'?"

    tracer = None if "--tanpa-trace" in sys.argv else make_tracer()
    print(f"model    : {MODEL}")
    print(f"langfuse : {'aktif' if tracer else 'nonaktif (isi LANGFUSE_* di .env)'}")

    print("\n=== 1. LangChain (chain sederhana: prompt | model | parser) ===")
    print(jelaskan("apa itu LangGraph", tracer=tracer))

    print("\n=== 2. LangGraph (agent + tool loop) ===")
    jawaban, pesan = run(pertanyaan, tracer=tracer)
    tampilkan_langkah(pesan)
    print(f"\njawaban akhir: {jawaban}")

    print("\n=== 3. Langfuse (trace) ===")
    if tracer:
        from langfuse import get_client

        print("cek dashboard Langfuse -> traces; tiap node/tool/LLM call jadi span.")
        get_client().flush()  # pastikan span terkirim sebelum proses keluar
    else:
        print("set LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY (self-host: cd ~/Documents/utils/langfuse && docker compose up -d)")


if __name__ == "__main__":
    main()
