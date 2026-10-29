# Diagnóstico de contribuições privadas no GitHub — 29/10/2026

## Ambiente validado

- Conta autenticada no navegador e no GitHub CLI: `MaxKsp`.
- Repositório de diário independente e privado: `MaxKsp/dev-activity-journal`.
- A branch padrão é `main`.
- Os novos commits possuem autoria reconhecida como `MaxKsp`.

## Causa da divergência

O perfil do GitHub está marcado como privado. Na página autenticada foi verificado:
2.083 contribuições no último ano e 24 em 29 de outubro. A consulta GraphQL feita
pelo monitor via GitHub CLI retornou zero. Portanto, esse zero não representa
a atividade vista pelo proprietário do perfil.

## Alteração de engenharia

O monitor agora separa contagem **confirmada** (quando fornecida pela API) de
**estimativa** baseada no último valor observado na página autenticada, somado
aos commits novos no repositório desde o marco conhecido.

- Evita reenviar um arquivo sem mudanças.
- Somente publica mudanças da pasta `publication_queue/`.
- Limita a uma publicação por ciclo e não força push.
- Interrompe ao encerrar o dia ou alcançar o limite estimado.
- A verificação ocorre a cada 10 segundos no processo local, não no GitHub Actions.

## Limitação

O gráfico do GitHub pode demorar para atualizar, e mudanças feitas em outros
repositórios podem alterar a contagem real enquanto a rotina roda. A referência
inicial não substitui a leitura autenticada atualizada do perfil.

Referência: https://docs.github.com/en/account-and-profile/how-tos/contribution-settings/troubleshooting-missing-contributions
