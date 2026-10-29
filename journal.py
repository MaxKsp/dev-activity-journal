"""Diário de desenvolvimento local: atividades verificáveis e exercícios diários."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOPICS = [
    ("Normalizador de telefones", "Implemente uma função que normalize telefones brasileiros sem perder o DDD.", "Entradas inválidas devem produzir um erro documentado."),
    ("Deduplicação de leads", "Implemente deduplicação determinística por telefone normalizado e origem.", "Preserve a ordem da primeira ocorrência."),
    ("Limitação de requisições", "Implemente um rate limiter de janela deslizante sem dependências.", "Trate os limites exatos da janela."),
    ("Busca com paginação", "Implemente paginação por cursor para uma coleção ordenada.", "Não repita nem perca itens entre páginas."),
    ("Filtragem de tarefas", "Implemente busca combinada por status, prioridade e texto.", "Filtros vazios não devem remover itens."),
    ("Validador de configuração", "Implemente validação de campos obrigatórios e tipos de um arquivo JSON.", "Retorne mensagens de erro específicas."),
    ("Cache com TTL", "Implemente cache local com expiração e invalidação explícita.", "Controle o relógio nos testes."),
    ("Agregador de métricas", "Implemente soma e média por dia para eventos com carimbo de data.", "Considere períodos sem eventos."),
    ("Parser CSV", "Implemente importação CSV tolerante a colunas extras.", "Reporte linhas inválidas sem perder as válidas."),
    ("Fila de tentativas", "Implemente uma fila com política de retry e backoff.", "Garanta limite máximo de tentativas."),
    ("Comparador de versões", "Implemente comparação de versões semânticas major.minor.patch.", "Trate entradas malformadas."),
    ("Verificador de permissões", "Implemente uma matriz de permissões por papel e recurso.", "Negue acesso por padrão."),
]


def add_entry(root: Path, project: str, summary: str, detail: str = "") -> None:
    if len(project.strip()) < 2 or len(summary.strip()) < 8:
        raise ValueError("Projeto e resumo descritivo são obrigatórios (resumo >= 8 caracteres).")
    filename = root / "data" / "entries.jsonl"
    filename.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "project": project.strip(),
        "summary": summary.strip(),
        "detail": detail.strip(),
    }
    with filename.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def daily_prompt(root: Path, day: date) -> bool:
    filename = root / "challenges" / f"{day.isoformat()}.md"
    if filename.exists():
        return False
    topic, instruction, assertion = TOPICS[day.toordinal() % len(TOPICS)]
    level = ("básico", "intermediário", "avançado")[(day.toordinal() // len(TOPICS)) % 3]
    filename.parent.mkdir(parents=True, exist_ok=True)
    filename.write_text(
        f"# Desafio de programação — {day.isoformat()}\n\n"
        f"**Tema:** {topic}\n\n**Nível:** {level}\n\n"
        f"## Objetivo\n\n{instruction}\n\n"
        f"## Critério mínimo de aceite\n\n{assertion}\n\n"
        "## Entrega\n\n"
        "1. Implementação em código-fonte próprio.\n"
        "2. Pelo menos três testes: caminho feliz, limite e erro.\n"
        "3. Registro do resultado real no diário, pelo comando journal.py add.\n\n"
        "> Este exercício foi gerado automaticamente; não é evidência de implementação.\n",
        encoding="utf-8",
    )
    return True


def report(root: Path) -> bool:
    source = root / "data" / "entries.jsonl"
    rows = []
    if source.exists():
        for line in source.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    totals = Counter(x["project"] for x in rows)
    lines = [
        "# Relatório de atividades registradas",
        "",
        f"**Registros de trabalho:** {len(rows)}",
        "",
        "Este relatório contabiliza somente atividades inseridas explicitamente.",
        "Exercícios gerados automaticamente não são contabilizados como trabalho concluído.",
        "",
        "## Por projeto",
        "",
    ]
    lines += [f"- {project}: {count}" for project, count in sorted(totals.items())] or ["Nenhum registro ainda."]
    lines += ["", "## Últimos registros", ""]
    lines += [
        f"- {row['date'][:10]} — **{row['project']}**: {row['summary']}"
        for row in rows[-20:][::-1]
    ] or ["Nenhum registro ainda."]
    content = "\n".join(lines) + "\n"
    filename = root / "reports" / "summary.md"
    filename.parent.mkdir(parents=True, exist_ok=True)
    if filename.exists() and filename.read_text(encoding="utf-8") == content:
        return False
    filename.write_text(content, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    subs = parser.add_subparsers(dest="command", required=True)
    add = subs.add_parser("add", help="Registrar trabalho executado")
    add.add_argument("--project", required=True)
    add.add_argument("--summary", required=True)
    add.add_argument("--detail", default="")
    daily = subs.add_parser("daily-prompt", help="Criar um desafio novo para a data")
    daily.add_argument("--date", default=date.today().isoformat())
    subs.add_parser("report", help="Recalcular relatório apenas quando houver mudanças")
    args = parser.parse_args()
    if args.command == "add":
        add_entry(args.root, args.project, args.summary, args.detail)
        report(args.root)
    elif args.command == "daily-prompt":
        print("criado" if daily_prompt(args.root, date.fromisoformat(args.date)) else "já existente")
    elif args.command == "report":
        print("atualizado" if report(args.root) else "sem alterações")


if __name__ == "__main__":
    main()
