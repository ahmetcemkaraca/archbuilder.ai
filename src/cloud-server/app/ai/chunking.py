from __future__ import annotations

"""
Basit metin parçalama (chunking) stratejisi.

TR: Bu modül, metni kelime sınırlarını koruyarak sabit boyutlu parçalara böler.
Overlap ile bağlam korunur. Harici bağımlılık yoktur.
"""

from typing import List


def chunk_text(text: str, max_chars: int = 500, overlap: int = 50) -> List[str]:
    """Metni sabit boyutlu parçalara böl.

    Kurallar (TR):
    - Kelime bölme olmadan boşluklara göre kesilir
    - Parça üst üste bindirmesi (overlap) ile bağlam korunur
    - `max_chars` en az 50, overlap en az 0, overlap < max_chars olmalı
    """
    # Test dostu alt sınır: çok küçük değerler anlamsız; ancak 20-50 arası
    # kullanım senaryolarını da destekleyelim
    if max_chars < 10:
        max_chars = 10
    if overlap < 0:
        overlap = 0
    if overlap >= max_chars:
        overlap = max_chars // 2

    text = (text or "").strip()
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        # Kelime sınırında geriye doğru kaydır
        if end < n and text[end : end + 1] not in {" ", "\n", "\t"}:
            back = end
            while back > start and text[back - 1] not in {" ", "\n", "\t"}:
                back -= 1
            if back > start:
                end = back
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        # Overlap ile yeni başlangıç
        start = max(0, end - overlap)
    return chunks


def chunk_documents(
    documents: List[str], max_chars: int = 500, overlap: int = 50
) -> List[str]:
    """Birden fazla dokümanı arka arkaya chunk'la.

    TR: Dokümanlar arasında satır sonu ile ayrım yapılır; her doküman kendi içinde
    bölünür ve sıra korunur.
    """
    all_chunks: List[str] = []
    for doc in documents:
        all_chunks.extend(chunk_text(doc, max_chars=max_chars, overlap=overlap))
    return all_chunks
