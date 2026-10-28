# Aprendendo RuFaS com Jupyter Notebook

Primeira etapa do trabalho de otimização: um ambiente reproduzível para configurar, executar e comparar simulações reais do **RuFaS** sem precisar usar comandos no terminal durante o estudo.

O projeto contém duas etapas reproduzíveis: aprendizado do fluxo do RuFaS e otimização nutricional de uma dieta de menor custo. Ainda não há API ou interface web.

## Arquitetura

```text
Notebook Jupyter
    │ grava solicitação e acompanha estado
    ▼
volume Docker compartilhado
    │ fila de arquivos JSON
    ▼
worker RuFaS ──► main.py ──► CSV do RuFaS
    │
    └──► resultado processado + cálculo econômico identificado separadamente
```

Há dois contêineres:

- `notebook`: ambiente didático com JupyterLab, pandas e gráficos;
- `rufas-worker`: instalação isolada do RuFaS que recebe uma solicitação, prepara os arquivos oficiais de entrada e executa `main.py`.

Os contêineres trocam apenas arquivos em um volume nomeado. O notebook não recebe acesso ao socket do Docker.

## Pré-requisitos

- Docker com Compose;
- porta local `8888` livre;
- o diretório `RuFaS/` presente. Como ele é um submódulo, use `git clone --recurse-submodules ...` ou `git submodule update --init --recursive`.

## Início rápido

Opcionalmente, copie as variáveis de exemplo:

```bash
cp .env.example .env
```

Suba o ambiente:

```bash
docker compose up --build
```

Abra <http://localhost:8888/lab/tree/notebooks> e informe o token `rufas`, salvo se ele tiver sido alterado em `.env`.

- `01_primeira_simulacao.ipynb`: configuração, simulação e comparação manual;
- `02_otimizacao_dieta.ipynb`: formulação de menor custo com variáveis de decisão e restrições NASEM.
- `03_analise_sensibilidade.ipynb`: variações sistemáticas de preços e análise da robustez da dieta otimizada.

No notebook, execute as células na ordem. Tamanho do rebanho, lactação, dieta, preços e demais valores ficam visíveis e editáveis diretamente nas células. A execução valida essas entradas, gera automaticamente os arquivos físicos exigidos pelo RuFaS, acompanha o estado e carrega o resultado sem exigir outro comando.

Para encerrar:

```bash
docker compose down
```

O histórico permanece no volume `rufas-notebook-data`. Para removê-lo intencionalmente, use `docker compose down -v`.

## O que o notebook ensina

O roteiro cobre, em células separadas:

1. preparação do ambiente;
2. configuração da fazenda e do período;
3. tamanho do rebanho, fração em lactação e paridades;
4. dieta e custo dos ingredientes;
5. premissas econômicas;
6. validação antes da execução;
7. envio e monitoramento da simulação;
8. leitura das séries produzidas pelo RuFaS;
9. visualização de leite e população;
10. receita, custo da alimentação e margem;
11. comparação de um cenário de referência com uma variação didática.

O preço do leite de `0,45 USD/kg` é apenas uma hipótese didática. Deve ser substituído por uma fonte, região, moeda e data definidas no trabalho.

## Origem dos valores

- Arquivos de animal, alimentação, metadados e composição partem dos exemplos oficiais no submódulo `RuFaS`.
- Produção de leite, população e consumo vêm do CSV gerado pelo RuFaS.
- Receita, custo alimentar e margem são calculados neste projeto e aparecem com a origem `Calculado pelo projeto, não pelo RuFaS`.
- A alternativa incluída é uma comparação didática; ela não deve ser apresentada como dieta ótima.

## Modos de dieta

- `fixed`: usa as proporções informadas no cenário e reproduz o primeiro teste de forma controlada.
- `rufas_min_cost`: deixa `ration.user_input` desativado para usar o formulador interno de menor custo do RuFaS. O projeto preserva os preços de todos os ingredientes disponíveis para calcular o custo do resultado.

## Etapa 2 — otimização

O segundo notebook define formalmente:

```text
minimizar C(x) = soma(preço do ingrediente × kg de matéria seca por vaca/dia)
```

O RuFaS usa SLSQP e restrições NASEM de energia, proteína, minerais, fibra, gordura e consumo. O notebook executa a dieta fixa e a otimizada sob as mesmas condições e compara composição, custo, produção de leite, receita e margem sobre alimentação.

## Etapa 3 — análise de sensibilidade

O terceiro notebook aplica uma análise um fator por vez. O preço de cada ingrediente é variado em `-20%` e `+20%`, enquanto os demais valores permanecem constantes. A fila executa 15 otimizações: uma base e duas variações para cada um dos sete ingredientes. Os resultados mostram alterações de composição, custo, leite e margem, além de um ranking dos ingredientes mais influentes.

## Desenvolvimento e testes

Os módulos reutilizáveis ficam em `src/rufas_project/`; o worker fica em `worker/`; os cenários ficam em `configs/`.

```bash
python -m pytest
```

As decisões, limites e evolução proposta estão em [Docs/arquitetura-notebook-rufas.md](Docs/arquitetura-notebook-rufas.md).
