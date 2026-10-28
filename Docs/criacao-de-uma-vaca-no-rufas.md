# Criação de uma população de vacas para lactação no RuFaS

Este guia mostra como configurar, gerar e testar uma população de vacas leiteiras no RuFaS. O objetivo é iniciar uma simulação com uma quantidade planejada de vacas em lactação, mantendo vacas secas e reposições suficientes para que o rebanho continue biologicamente coerente.

> **Escopo:** preparação da população animal. Este documento ainda não trata de otimização.

## 1. O que será criado?

No RuFaS, uma fazenda leiteira não deve ser formada apenas por vacas em lactação. O ciclo representado pelo modelo é:

```text
Bezerra → novilha → novilha gestante → primeiro parto
                                            ↓
Vaca seca ← fim da lactação ← vaca em lactação
    ↓
novo parto e nova lactação
```

A população precisa conter animais com diferentes idades, paridades, dias em lactação e estados reprodutivos. Isso evita que todas as vacas parem ou sequem ao mesmo tempo.

O exemplo deste guia terá inicialmente:

- 20 vacas no total;
- aproximadamente 16 vacas em lactação;
- aproximadamente 4 vacas secas;
- vacas distribuídas da primeira à quinta paridade;
- bezerras, novilhas e animais de reposição mantidos no cenário.

## 2. População-base e rebanho inicial

O RuFaS trabalha com dois conceitos diferentes.

### 2.1. População-base

É um arquivo contendo muitos animais biologicamente plausíveis:

```text
input/data/animal/animal_population.json
```

Sua estrutura contém grupos como:

```json
{
  "calves": [],
  "heiferIs": [],
  "heiferIIs": [],
  "heiferIIIs": [],
  "cows": [],
  "replacement": []
}
```

Esse arquivo funciona como um banco de animais disponíveis. Ele pode ser carregado do exemplo ou gerado novamente pelo RuFaS.

### 2.2. Rebanho inicial amostrado

Ao iniciar uma simulação, o `HerdFactory` seleciona animais da população-base conforme:

- total de vacas desejado;
- proporção de vacas em lactação;
- distribuição por paridade;
- quantidades de bezerras e novilhas;
- quantidade de reposições.

```text
População-base grande
          ↓ amostragem
Rebanho inicial do cenário
          ↓ simulação diária
Rebanho ao longo do tempo
```

O arquivo produzido por `HERD_INITIALIZATION` é uma população-base. A quantidade inicial de vacas em lactação é definida na configuração do cenário e obtida por amostragem dessa base.

## 3. Cálculo das vacas em lactação

Os parâmetros principais ficam no bloco `herd_information` de:

```text
input/data/animal/example_freestall_animal.json
```

Exemplo:

```json
{
  "cow_num": 20,
  "milking_cow_fraction": 0.80,
  "parity_fractions": {
    "1": 0.40,
    "2": 0.25,
    "3": 0.20,
    "4": 0.10,
    "5": 0.05
  }
}
```

Quantidade aproximada em lactação:

```text
cow_num × milking_cow_fraction
20 × 0,80 = 16 vacas em lactação
```

Quantidade aproximada de vacas secas:

```text
20 × (1 − 0,80) = 4 vacas secas
```

O RuFaS calcula e arredonda cada combinação de paridade e estado de lactação separadamente. Em rebanhos pequenos, o total real pode diferir em uma ou duas vacas do cálculo geral.

## 4. Distribuição por paridade

`parity_fractions` representa a distribuição conforme o número de partos:

| Chave | Interpretação                       | Exemplo |
| ----- | ------------------------------------- | ------: |
| `1` | Primeira lactação                   |     40% |
| `2` | Segunda lactação                    |     25% |
| `3` | Terceira lactação                   |     20% |
| `4` | Quarta lactação                     |     10% |
| `5` | Quinta lactação ou grupo mais velho |      5% |

As frações devem somar `1.0`:

```text
0,40 + 0,25 + 0,20 + 0,10 + 0,05 = 1,00
```

Animais de diferentes paridades apresentam diferenças de peso, produção, reprodução e risco de saída do rebanho. Por isso, não é adequado iniciar todas as vacas com a mesma paridade.

## 5. Configuração utilizada no tutorial

O bloco `herd_information` será:

