"""Observa novas entregas revisadas e publica uma por ciclo, até a meta diária."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "publication_queue"
BRAZIL = timezone(timedelta(hours=-3))
EXPECTED_REMOTE = "github.com/maxksp/dev-activity-journal"
ALLOWED = {".md", ".py", ".json", ".txt"}


def call(args: list[str], *, cwd: Path = ROOT, timeout: int = 25) -> str:
    result = subprocess.run(args, cwd=cwd, text=True, encoding="utf-8",
                            errors="replace", stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"{args[0]} falhou: {result.stderr.strip()[-500:]}")
    return result.stdout.strip()


def verify_repository() -> None:
    root = Path(call(["git", "rev-parse", "--show-toplevel"])).resolve()
    if root != ROOT.resolve():
        raise RuntimeError("Pasta Git incorreta")
    if call(["git", "branch", "--show-current"]) != "main":
        raise RuntimeError("Branch diferente de main")
    remote = call(["git", "remote", "get-url", "origin"]).lower()
    if EXPECTED_REMOTE not in remote:
        raise RuntimeError("Remote diferente do projeto autorizado")
    if call(["git", "config", "user.email"]).lower() != "maxkiller209@gmail.com":
        raise RuntimeError("E-mail do autor não confere")
    if call(["git", "diff", "--cached", "--name-only"]):
        raise RuntimeError("Há alterações já staged; revisão manual necessária")


def today_brazil() -> date:
    return datetime.now(BRAZIL).date()


def contribution_count(day: date) -> int:
    start = day.isoformat() + "T00:00:00-03:00"
    end = (day + timedelta(days=1)).isoformat() + "T00:00:00-03:00"
    query = (
        "query { viewer { login contributionsCollection("
        + f'from:"{start}",to:"{end}"'
        + ") { contributionCalendar { weeks { contributionDays { date contributionCount } } } } } }"
    )
    output = call(["gh", "api", "graphql", "-f", f"query={query}"])
    data = json.loads(output)["data"]["viewer"]
    if data["login"].lower() != "maxksp":
        raise RuntimeError("Conta GitHub autenticada não corresponde ao perfil")
    days = [
        x for w in data["contributionsCollection"]["contributionCalendar"]["weeks"]
        for x in w["contributionDays"] if x["date"] == day.isoformat()
    ]
    if len(days) != 1:
        raise RuntimeError("API não retornou a data esperada")
    return int(days[0]["contributionCount"])


def ready_files() -> list[Path]:
    if not QUEUE.exists():
        return []
    candidates = []
    for path in sorted(QUEUE.iterdir()):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in ALLOWED:
            continue
        if path.stat().st_size < 80 or path.stat().st_size > 100_000:
            continue
        if not path.read_text(encoding="utf-8").strip():
            continue
        relative = path.relative_to(ROOT).as_posix()
        if not call(["git", "status", "--porcelain", "--", relative]):
            continue
        candidates.append(path)
    return candidates


def publish_one(path: Path) -> str:
    verify_repository()
    # Não misturar alterações de outros projetos nem do dataset ainda não publicado.
    call([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"])
    relative = path.relative_to(ROOT).as_posix()
    if not relative.startswith("publication_queue/"):
        raise RuntimeError("Arquivo fora da fila autorizada")
    call(["git", "add", "--", relative])
    if not call(["git", "diff", "--cached", "--name-only"]):
        return "Arquivo sem alterações; nada publicado"
    call(["git", "commit", "-m", f"docs: publicar entrega revisada {path.stem[:65]}"])
    # Push não-forçado; na falha, registrar erro e interromper sem reescrever histórico.
    call(["git", "push", "origin", "main"], timeout=60)
    return f"Publicado: {relative}"


def run(target: int, interval: int, day: date, minimum: int, *, once: bool, publish: bool, anchor: str | None = None) -> None:
    if interval < 10:
        raise ValueError("Intervalo mínimo: 10 segundos")
    if not 1 <= minimum <= target:
        raise ValueError("Contagem mínima/objetivo inválidos")
    verify_repository()
    # A API pode ocultar contribuições de perfis privados; usar baseline da visão autenticada.
    published = int(call(["git", "rev-list", "--count", f"{anchor}..HEAD"])) if anchor else 0
    print(f"MONITOR {day.isoformat()} a cada {interval}s; baseline={minimum}; publicações após baseline={published}; alvo={target}; publica={publish}", flush=True)
    while True:
        if today_brazil() != day:
            print("ENCERRADO: data da meta terminou", flush=True)
            return
        try:
            count = contribution_count(day)
            # Acesso de CLI sem visibilidade do perfil privado retorna 0, apesar do gráfico autenticado.
            # Estimativa conservadora: baseline observado + commits locais desde o snapshot.
            estimate = max(count, minimum + published)
            if estimate >= target:
                label = "CONFIRMADO" if count >= target else "LIMITE LOCAL ATINGIDO (revalidar no navegador)"
                print(f"{label}: API={count}; estimativa={estimate}/{target}", flush=True)
                return
            files = ready_files()
            if not files:
                print(f"SEM NOVA ALTERAÇÃO: API={count}; estimativa={estimate}/{target}", flush=True)
            elif not publish:
                print(f"SIMULAÇÃO: {len(files)} mudanças; API={count}; estimativa={estimate}/{target}", flush=True)
            else:
                result = publish_one(files[0])
                print(result, flush=True)
                if result.startswith("Publicado:"):
                    published += 1
        except (RuntimeError, ValueError, KeyError, TypeError, json.JSONDecodeError,
                subprocess.TimeoutExpired) as exc:
            print(f"PAUSADO: leitura/publicação não verificada: {exc}", flush=True)
        if once:
            return
        time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=int, default=435)
    parser.add_argument("--interval", type=int, default=10)
    parser.add_argument("--date", type=date.fromisoformat, default=today_brazil())
    parser.add_argument("--minimum-visible", type=int, default=24)
    parser.add_argument("--anchor", default="bab8943", help="Commit de referência da contagem autenticada")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--publish", action="store_true", help="Publicar somente alterações aprovadas na fila")
    args = parser.parse_args()
    run(args.target, args.interval, args.date, args.minimum_visible,
        once=args.once, publish=args.publish, anchor=args.anchor)


if __name__ == "__main__":
    main()
