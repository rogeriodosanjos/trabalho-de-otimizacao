# Introdução ao RuFaS

Este documento apresenta o RuFaS de forma conceitual e mostra como preparar o ambiente e executar uma primeira simulação. O objetivo, neste momento, é somente entender o funcionamento básico da ferramenta e confirmar que ela está instalada corretamente.

> **Escopo deste guia:** conhecer a estrutura do RuFaS, executar o cenário de exemplo e localizar os resultados. Otimização e alterações no cenário serão tratadas posteriormente.

## 1. O que é o RuFaS?

RuFaS é a sigla de **Ruminant Farm Systems**. Trata-se de uma plataforma de código aberto, escrita em Python, para simular sistemas de produção de ruminantes. Atualmente, seu foco principal são fazendas de gado leiteiro.

O RuFaS é um **simulador de fazenda completa** (*whole-farm model*). Isso significa que ele procura representar, de forma integrada, os principais componentes de uma fazenda e a interação entre eles ao longo do tempo.

De maneira simplificada, seu funcionamento pode ser representado assim:

```text
Dados da fazenda
       ↓
Configuração do cenário
       ↓
Simulação diária dos processos
       ↓
Resultados produtivos, econômicos e ambientais
```

O RuFaS não é apenas uma calculadora que recebe alguns valores e devolve uma única resposta. Ele acompanha a evolução do sistema durante um período definido, normalmente dia a dia. Por isso, uma execução pode gerar muitas variáveis e uma grande quantidade de dados.

## 2. O que o RuFaS representa?

O modelo é dividido em módulos interligados. Cada módulo representa uma parte da fazenda.

### 2.1. Animais

O módulo animal representa o ciclo de vida e o manejo dos bovinos, incluindo:

- nascimento e desmame;
- crescimento das novilhas;
- reprodução e gestação;
- parto;
- lactação e produção de leite;
- período seco;
- descarte, venda e mortalidade;
- consumo de alimento;
- produção inicial de dejetos;
- emissões entéricas, como metano.

Os animais são organizados em grupos e instalações. O estado do rebanho muda ao longo da simulação.

### 2.2. Alimentação e armazenamento de alimentos

Esse módulo controla os alimentos disponíveis na fazenda, as compras, os estoques e as rações fornecidas aos diferentes grupos de animais.

O usuário pode fornecer uma dieta ou permitir que o RuFaS formule uma ração de menor custo, respeitando requisitos nutricionais. Entre os fatores considerados estão matéria seca, energia, proteína, fibra, gordura, cálcio e fósforo.

### 2.3. Manejo de dejetos

Depois que os dejetos são produzidos pelos animais, o módulo de manejo representa etapas como:

- remoção dos dejetos das instalações;
- adição de água e material de cama;
- separação entre sólidos e líquidos;
- digestão anaeróbia;
- armazenamento;
- aplicação no campo;
- perdas de nutrientes e emissões.

As instalações e os grupos de animais precisam estar associados a uma cadeia coerente de manejo de dejetos.

### 2.4. Solo e culturas

O módulo de solo e culturas representa o crescimento das plantas e as mudanças que acontecem no solo. Ele utiliza informações como clima, tipo de solo, plantio, colheita, preparo do solo e aplicação de fertilizante ou esterco.

Entre os processos simulados estão:

- disponibilidade e transformação de nitrogênio;
- ciclo do fósforo;
- ciclo do carbono;
- infiltração e movimento de água;
- escoamento superficial;
- erosão;
- crescimento e produtividade das culturas.

As culturas colhidas podem alimentar os estoques usados pelo rebanho, conectando esse módulo ao de alimentação.

### 2.5. Economia, energia e emissões

O RuFaS também reúne informações para estimar custos, consumo de energia e emissões relacionadas às atividades da fazenda. Isso permite observar o sistema por diferentes perspectivas, não apenas pela produção de leite.

