# agent-demo — LangChain + LangGraph + Langfuse (1 project kecil)

Tujuan: satu contoh **sekali jalan** yang memperlihatkan peran masing-masing lapis.

| Lapis | File | Perannya di demo ini |
|---|---|---|
| **LangChain** | `demo/chain.py`, `demo/tools.py` | komponen: prompt template, model wrapper, output parser, 2 tool (`tambah`, `hitung_kata`) |
| **LangGraph** | `demo/graph.py` | alur agent: node `agent` ⇄ node `tools`, conditional edge, guard `MAX_LANGKAH`, checkpointer (state per `thread_id`) |
| **Langfuse** | `demo/llm.py` (`make_tracer`) | callback handler → setiap LLM call, tool call, dan node jadi span + token + latency di dashboard |

Model default: **OmniRoute lokal** (`http://localhost:20128/v1`, model `deepseek/deepseek-flash`), jadi tidak butuh API key berbayar.

## Jalanin

```bash
cd ~/Documents/belajar/langgraph-langfuse
uv run python -m demo "Berapa 17 + 25? Lalu berapa kata di 'agent itu belajar graph'?"
```

Tanpa tracing: tambah `--tanpa-trace`.

## Alur graph

```
START -> agent ──(ada tool_calls & langkah < 4)──> tools ──> agent -> ... -> END
              └─(tidak ada tool_calls / langkah habis)───────────────┘
```

- `agent`  : satu panggilan LLM (`make_llm().bind_tools(TOOLS)`)
- `tools`  : `ToolNode(TOOLS)` — eksekusi tool yang diminta model
- `lanjut` : conditional edge; pakai `tools_condition` + batas `MAX_LANGKAH=4` biar tak loop abadi
- `MemorySaver` : state disimpan per `thread_id`, jadi bisa lanjut percakapan

## Env

`.env` (sudah dibuat dari `.env.example`):

```
OPENAI_BASE_URL=http://localhost:20128/v1
OPENAI_API_KEY=sk-local
MODEL=deepseek/deepseek-flash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

Kalau `LANGFUSE_*` kosong, `make_tracer()` return `None` dan tracing dilewati (demo tetap jalan).

## Langfuse

Self-host sudah jalan di `~/Documents/utils/langfuse` (image resmi `langfuse/langfuse:4` + worker + postgres + clickhouse + redis + minio).

```bash
cd ~/Documents/utils/langfuse
docker compose up -d       # start
docker compose ps          # status
docker compose down        # stop (data tetap di volume)
```

- UI: http://localhost:3000 — login `jefri@ricefield.id` / `langfuse1234`
- Project & API key sudah di-provision otomatis lewat `LANGFUSE_INIT_*` (lihat `.env` di folder itu)
- Trace masuk ke project **agent-demo**

## Cara baca kodenya (urutan belajar)

1. `demo/chain.py` — pahami `prompt | llm | parser`. Ini "hello world" LangChain.
2. `demo/tools.py` — `@tool` + docstring → skema JSON yang dibaca model.
3. `demo/graph.py` — state, node, edge, conditional edge. Perhatikan `add_messages` vs `langkah`.
4. `demo/__main__.py` — pemanggilan + cara tracer disuntik lewat `config={"callbacks": [tracer]}`.
5. Buka Langfuse → lihat satu trace: ada span graph, span LLM, span tool, plus token & durasi.

## Catatan versi (penting saat debug)

- Stack ini pakai **Langfuse v4** (`langfuse/langfuse:4`) yang jalan dalam mode `events_only`: trace dikirim **lewat OTel** ke `POST /api/public/otel/v1/traces`. Endpoint lama `GET /api/public/traces` balas **404** — itu normal, bukan berarti tracing gagal.
- SDK `langfuse` 5.x otomatis pakai OTel, jadi cukup `LANGFUSE_PUBLIC_KEY` + `LANGFUSE_SECRET_KEY` + `LANGFUSE_HOST`.
- Cek data benar-benar masuk (jangan lihat tabel `traces`, kosong by design):

```bash
cd ~/Documents/utils/langfuse
CH=$(grep '^CLICKHOUSE_PASSWORD=' .env | cut -d= -f2)
docker exec langfuse-clickhouse-1 clickhouse-client --user clickhouse --password "$CH" \
  -q "SELECT type, name, count() FROM events_full GROUP BY type, name ORDER BY 3 DESC"
```

Hasil yang diharapkan kira-kira: `AGENT agent`, `TOOL tambah`, `TOOL hitung_kata`, `GENERATION ChatOpenAI`, `CHAIN LangGraph` / `lanjut` / `tools`.

## Troubleshooting

- `Bind for 0.0.0.0:5432 failed` → host sudah punya postgres lain; `docker-compose.override.yml` di folder langfuse sudah men-`!reset` port DB/cache ke host. Jangan dihapus.
- Trace tidak muncul di UI tapi demo jalan → pastikan `.env` demo `LANGFUSE_HOST=http://localhost:3000` (bukan 3030; 3030 itu worker internal).
- Trace tetap kosong → jalankan demo dengan `LANGFUSE_DEBUG=True uv run python -m demo "..."` dan cari baris `Langfuse tracer successfully initialized`.

## Eksperimen yang disarankan

- Naikkan `MAX_LANGKAH` dan tanya hal yang bikin model memanggil tool berkali-kali.
- Hapus `bind_tools` → lihat model menjawab tanpa tool (dan salah hitung).
- Tambah tool baru (mis. `sekarang()`), lihat otomatis muncul di skema.
- Hapus `checkpointer` → `thread_id` jadi tak berguna.
- Bandingkan model: `MODEL=moonshot/kimi-k3` (lihat cost di Langfuse).
