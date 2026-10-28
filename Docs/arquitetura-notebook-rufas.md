# Arquitetura da etapa de aprendizado do RuFaS

## Objetivo

Permitir que uma pessoa ainda aprendendo RuFaS configure uma fazenda leiteira, execute o simulador e compare cenários dentro de um notebook reproduzível. A implementação atual evita antecipar a API e a interface web previstas para etapas posteriores.

## O que está confirmado

Pela instalação do RuFaS e pelo material de aula disponível no projeto:

- o RuFaS é executado por `main.py` a partir de arquivos de metadados e configurações;
- a configuração de animais aceita tamanho do rebanho, raça, composição do leite, peso maduro, fração em lactação e distribuição de paridades;
- a alimentação pode usar uma ração fornecida pelo usuário ou o formulador interno;
- o formulador interno busca uma dieta de menor custo usando SLSQP e restrições nutricionais do modelo;
- os exemplos oficiais fornecem uma configuração `animals_only`, alimentação do Meio-Oeste e composição NASEM;
- os resultados filtrados podem ser exportados em CSV.

## Decisões desta etapa

### Separação de responsabilidades

O notebook trata somente de configuração, submissão, acompanhamento e análise. O worker conhece a instalação do RuFaS e executa a simulação. Os módulos em `src/rufas_project` concentram validação, tradução das entradas, leitura dos resultados, economia e comparação.

### Comunicação por arquivos

Uma solicitação é um diretório `jobs/<uuid>` contendo:

```text
request.json          configuração pedida pelo notebook
status.json           queued, running, succeeded ou failed
input/                entradas resolvidas do RuFaS
output/               saídas originais do RuFaS
run.log               saída da execução
result.json           resultado simplificado para análise
resolved_config.json  configuração efetivamente usada
feed_prices.json      preços usados no cálculo econômico
```

As escritas iniciais são atômicas. O worker processa uma execução por vez, o que é adequado para aprendizado e evita concorrência acidental sobre o simulador.

### Cenário de referência

O primeiro teste usa 20 vacas, 80% em lactação, raça Holandesa, 30 dias e a ração para vacas em lactação do exemplo oficial. Os preços de alimentos também partem desse exemplo. Esses números tornam o teste reproduzível, mas não representam necessariamente uma propriedade real.

### Cenário alternativo

O segundo cenário desloca dois pontos percentuais de silagem de milho para milho em grão. A intenção é aprender comparação, e não afirmar que a alteração melhora nutrição, produção ou custo. Uma otimização científica posterior precisará declarar variáveis, limites, função objetivo, restrições e método de validação.

## Limites conhecidos

- A execução usa `animals_only`; solo, lavoura, esterco e emissões não fazem parte do primeiro teste.
- A análise econômica considera receita do leite e alimentação das vacas em lactação. Não é lucro líquido da fazenda.
- Moeda e unidade são apresentadas como USD por kg. O preço do leite é uma hipótese didática sem fonte de mercado.
- O notebook expõe apenas um subconjunto seguro dos muitos parâmetros do RuFaS.
- O resultado depende da versão fixada pelo submódulo RuFaS e da semente aleatória informada.

## Informações que faltam para o trabalho definitivo

Antes de modelar a otimização, ainda será necessário definir:

- região e sistema produtivo da fazenda;
- horizonte de simulação e período de aquecimento, se houver;
- número real de animais e distribuição por categoria;
- disponibilidade, composição e limites de inclusão dos alimentos;
- preços, moeda, datas e fontes verificáveis;
- objetivo da otimização e restrições nutricionais/econômicas;
- cenários, repetições, sementes e métricas de comparação;
- critério de sucesso e estratégia de validação.

## Evolução planejada

A Etapa 2 foi implementada no notebook `02_otimizacao_dieta.ipynb`, usando o formulador interno SLSQP do RuFaS para minimizar o custo da dieta sob restrições NASEM. A Etapa 3 foi implementada no notebook `03_analise_sensibilidade.ipynb`: ela varia individualmente os preços dos ingredientes em ±20%, executa 15 otimizações pela fila e classifica os ingredientes por influência sobre composição, custo e margem. Depois, os mesmos módulos poderão ser chamados por uma API e por uma interface web, sem duplicar as regras científicas.