## 3. Como os módulos se relacionam?

Uma das características mais importantes do RuFaS é a integração. Uma decisão tomada em um módulo pode produzir efeitos em vários outros.

Por exemplo:

```text
Dieta dos animais
   ├── afeta o custo da alimentação
   ├── afeta a produção de leite
   ├── afeta a quantidade e composição dos dejetos
   └── afeta as emissões dos animais e dos dejetos
```

Da mesma forma, uma cultura produzida na fazenda pode entrar no estoque de alimentos; os dejetos podem retornar aos campos como fertilizante; e o clima pode afetar simultaneamente a produção agrícola e o manejo do sistema.

Por causa dessas relações, é importante interpretar os resultados como partes de um sistema, e não como números completamente independentes.

## 4. Conceitos importantes

### Cenário

É uma representação de uma fazenda e de suas condições de simulação. Um cenário reúne informações sobre rebanho, instalações, alimentos, campos, clima, dejetos e período simulado.

### Entrada (*input*)

São os dados fornecidos ao modelo. No RuFaS, a maior parte das entradas está em arquivos JSON ou CSV dentro da pasta `input/`.

### Metadata

É o arquivo que informa ao RuFaS onde estão as entradas de um cenário e quais regras devem ser usadas para validá-las. Pode ser entendido como um “mapa de endereços” dos dados.

### Tarefa (*task*)

É a instrução que diz ao RuFaS o que executar. Uma tarefa informa, por exemplo, o tipo de execução, o cenário utilizado, a semente aleatória, o nome dos arquivos de saída e o nível de detalhamento dos registros.

### Semente aleatória (*random seed*)

É um número usado para tornar reproduzíveis os eventos aleatórios da simulação. Quando duas execuções usam os mesmos dados, a mesma versão do programa e a mesma semente, espera-se que apresentem os mesmos resultados.

### Filtro de saída

Define quais variáveis devem ser gravadas nos arquivos de resultado. Como o RuFaS calcula muitas variáveis, os filtros evitam que toda execução gere dados desnecessários.

### Log

É o registro da execução. Os logs apresentam mensagens informativas, avisos e erros e são essenciais para diagnosticar problemas.

## 5. Estrutura básica do projeto

Neste repositório, o código do simulador está na pasta `RuFaS/`. Os itens mais importantes para um primeiro contato são:

```text
RuFaS/
├── main.py                         # ponto de entrada do programa
├── pyproject.toml                  # versão do Python e dependências
├── RUFAS/                          # código-fonte do simulador
├── input/
│   ├── task_manager_metadata.json  # aponta para o arquivo de tarefas
│   ├── data/                       # dados dos cenários
│   └── metadata/                   # mapas dos arquivos de entrada
└── output/
    └── output_filters/             # filtros que selecionam as saídas
```

O fluxo do cenário padrão é:

```text
main.py
  ↓
input/task_manager_metadata.json
  ↓
input/data/tasks/example_freestall_task.json
  ↓
input/metadata/example_freestall_dairy_metadata.json
  ↓
arquivos de dados do cenário
  ↓
resultados em output/
```

O cenário padrão representa uma fazenda leiteira com alojamento do tipo **freestall**. Na versão atual deste repositório, ele executa uma simulação completa de 2013 a 2019 e utiliza o padrão nutricional NASEM.

## 6. Preparação para o primeiro teste

### 6.1. Abrir um terminal na pasta correta

Os comandos do RuFaS devem ser executados a partir da pasta que contém o arquivo `main.py`.

A partir da raiz deste trabalho, entre na pasta do programa:

```bash
cd RuFaS
```

Para conferir o local atual:

```bash
pwd
```

O caminho exibido deve terminar em `/Trabalho/RuFaS`.

### 6.2. Conferir a versão do Python

Esta versão do RuFaS aceita Python 3.12 ou 3.13.

```bash
python3 --version
```