```json
"herd_information": {
  "calf_num": 8,
  "heiferI_num": 44,
  "heiferII_num": 38,
  "heiferIII_num_springers": 5,
  "cow_num": 20,
  "replace_num": 500,
  "herd_num": 20,
  "herd_size_adjustment_period": 30,
  "herd_size_sell_threshold": 21,
  "herd_size_buy_threshold": 19,
  "breed": "HO",
  "parity_fractions": {
    "1": 0.40,
    "2": 0.25,
    "3": 0.20,
    "4": 0.10,
    "5": 0.05
  },
  "milking_cow_fraction": 0.80,
  "annual_milk_yield": null,
  "simulate_genetics": false
}
```

Campos importantes:

- `cow_num`: número inicial de vacas secas e em lactação;
- `herd_num`: número-alvo de vacas durante a simulação;
- `milking_cow_fraction`: proporção inicial em lactação;
- `herd_size_sell_threshold`: limite acima do qual pode ocorrer venda;
- `herd_size_buy_threshold`: limite abaixo do qual pode ocorrer compra;
- `replace_num`: animais disponíveis para reposição;
- `breed: HO`: raça Holandesa.

Os grupos jovens foram mantidos iguais aos do exemplo para não alterar simultaneamente muitas partes do sistema.

## 6. Limites mínimos

Na versão atual do RuFaS, as regras de validação exigem pelo menos:

- 6 vacas em `cow_num`;
- 6 vacas em `herd_num`;
- 2 animais em cada grupo de novilhas;
- 50 animais em `replace_num`.

Por isso, uma simulação com somente uma vaca não é aceita diretamente.

## 7. Preparar arquivos próprios

Execute os comandos a partir da pasta `RuFaS/`. Não altere os exemplos originais:

```bash
cp input/data/animal/example_freestall_animal.json \
   input/data/animal/lactacao_tutorial_animal.json

cp input/data/config/example_animals_only_config.json \
   input/data/config/lactacao_tutorial_config.json

cp input/metadata/example_animals_only_metadata.json \
   input/metadata/lactacao_tutorial_metadata.json

cp input/data/tasks/example_animals_only_task.json \
   input/data/tasks/lactacao_tutorial_task.json

cp input/task_manager_metadata.json \
   input/lactacao_tutorial_task_manager_metadata.json
```

Os cinco arquivos terão funções diferentes:

| Arquivo                                          | Função                              |
| ------------------------------------------------ | ------------------------------------- |
| `lactacao_tutorial_animal.json`                | Define tamanho e manejo do rebanho    |
| `lactacao_tutorial_config.json`                | Define período e tipo da simulação |
| `lactacao_tutorial_metadata.json`              | Aponta para os dados do cenário      |
| `lactacao_tutorial_task.json`                  | Define a execução                   |
| `lactacao_tutorial_task_manager_metadata.json` | Aponta para a tarefa                  |

### 7.1. Usar um período curto no primeiro teste

Abra `input/data/config/lactacao_tutorial_config.json` e use inicialmente:

```json
{
  "start_date": "2013:1",
  "end_date": "2013:30",
  "set_seed": true,
  "simulation_type": "animals_only",
  "nutrient_standard": "NASEM",
  "FIPS_county_code": 55025,
  "include_detailed_values": false
}
```

Trinta dias são suficientes para validar a população inicial e os arquivos de saída. Depois do primeiro teste, o período poderá ser ampliado.

## 8. Configurar o arquivo animal

Abra:

```text
input/data/animal/lactacao_tutorial_animal.json
```

Substitua somente o bloco `herd_information` pelos valores da seção 5. Não remova as demais partes, pois elas definem reprodução, peso, instalações, dietas e manejo de dejetos.

## 9. Verificar as instalações

Vacas em lactação são direcionadas ao grupo:

```json
"animal_combination": "LAC_COW"
```

Vacas secas e novilhas próximas do parto usam:

```json
"animal_combination": "CLOSE_UP"
```

No cenário *freestall* de exemplo, o curral `LAC_COW` possui 88 vagas e o `CLOSE_UP` possui 22. Isso é suficiente para as 20 vacas deste tutorial.

Para rebanhos maiores, confira:

```json
{
  "number_of_stalls": 88,
  "max_stocking_density": 1.2
}
```

Também devem existir dieta e fluxo de dejetos válidos para `LAC_COW` e `CLOSE_UP`. Por isso, o tutorial parte do cenário completo já fornecido.

