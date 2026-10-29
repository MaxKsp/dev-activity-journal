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