O resultado deve ser semelhante a:

```text
Python 3.13.7
```

Se o computador possuir mais de uma versão, poderá ser necessário usar `python3.12` ou `python3.13` explicitamente nos comandos seguintes.

### 6.3. Criar um ambiente virtual

O ambiente virtual mantém as dependências do RuFaS separadas de outros projetos Python.

```bash
python3 -m venv venv
```

Ative o ambiente no macOS ou Linux:

```bash
source venv/bin/activate
```

No Windows PowerShell, o comando equivalente é:

```powershell
venv\Scripts\Activate.ps1
```

Quando o ambiente estiver ativo, o terminal normalmente mostrará `(venv)` antes do comando.

### 6.4. Instalar as dependências

Com o ambiente virtual ativo e ainda dentro da pasta `RuFaS`, execute:

```bash
python -m pip install --upgrade pip
python -m pip install .
```

O segundo comando lê o arquivo `pyproject.toml` e instala as bibliotecas necessárias. A instalação pode levar alguns minutos.

> Se aparecer `ModuleNotFoundError`, como `No module named 'numpy'`, normalmente as dependências ainda não foram instaladas ou o ambiente virtual não está ativo.

### 6.5. Confirmar que o programa inicia

Antes da simulação, peça apenas a ajuda da linha de comando:

```bash
python main.py --help
```

Se a instalação estiver correta, o RuFaS exibirá as opções disponíveis e encerrará sem executar uma simulação.

## 7. Primeiro teste: executar o cenário de exemplo

### 7.1. Habilitar uma saída CSV

O repositório inclui um filtro geral desabilitado, identificado pelo sublinhado inicial em `_csv_all_variables.txt`. Para preservar o arquivo original, faça uma cópia sem o sublinhado:

```bash
cp output/output_filters/_csv_all_variables.txt \
   output/output_filters/csv_all_variables.txt
```

Esse filtro solicita um conjunto amplo de variáveis. Ele é útil para conhecer o programa, mas pode gerar arquivos grandes. Em estudos posteriores, será melhor criar filtros contendo somente as variáveis necessárias.

No Windows PowerShell, use:

```powershell
Copy-Item output/output_filters/_csv_all_variables.txt `
          output/output_filters/csv_all_variables.txt
```

### 7.2. Executar a simulação

Execute o cenário padrão mostrando avisos no terminal:

```bash
python main.py -v warnings
```

Sem a opção `-p`, o RuFaS usa automaticamente:

```text
input/task_manager_metadata.json
```

Esse arquivo aponta para a tarefa `example_freestall_task.json`, que por sua vez aponta para o metadata do cenário *freestall*.

O mesmo teste pode ser executado de forma explícita com:

```bash
python main.py \
  -p input/task_manager_metadata.json \
  -v warnings
