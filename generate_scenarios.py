"""Gera cenários sintéticos reprodutíveis, independentes e executáveis."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scenario_rules import evaluate

ROOT = Path(__file__).resolve().parent
DESCRIPTIONS = {
    "phone": "Normalização E.164 de número brasileiro para deduplicação de contatos",
    "retry": "Intervalo limitado por teto para reenvio de mensagens com falha",
    "sla": "Classificação de prazo de atendimento em um pipeline de suporte",
    "message": "Seleção entre atendimento de sessão e template por janela configurada",
    "lead_score": "Pontuação de completude de cadastro para qualificação de lead",
}

def build_case(n: int) -> dict:
    if n < 1:
        raise ValueError("n deve ser positivo")
    kind = ("phone", "retry", "sla", "message", "lead_score")[(n - 1) % 5]
    if kind == "phone":
        ddd = 11 + (n * 7) % 89
        prefix = "9" if (n // 5) % 2 == 0 else "3"
        suffix = f"{(n * 7919 + 1234567) % (10**8):08d}" if prefix == "9" else f"{(n * 7919 + 1234567) % (10**7):07d}"
        digits = f"{ddd}{prefix}{suffix}"
        form = (n // 5) % 4
        if form == 0:
            raw = f"+55 ({ddd}) {prefix}{suffix[:4]}-{suffix[4:]}"
        elif form == 1:
            raw = f"{ddd} {prefix}{suffix}"
        elif form == 2:
            raw = f"55{digits}"
        else:
            raw = f"({ddd}) {prefix}{suffix}"
        payload = {"raw": raw}
    elif kind == "retry":
        payload = {"attempt": 1 + (n * 3) % 14, "base_seconds": 2 + n % 13, "cap_seconds": 30 + (n % 9) * 90}
    elif kind == "sla":
        limit = 30 + n * 3
        payload = {
            "elapsed_minutes": (n * 17) % (limit + 120),
            "limit_minutes": limit,
            "warning_minutes": 10 + (n % 6) * 10,
        }
    elif kind == "message":
        payload = {"minutes_since_contact": (n * 71) % 3400, "window_minutes": 60 + (n % 25) * 60}
    else:
        payload = {
            "name": bool(n & 1),
            "phone": bool(n & 2),
            "email": bool(n & 4),
            "source": bool(n & 8),
            "engagement_points": n // 5,
        }
    return {
        "id": f"SC-{n:04d}",
        "category": kind,
        "description": DESCRIPTIONS[kind],
        "input": payload,
        "expected": evaluate(kind, payload),
        "origin": "synthetic-generated",
    }

def generate(count: int, folder: Path) -> list[Path]:
    if not 1 <= count <= 10000:
        raise ValueError("Contagem fora de 1..10000")
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for n in range(1, count + 1):
        obj = build_case(n)
        path = folder / f"{obj['id']}.json"
        content = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") != content:
            raise ValueError(f"Cenário já existe e difere: {path}")
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--count", type=int, default=412)
    ap.add_argument("--root", type=Path, default=ROOT / "scenarios")
    args = ap.parse_args()
    paths = generate(args.count, args.root)
    print(f"{len(paths)} cenários independentes disponíveis em {args.root}")

if __name__ == "__main__":
    main()
