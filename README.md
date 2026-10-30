# Aprendendo RuFaS com Jupyter Notebook

Trabalho de otimização em um ambiente reproduzível para configurar, executar e comparar simulações reais do **RuFaS** sem precisar usar comandos no terminal durante o estudo.

O projeto contém três etapas reproduzíveis: aprendizado do fluxo do RuFaS, otimização nutricional de uma dieta de menor custo e análise de sensibilidade interativa. Ainda não há API ou interface web.

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

### Acesso ao JupyterLab

Depois que os contêineres iniciarem, abra no navegador:

- [http://localhost:8888/lab/tree/notebooks](http://localhost:8888/lab/tree/notebooks)

Na tela de autenticação, informe o token padrão:

```text
rufas
```

O JupyterLab usa um **token**, e não uma senha de usuário. Também é possível acessar diretamente com o token na URL:

- [http://localhost:8888/lab/tree/notebooks?token=rufas](http://localhost:8888/lab/tree/notebooks?token=rufas)

Para alterar o token ou a porta, copie `.env.example` para `.env` e edite:

```dotenv
JUPYTER_PORT=8888
JUPYTER_TOKEN=rufas
```

Se a porta for alterada, substitua `8888` na URL pelo valor configurado em `JUPYTER_PORT`.

### Notebooks disponíveis

- `01_primeira_simulacao.ipynb`: configuração, simulação e comparação manual;
- `02_otimizacao_dieta.ipynb`: compara nosso modelo linear de cinco pisos com o formulador NASEM do RuFaS e exporta a linha de base.
- `03_analise_sensibilidade.ipynb`: recebe a dieta do Notebook 2 e oferece barras de quantidade e preço para cada ingrediente antes de simular o ajuste na mesma fazenda.

No notebook, execute as células na ordem. Tamanho do rebanho, lactação, dieta, preços e demais valores ficam visíveis e editáveis diretamente nas células. A execução valida essas entradas, gera automaticamente os arquivos físicos exigidos pelo RuFaS, acompanha o estado e carrega o resultado sem exigir outro comando.

Os Notebooks 1 e 2 são independentes em execução. O Notebook 3 possui dependência explícita do Notebook 2: a Etapa 2 grava `notebook2_custom_baseline.json` no volume compartilhado, contendo fazenda, semente, restrições, preços, dieta ótima e identificador da simulação-base. Portanto, execute o Notebook 2 por completo antes da Etapa 3.

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

Essa função objetivo busca **somente a dieta de menor custo**; ela não maximiza diretamente a produção de leite. Nosso otimizador aplica os cinco pisos de energia (TDN), proteína bruta, cálcio, fósforo e fibra (NDF), derivados da dieta de referência calculada pelo RuFaS.

Separadamente, o RuFaS usa SLSQP e seu conjunto mais amplo de condições NASEM. Depois das duas otimizações, o notebook simula as dietas sob as mesmas condições e compara composição, custo, produção de leite, receita e margem. Assim, produção, receita e margem são resultados posteriores da avaliação, e não componentes da função objetivo do nosso modelo atual.

## Etapa 3 — análise de sensibilidade

O terceiro notebook realiza uma análise interativa do tipo *what-if*. Para cada ingrediente existem duas barras: quantidade em kg de matéria seca por vaca/dia e preço em USD/kg de matéria seca. A linha de base vem diretamente do Notebook 2; depois dos ajustes, as quantidades são convertidas em percentuais e formam uma dieta fixa para avaliação. O botão **Salvar ajustes** grava os controles em `notebook3_manual_adjustments.json`, impedindo que sejam perdidos quando uma célula é executada novamente ou o kernel é reiniciado.

A dieta ajustada é aplicada ao RuFaS com a mesma configuração de fazenda e a mesma semente. O notebook confirma a reprodução da população, verifica as cinco restrições nas quantidades planejadas e na ração média efetivamente consumida, e compara leite, custo planejado, custo realizado, receita, margem e composição com o resultado original do nosso otimizador.

## Estrutura da implementação

Os módulos reutilizáveis ficam em `src/rufas_project/`, o worker fica em `worker/` e o snapshot de preços fica em `configs/`.

As decisões, limites e evolução proposta estão em [Docs/arquitetura-notebook-rufas.md](Docs/arquitetura-notebook-rufas.md).