```

A duração depende do computador, pois o cenário padrão representa vários anos e integra todos os módulos da fazenda.

### 7.3. Como saber se funcionou

Durante a execução, o terminal deve mostrar informações da versão do RuFaS, o início da tarefa e eventuais avisos. Ao final, não deve existir uma mensagem de encerramento por erro inesperado.

Confira o conteúdo da pasta de saída:

```bash
find output -maxdepth 2 -type f
```

Também é possível examiná-la pelo explorador de arquivos do VS Code. Dependendo das configurações da tarefa e dos filtros habilitados, podem ser criados arquivos CSV, JSON, gráficos, relatórios e logs.

### 7.4. Verificar os logs

Se a execução falhar ou produzir avisos, consulte primeiro:

```text
output/logs/
```

Os três tipos de mensagem mais importantes são:

- **log:** informação sobre o andamento normal;
- **warning:** situação que merece atenção, mas que pode não impedir a execução;
- **error:** falha que pode invalidar uma etapa ou interromper a simulação.

Um aviso não significa automaticamente que todo o resultado está errado. Entretanto, ele deve ser entendido antes que os dados sejam utilizados em uma análise.

## 8. Opções úteis da linha de comando

Mostrar a ajuda:

```bash
python main.py --help
```

Mostrar apenas erros no terminal:

```bash
python main.py -v errors
```

Mostrar avisos e erros:

```bash
python main.py -v warnings
```

Executar sem gerar gráficos:

```bash
python main.py -g -v warnings
```

Escolher outro arquivo de tarefas:

```bash
python main.py -p caminho/para/o/metadata.json
```

Existe também a opção `-c`, que limpa o diretório de saída antes da execução. Ela não deve ser usada sem verificar quais resultados já estão nessa pasta:

```bash
python main.py -c
```

## 9. Problemas comuns

### `ModuleNotFoundError`

As dependências não foram instaladas ou o ambiente virtual não está ativo.

```bash
source venv/bin/activate
python -m pip install .
```

### `python: command not found`

Tente usar `python3` no lugar de `python`. Depois de ativar corretamente o ambiente virtual, normalmente `python` passa a apontar para a versão instalada nele.

### Arquivo de entrada não encontrado

Confirme que o comando está sendo executado dentro da pasta `RuFaS`. Os caminhos dos arquivos de entrada são relativos a essa pasta.

### Nenhum CSV foi produzido

Confira se existe um arquivo de filtro habilitado em `output/output_filters/`. Arquivos cujo nome começa com `_` ficam desabilitados.

### A execução está demorando

O cenário padrão simula uma fazenda completa durante vários anos. A demora, por si só, não representa uma falha. Observe as mensagens do terminal e os logs antes de interromper o processo.

### A simulação terminou com erro

Leia a última mensagem no terminal e consulte `output/logs/`. Verifique especialmente:

1. se o ambiente virtual está ativo;
2. se todas as dependências foram instaladas;
3. se o comando foi executado dentro de `RuFaS/`;
4. se algum arquivo foi renomeado ou alterado;
5. se os arquivos JSON continuam com sintaxe válida.

## 10. Checklist do primeiro teste

- [ ] Estou na pasta `RuFaS/`.
- [ ] Estou usando Python 3.12 ou 3.13.
- [ ] Criei e ativei o ambiente virtual.
- [ ] Executei `python -m pip install .`.
- [ ] `python main.py --help` funciona.
- [ ] Habilitei o filtro CSV de exemplo.
- [ ] Executei `python main.py -v warnings`.
- [ ] Encontrei os resultados em `output/`.
- [ ] Consultei os logs e identifiquei eventuais avisos ou erros.

## 11. O que observar neste primeiro contato

Neste estágio, não é necessário alterar parâmetros. O objetivo é conseguir responder às seguintes perguntas:

1. Qual arquivo inicia o RuFaS?
2. Qual arquivo informa a tarefa que será executada?
3. Qual metadata descreve o cenário usado?
4. Onde ficam os dados de entrada?
5. Onde ficam os resultados e os logs?
6. A simulação pode ser repetida com a mesma configuração?

Quando essas relações estiverem claras e o cenário padrão puder ser executado com sucesso, o próximo passo natural será criar uma cópia do cenário de exemplo e realizar uma alteração pequena e controlada, sem modificar os arquivos originais.

## 12. Referências dentro do repositório

- `RuFaS/README.md`: apresentação e instalação rápida.
- `RuFaS/docs/_src/_wiki/onboarding.rst`: introdução aos módulos e ao fluxo de uso.
- `RuFaS/docs/_src/_wiki/RuFaS-Command-Line-Arguments.rst`: opções da linha de comando.
- `RuFaS/docs/_src/_wiki/Task-Manager.rst`: funcionamento das tarefas.
- `RuFaS/docs/_src/_wiki/Input-Manager.rst`: carregamento e validação das entradas.
- `RuFaS/docs/_src/_wiki/Output-Manager.rst`: seleção e geração das saídas.