## 10. Apontar o metadata para o arquivo animal

Abra:

```text
input/metadata/lactacao_tutorial_metadata.json
```

No bloco `animal`, altere somente `path`:

```json
"path": "input/data/animal/lactacao_tutorial_animal.json"
```

No bloco `config`, altere `path` para:

```json
"path": "input/data/config/lactacao_tutorial_config.json"
```

Inicialmente, mantenha o bloco `animal_population` apontando para:

```json
"path": "input/data/animal/animal_population.json"
```

Preserve `title`, `description`, `type` e `properties` nos dois blocos.

## 11. Configurar a tarefa

Substitua o conteúdo de:

```text
input/data/tasks/lactacao_tutorial_task.json
```

por:

```json
{
  "parallel_workers": 1,
  "tasks": [
    {
      "task_type": "SIMULATION_SINGLE_RUN",
      "metadata_file_path": "input/metadata/lactacao_tutorial_metadata.json",
      "output_prefix": "lactacao_tutorial",
      "log_verbosity": "warnings",
      "random_seeds": [42],
      "exclude_info_maps": false,
      "cross_validation_file_paths": [
        "input/metadata/cross_validation/animal_cross_validation.json",
        "input/metadata/cross_validation/weather_cross_validation.json"
      ]
    }
  ]
}
```

A semente `42` permite repetir a mesma amostragem inicial.

## 12. Apontar para a tarefa

Substitua o conteúdo de:

```text
input/lactacao_tutorial_task_manager_metadata.json
```

por:

```json
{
  "files": {
    "tasks": {
      "title": "Task manager data",
      "description": "Configuração do tutorial de lactação.",
      "path": "input/data/tasks/lactacao_tutorial_task.json",
      "type": "json",
      "properties": "tasks_properties"
    }
  }
}
```

## 13. Criar um filtro de lactação

Crie:

```text
output/output_filters/csv_lactacao_tutorial.txt
```

Adicione estas expressões, uma por linha:

```text
^AnimalModuleReporter\.report_daily_animal_population\.(num_lactating_cows|num_dry_cows|num_cows_total)$
^AnimalModuleReporter\.report_herd_statistics_data\.(daily_milk_production|milking_cow_num|dry_cow_num|avg_days_in_milk)$
```

O nome precisa começar com `csv` para gerar saída CSV.

## 14. Executar o teste

Ative o ambiente e execute:

```bash
source venv/bin/activate

python main.py \
  -p input/lactacao_tutorial_task_manager_metadata.json \
  -v warnings
```

O metadata copiado de `example_animals_only_metadata.json` utiliza:

```json
"simulation_type": "animals_only"
```

Esse modo concentra o primeiro teste no módulo animal.

## 15. Conferir os resultados

Procure os arquivos em:

```text
output/CSVs/
output/logs/
```

Variáveis principais:

| Variável                 | Interpretação                        |
| ------------------------- | -------------------------------------- |
| `num_lactating_cows`    | Vacas em lactação no dia             |
| `num_dry_cows`          | Vacas secas no dia                     |
| `num_cows_total`        | Total de vacas no dia                  |
| `daily_milk_production` | Produção diária de leite do rebanho |
| `avg_days_in_milk`      | Média de dias em lactação           |

No início, espera-se aproximadamente:

```text
16 vacas em lactação
4 vacas secas
20 vacas no total
```

As quantidades mudam porque vacas secam, parem, iniciam nova lactação, são vendidas, morrem ou são substituídas.

## 16. Conferir a população-base com `jq`

Quantidade de vacas em lactação disponíveis:

```bash
jq '[.cows[] | select(.animal_type == "LacCow")] | length' \
  input/data/animal/animal_population.json
```

Quantidade de vacas secas:

```bash
jq '[.cows[] | select(.animal_type == "DryCow")] | length' \
  input/data/animal/animal_population.json
```

Distribuição das vacas em lactação por paridade:

```bash
jq '[.cows[] | select(.animal_type == "LacCow") | .parity]
    | group_by(.)
    | map({paridade: .[0], quantidade: length})' \
  input/data/animal/animal_population.json
```

Esses comandos somente leem o arquivo.

## 17. Gerar uma nova população-base

Se a população fornecida não atender ao cenário, o projeto possui:

```text
input/data/tasks/herd_init_task.json
input/metadata/herd_init_metadata.json
```

Execute:

```bash
python main.py \
  -p input/metadata/herd_init_metadata.json \
  -v warnings
```

O RuFaS cria bezerras e simula seu crescimento, reprodução, partos e lactações. Os valores padrão são:

```json
"herd_initialization": {
  "initial_animal_num": 10000,
  "simulation_days": 5000
}
```

A execução pode ser demorada, mas produz vacas em diferentes paridades, dias em lactação e estados reprodutivos.

O resultado será semelhante a:

```text
output/animal_population-27-Oct-2026_Tue_14-30-00.json
```

Para utilizar o arquivo:

```bash
cp output/animal_population-ARQUIVO_GERADO.json \
   input/data/animal/lactacao_tutorial_population.json
```

Depois altere no metadata do tutorial:

```json
"animal_population": {
  "path": "input/data/animal/lactacao_tutorial_population.json"
}
```

Preserve os outros campos do bloco e execute novamente `SIMULATION_SINGLE_RUN`.

## 18. Redimensionar o rebanho

Escolha:

- `N`: total inicial de vacas;
- `L`: fração desejada em lactação.

Use:

```text
Vacas em lactação ≈ N × L
Vacas secas ≈ N × (1 − L)
```

Exemplo para 100 vacas e 83,56% em lactação:

```json
"cow_num": 100,
"herd_num": 100,
"milking_cow_fraction": 0.8356
```

Resultado aproximado:

```text
84 vacas em lactação
16 vacas secas
```

Para rebanhos maiores, ajuste também:

- limites de compra e venda;
- capacidade dos currais `LAC_COW` e `CLOSE_UP`;
- disponibilidade de alimentos;
- quantidade de novilhas e reposições;
- capacidade do sistema de dejetos.

## 19. Erros comuns

### A soma de `parity_fractions` não é 1

Revise as cinco frações. Elas devem totalizar `1.0`.

### O total inicial não é exatamente o calculado

O RuFaS arredonda cada combinação de paridade e lactação. Use um rebanho maior ou frações que resultem em valores inteiros.

### Faltam vacas de alguma paridade

A população-base precisa conter vacas secas e em lactação nas paridades solicitadas. Gere uma nova população ou revise a distribuição.

### O curral não comporta as vacas

Confira `number_of_stalls` e `max_stocking_density` em `LAC_COW` e `CLOSE_UP`.

### A ração não pode ser formulada

Confira ingredientes e dieta de `LAC_COW`. Os logs mostram quais restrições nutricionais falharam.

### O rebanho perde vacas rapidamente

Verifique mortalidade, descarte, reprodução, novilhas próximas ao parto, reposições e limites de compra e venda.

### Nenhum CSV foi criado

O filtro deve estar em `output/output_filters/`, ter extensão `.txt` e nome iniciado por `csv`.

## 20. Checklist

- [ ] Criei cópias dos arquivos de exemplo.
- [ ] Configurei uma simulação inicial de 30 dias.
- [ ] Defini `cow_num` e `herd_num`.
- [ ] Defini `milking_cow_fraction`.
- [ ] As cinco `parity_fractions` somam `1.0`.
- [ ] Ajustei os limites de compra e venda.
- [ ] Verifiquei os currais `LAC_COW` e `CLOSE_UP`.
- [ ] O metadata aponta para o novo arquivo animal.
- [ ] A tarefa aponta para o novo metadata.
- [ ] Criei o filtro `csv_lactacao_tutorial.txt`.
- [ ] Executei com uma semente fixa.
- [ ] Conferi vacas em lactação, vacas secas e produção de leite.
- [ ] Consultei os logs.

## 21. Arquivos relevantes

- `RUFAS/biophysical/animal/herd_factory.py`: amostragem por paridade e lactação;
- `RUFAS/biophysical/animal/animal.py`: ciclo de vida de cada animal;
- `RUFAS/biophysical/animal/herd_manager.py`: atualização diária do rebanho;
- `RUFAS/biophysical/animal/animal_module_reporter.py`: população e produção;
- `input/data/animal/example_freestall_animal.json`: configuração de referência;
- `input/data/animal/animal_population.json`: população-base fornecida;
- `input/data/tasks/herd_init_task.json`: geração de nova população-base;
- `input/metadata/example_animals_only_metadata.json`: cenário do módulo animal;
- `RUFAS/input/metadata/properties/default.json`: regras de validação.
