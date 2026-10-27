"""Tools ala LangChain: fungsi python yang bisa dipanggil model.

@tool -> otomatis jadi skema JSON buat function/tool calling.
Docstring = deskripsi yang dibaca model, jadi tulis jelas.
"""
from langchain_core.tools import tool


@tool
def tambah(a: float, b: float) -> float:
    """Jumlahkan dua angka.

    Args:
        a: angka pertama
        b: angka kedua
    """
    return a + b


@tool
def hitung_kata(teks: str) -> int:
    """Hitung jumlah kata dalam sebuah teks.

    Args:
        teks: kalimat yang mau dihitung
    """
    return len(teks.split())


TOOLS = [tambah, hitung_kata]
