# Verificação operacional — monitor de publicações GitHub

Data: 2026-10-29
Repositório: MaxKsp/dev-activity-journal
Branch autorizada: main

## Objetivo

Documentar uma verificação reprodutível do publicador local: criar uma entrega
substantiva, aguardar a detecção da alteração e confirmar que a publicação
aparece no remoto sem duplicação no próximo ciclo.

## Critérios de aceite

1. O monitor só considera arquivos de texto alterados dentro de
   `publication_queue/`. Arquivos já publicados sem mudanças devem ser ignorados.
2. A suíte de testes Python precisa terminar sem falhas antes do commit.
3. O commit deve conter apenas o arquivo liberado e usar a identidade local
   associada ao proprietário do repositório.
4. O envio ocorre em `origin/main` sem `--force`.
5. O mesmo arquivo não produz um segundo commit enquanto não for modificado.
6. A consulta de contribuições pode não incluir atividade privada, mesmo que
   o usuário autenticado veja essa atividade no perfil.

## Comandos independentes de validação

- `git status --short`: verificar a árvore de trabalho.
- `py -3 -m unittest discover -s tests -q`: executar os testes.
- `git log -1 --oneline`: identificar a última alteração local.
- `git ls-remote origin refs/heads/main`: comparar o HEAD remoto.
- `gh run list --workflow daily.yml --limit 3`: verificar automação do GitHub Actions.

## Observações

A rotina publica **entregas novas**, não cria conteúdo automaticamente a cada
dez segundos. A frequência de verificação não equivale à frequência de commits.
O contador estimado não substitui o gráfico do GitHub autenticado. O limite
de 435 é um teto operacional, não garantia de contribuições creditadas.
