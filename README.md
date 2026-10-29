# Dev Activity Journal

Repositório privado para organizar trabalho de desenvolvimento e exercícios de programação, com GitHub Actions e Python padrão (sem dependências).

## Funcionamento

- Registro manual de trabalho real: detalha uma atividade concluída em projeto.
- Resumo verificável: gera relatório somente com os registros inseridos.
- Prática diária: cria automaticamente um exercício com critérios de aceite para posterior implementação.
- Automação: GitHub Actions executa às 09:17, horário de Brasília (12:17 UTC), e sob demanda. Executa testes e só faz commit se houver alterações.

A geração de um exercício não significa que ele foi resolvido. Commits da automação são identificados como tal. A ferramenta não fabrica 434 commits nem altera datas.

## Comandos

Requer Python 3.10 ou superior.

    python -m unittest discover -s tests -v
    python journal.py daily-prompt --date 2026-10-29
    python journal.py add --project "Orbita" --summary "Corrigidos testes de deduplicação" --detail "Testes executados localmente."
    python journal.py report

Ao registrar trabalho, faça também um commit com o código ou evidência correspondente. O diário não substitui o desenvolvimento real.

## Contribuições privadas no perfil

O GitHub exige, entre outros critérios, e-mail de autoria associado à conta, branch padrão de repositório independente e configuração de visibilidade das contribuições privadas. Pode levar até 24 horas para refletir as contribuições elegíveis. A atribuição de commits automáticos está sujeita às regras da plataforma.

No seu perfil, use: Contribution settings > Private contributions.

## Segurança

- Nenhuma credencial é persistida no repositório.
- O fluxo usa o token temporário padrão do GitHub Actions, limitado à escrita de conteúdo neste repositório.
- Não acessa outros repositórios privados nem executa instaladores de terceiros.

## Conjunto de cenários de CRM e suporte (29/10/2026)

O repositório inclui casos sintéticos reproduzíveis para testar:
normalização de telefones, políticas de retry/backoff, prazo SLA,
janela de mensagens e pontuação de leads.

O gerador produz arquivos `scenarios/SC-*.json` localmente, sob demanda.
`tests/test_scenarios.py` gera 412 casos temporários para verificar dados, unicidade,
resultados e reprodutibilidade, sem versionar dados sintéticos em massa.
**São cenários de teste gerados, não trabalho manual já executado nem contatos reais.**

Para regerar e validar a amostra:

    py -3 generate_scenarios.py --count 412
    py -3 -m unittest discover -s tests -v

O GitHub pode aplicar regras de atribuição, indexação e visibilidade;
a quantidade de commits não garante um número idêntico no gráfico.

## Monitor local de publicações (meta 435, 29/10/2026)

O script `scripts/publish_watcher.py` verifica a cada 10 segundos
a meta diária no GitHub. Ele não cria commits vazios ou conteúdo fictício.
Publica, no máximo, um arquivo novo ou alterado de `publication_queue/`
por ciclo. Somente arquivos de texto válidos, com conteúdo substantivo,
entram na fila. Os 412 cenários já gerados estão fora dessa fila.

A rotina interrompe automaticamente quando:
- a API confirma 435 contribuições no dia;
- o calendário brasileiro passa para 30 de outubro;
- a quantidade de publicações locais atinge o limite conservador,
  considerando a primeira contagem válida.

Como o perfil está privado, a API de contribuições da sessão CLI pode retornar zero.
A rotina usa a referência **24 contribuições**, confirmada no perfil autenticado
em 29/10/2026, e conta commits novos a partir de `bab8943`. O valor calculado
é uma **estimativa**, não uma confirmação em tempo real do gráfico. O limite
local interrompe envios para não ultrapassar o orçamento atribuído ao monitor.
Arquivos já versionados e sem alterações não são republicados.

Acompanhamento sem publicações:

    py -3 scripts/publish_watcher.py --once

Execução local contínua (até o fim do dia):

    py -3 scripts/publish_watcher.py --date 2026-10-29 --interval 10 --target 435 --publish

É necessário manter o computador ligado e a sessão autenticada no GitHub.
Não existe garantia de contabilização de um commit em 10 segundos no gráfico.
