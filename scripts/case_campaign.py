"""Campanha de verificações CRM com casos sintéticos, 1 mudança testada por ciclo.

Cada caso inclui entrada e saída esperada. Sem commits vazios ou datas retroativas.
Contagem do gráfico é estimada: atividade de outras fontes não é monitorada.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from generate_scenarios import build_case  # noqa: E402
from scenario_rules import evaluate  # noqa: E402
from scripts.publish_watcher import call, publish_one, verify_repository  # noqa: E402

QUEUE = ROOT / "publication_queue"
STATE_DIR = ROOT / ".monitor"
ANCHOR = "8bf23f6"
BASELINE = 30
TARGET = 435
DAY = date(2026, 10, 29)
MAX_CASE = 412


def tracked(path: Path) -> bool:
    return bool(call(["git", "ls-files", "--", path.relative_to(ROOT).as_posix()]))


def estimated_total(anchor: str = ANCHOR, baseline: int = BASELINE) -> int:
    # A contagem do GitHub pode incluir outros repositórios, portanto é um teto local.
    return baseline + int(call(["git", "rev-list", "--count", f"{anchor}..HEAD"]))


def pending_or_next_case() -> Path | None:
    QUEUE.mkdir(exist_ok=True)
    for n in range(1, MAX_CASE + 1):
        path = QUEUE / f"SC-{n:04d}.json"
        if tracked(path):
            continue
        if not path.exists():
            obj = build_case(n)
            if evaluate(obj["category"], obj["input"]) != obj["expected"]:
                raise RuntimeError("Caso gerado não passou pela validação")
            path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
        return path
    return None


def synced_with_remote() -> bool:
    local = call(["git", "rev-parse", "HEAD"])
    remote_ref = call(["git", "ls-remote", "origin", "refs/heads/main"])
    remote = remote_ref.split()[0] if remote_ref else ""
    if remote == local:
        return True
    # Somente fast-forward. Não criar novas alterações até sincronizar o remoto.
    ancestor = call(["git", "merge-base", local, remote]) if remote else ""
    if ancestor != remote:
        raise RuntimeError("Branch divergente: intervenção manual necessária")
    call(["git", "push", "origin", "main"], timeout=60)
    return call(["git", "rev-parse", "HEAD"]) == call(["git", "ls-remote", "origin", "refs/heads/main"]).split()[0]


def check_date(day: date) -> bool:
    # GitHub mostra as contribuições pela data UTC, não pelo fuso de Brasília.
    return datetime.now(timezone.utc).date() == day


def cycle(target: int, baseline: int, anchor: str, day: date) -> str:
    if not check_date(day):
        return "STOP_DATA_UTC"
    verify_repository()
    if not synced_with_remote():
        return "WAIT_SYNC"
    total = estimated_total(anchor, baseline)
    if total >= target:
        return f"STOP_LIMITE_LOCAL {total}/{target}"
    path = pending_or_next_case()
    if path is None:
        return "STOP_CASOS_ESGOTADOS"
    result = publish_one(path)
    return f"{result} ESTIMATIVA {estimated_total(anchor, baseline)}/{target}"


def run(*, once: bool, interval: int, target: int, baseline: int, anchor: str, day: date) -> None:
    if not 10 <= interval <= 3600:
        raise ValueError("Intervalo precisa ser 10..3600 segundos")
    if not 0 < baseline < target or target - baseline > MAX_CASE + 20:
        raise ValueError("Limite não compatível com o conjunto de casos")
    if not call(["git", "cat-file", "-t", anchor]) == "commit":
        raise RuntimeError("Commit-base não encontrado")
    STATE_DIR.mkdir(exist_ok=True)
    failures = 0
    while True:
        started = time.monotonic()
        try:
            message = cycle(target, baseline, anchor, day)
            failures = 0
        except Exception as exc:
            failures += 1
            message = f"ERRO_{failures}: {type(exc).__name__}: {exc}"
        log = f"{datetime.now(timezone.utc).isoformat()} {message}"
        print(log, flush=True)
        with (STATE_DIR / "case_campaign.log").open("a", encoding="utf-8") as stream:
            stream.write(log + "\n")
        if message.startswith("STOP_") or once or failures >= 5:
            return
        duration = time.monotonic() - started
        time.sleep(max(1, interval - duration) if failures == 0 else 60)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--interval", type=int, default=10)
    ap.add_argument("--target", type=int, default=TARGET)
    ap.add_argument("--baseline", type=int, default=BASELINE)
    ap.add_argument("--anchor", default=ANCHOR)
    ap.add_argument("--date-utc", type=date.fromisoformat, default=DAY)
    args = ap.parse_args()
    run(once=args.once, interval=args.interval, target=args.target,
        baseline=args.baseline, anchor=args.anchor, day=args.date_utc)


if __name__ == "__main__":
    main()
