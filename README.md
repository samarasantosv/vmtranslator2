# VMTranslator – Parte 2

Continuação do tradutor de código VM (Virtual Machine) do Nand2Tetris para
Assembly da CPU Hack. Esta segunda etapa estende o projeto da Parte 1,
adicionando controle de fluxo e sub-rotinas, sem reescrever o que já havia
sido implementado.

## Integrante

Samara Santos Viegas — Matrícula: 2022042898

## Linguagem de programação e versão

Python 3 (desenvolvido e testado com Python 3.11, mas compatível com
qualquer versão 3.8+)

Nenhuma biblioteca externa foi utilizada — apenas a biblioteca padrão do
Python.

---

## O que foi adicionado nesta etapa

- Código de **bootstrap**, que inicializa `SP = 256` e chama `Sys.init`,
  gerado automaticamente quando a entrada do tradutor é um diretório
- Comandos de **controle de fluxo**: `label`, `goto`, `if-goto`
- Comandos de **sub-rotinas**: `function`, `call`, `return`
- Suporte a **múltiplos arquivos `.vm`** em um mesmo diretório, traduzidos
  em conjunto para um único arquivo `.asm`

O `Parser` e o `CodeWriter` da Parte 1 foram **estendidos**, não reescritos:
os métodos de `push`/`pop`/operações aritméticas continuam exatamente iguais.

---

## Instruções de build e execução

Não há etapa de compilação — Python é interpretado. É necessário apenas ter
o Python 3 instalado.

O tradutor agora aceita **dois modos de entrada**:

### 1. Um único arquivo `.vm` (sem bootstrap)

Usado quando o próprio script `.tst` do teste já inicializa `SP`, `LCL` e
`ARG` manualmente (caso dos testes de `ProgramFlow` e de `SimpleFunction`).

```bash
python main.py caminho/para/Arquivo.vm
```

Gera `Arquivo.asm` na mesma pasta do `.vm` de entrada.

### 2. Um diretório com um ou mais arquivos `.vm` (com bootstrap automático)

Usado quando o programa depende de `Sys.init` para inicializar a pilha e
chamar a primeira função (caso do teste `NestedCall`).

```bash
python main.py caminho/para/DiretorioDoPrograma/
```

Gera `DiretorioDoPrograma.asm` dentro do próprio diretório, contendo o
bootstrap seguido da tradução de todos os `.vm` encontrados na pasta.

### Exemplo de uso

```bash
python main.py tests/FunctionCalls/NestedCall
```

Saída no terminal:

```
Traducao concluida: tests/FunctionCalls/NestedCall/NestedCall.asm
```

---

## Estrutura do projeto

```
vmtranslator/
├── codewriter/
│   ├── __init__.py
│   └── codewriter.py    # Geração do código Assembly Hack (Parte 1 + Parte 2)
├── parser/
│   ├── __init__.py
│   └── parser.py        # Leitura e tokenização do(s) arquivo(s) .vm (Parte 1 + Parte 2)
├── tests/
│   ├── StackArithmetic/          # testes da Parte 1
│   ├── MemoryAccess/              # testes da Parte 1
│   ├── ProgramFlow/
│   │   ├── BasicLoop/
│   │   │   ├── BasicLoop.vm
│   │   │   ├── BasicLoop.tst
│   │   │   └── BasicLoop.cmp
│   │   └── FibonacciSeries/
│   │       ├── FibonacciSeries.vm
│   │       ├── FibonacciSeries.tst
│   │       └── FibonacciSeries.cmp
│   └── FunctionCalls/
│       ├── SimpleFunction/
│       │   ├── SimpleFunction.vm
│       │   ├── SimpleFunction.tst
│       │   └── SimpleFunction.cmp
│       └── NestedCall/
│           ├── NestedCall.vm
│           ├── Sys.vm
│           ├── NestedCall.tst
│           └── NestedCall.cmp
├── main.py               # Ponto de entrada (agora aceita arquivo OU diretório)
├── README.md
└── .gitignore
```

---

## Detalhamento de cada parte implementada

### 1. Parser (`parser/parser.py`) — extensões

Além dos tipos já existentes (`C_ARITHMETIC`, `C_PUSH`, `C_POP`), o
`command_type()` passou a reconhecer:

| Tipo | Comando VM | Descrição |
| --- | --- | --- |
| `C_LABEL` | `label X` | Define um rótulo para saltos |
| `C_GOTO` | `goto X` | Salto incondicional |
| `C_IF` | `if-goto X` | Salta se o topo da pilha for diferente de 0 |
| `C_FUNCTION` | `function nome nLocals` | Declara uma função com `nLocals` variáveis locais |
| `C_CALL` | `call nome nArgs` | Chama uma função passando `nArgs` argumentos |
| `C_RETURN` | `return` | Retorna da função atual para quem a chamou |

O método `arg1()` foi ajustado para não ser chamado em `C_RETURN` (esse
comando não tem argumentos), e `arg2()` passou a ser usado também por
`function`/`call` (número de variáveis locais / número de argumentos).

### 2. CodeWriter (`codewriter/codewriter.py`) — extensões

| Método novo | O que faz |
| --- | --- |
| `set_file_name(nome)` | Define o prefixo usado nas variáveis `static` de cada arquivo `.vm` traduzido (necessário agora que um `.asm` pode conter vários `.vm`) |
| `write_label(nome)` | Gera o rótulo `(funcaoAtual$nome)` |
| `write_goto(nome)` | Gera salto incondicional para o rótulo |
| `write_if(nome)` | Desempilha o topo e salta se o valor for diferente de zero |
| `write_function(nome, nLocals)` | Gera o rótulo da função e inicializa `nLocals` variáveis locais com 0 |
| `write_call(nome, nArgs)` | Gera o protocolo completo de chamada de função |
| `write_return()` | Gera o protocolo de retorno de função |
| `write_init()` | Gera o bootstrap (`SP = 256` + `call Sys.init 0`) |

#### Controle de fluxo

| Comando VM | Tradução |
| --- | --- |
| `label X` | `(funcaoAtual$X)` |
| `goto X` | `@funcaoAtual$X` seguido de `0;JMP` |
| `if-goto X` | Desempilha o topo; se diferente de 0, salta para `funcaoAtual$X` |

Os rótulos são "namespaced" com o nome da função atual (`funcaoAtual$X`) para
evitar que um `label` de mesmo nome em funções diferentes cause colisão.

#### Bootstrap

Escrito uma única vez, no início do `.asm`, apenas quando a entrada é um
diretório:

```asm
@256
D=A
@SP
M=D
```

seguido de uma chamada `call Sys.init 0`, que transfere o controle para a primeira função do programa.

#### `function nome nLocals`

Escreve o rótulo da função e empilha `0` para cada variável local declarada, deixando a pilha pronta para o corpo da função usar `local i`.

#### `call nome nArgs`

1. Empilha o endereço de retorno (rótulo único, gerado como `nome$ret.N`, onde `N` é um contador global que garante que cada chamada tenha um
 rótulo diferente, mesmo que a mesma função seja chamada várias vezes)
2. Empilha `LCL`, `ARG`, `THIS`, `THAT` do chamador (salvando o "frame" atual)
3. Ajusta `ARG = SP - 5 - nArgs` (aponta para o primeiro argumento empilhado)
4. Ajusta `LCL = SP`
5. Salta para a função chamada
6. Define o rótulo de retorno logo em seguida

#### `return`

Usa dois registradores temporários (`R13` e `R14`) para guardar,
respectivamente, o endereço do frame da função atual (`endFrame = LCL`) e o endereço de retorno, **antes** de começar a sobrescrever a pilha. Depois:

1. Move o valor de retorno (topo da pilha) para a posição do primeiro
   argumento (`*ARG = pop()`)
2. Ajusta `SP = ARG + 1`
3. Restaura `THAT`, `THIS`, `ARG` e `LCL` do chamador, lendo-os de trás para frente a partir do frame salvo em `R13`
4. Salta para o endereço de retorno guardado em `R14`

> Essa lógica foi validada manualmente simulando a execução da CPU Hack
> (push 4, push 5, call de uma função de soma, return) antes de ser
> considerada pronta — o resultado correto (9) foi confirmado.

### 3. Main (`main.py`) — extensões

Passou a detectar se o argumento recebido é um **arquivo** ou um
**diretório**:

- **Arquivo `.vm`**: traduz apenas aquele arquivo, sem escrever bootstrap.
- **Diretório**: coleta todos os `.vm` da pasta, escreve o bootstrap uma
  única vez no início do `.asm` de saída, e traduz cada arquivo em
  sequência, atualizando o prefixo de variáveis `static` a cada troca de
  arquivo (via `set_file_name`).

```python
if os.path.isdir(input_path):
    vm_files = [...]          # todos os .vm da pasta
    write_bootstrap = True
else:
    vm_files = [input_path]
    write_bootstrap = False

codewriter = CodeWriter(output_path)
if write_bootstrap:
    codewriter.write_init()

for vm_file in vm_files:
    process_file(vm_file, codewriter)   # aplica Parser + CodeWriter

codewriter.close()
```

---

## Como testar

Testes oficiais do Nand2Tetris, pasta `projects/08`, organizados dentro de
`tests/ProgramFlow/` e `tests/FunctionCalls/`.

```bash
python main.py tests/ProgramFlow/BasicLoop/BasicLoop.vm
python main.py tests/ProgramFlow/FibonacciSeries/FibonacciSeries.vm
python main.py tests/FunctionCalls/SimpleFunction/SimpleFunction.vm
python main.py tests/FunctionCalls/NestedCall
```

> Repare que `NestedCall` recebe a **pasta**, não o arquivo `.vm` — é isso
> que ativa o bootstrap automático (`SP=256` + `call Sys.init`).

Validação de cada `.asm` gerado feita no CPU Emulator do Nand2Tetris:
carregando o `.tst` correspondente (menu File → Load Script) e rodando até o
fim, conferindo a mensagem `Comparison ended successfully`.

---

## Testes realizados

| # | Teste | Foco | Resultado |
| --- | --- | --- | --- |
| 1 | `ProgramFlow/BasicLoop` | `label`, `goto`, `if-goto` | ✅ Comparison ended successfully |
| 2 | `ProgramFlow/FibonacciSeries` | recursão/loop mais longo | ✅ Comparison ended successfully |
| 3 | `FunctionCalls/SimpleFunction` | `function`/`return` básicos | ✅ Comparison ended successfully |
| 4 | `FunctionCalls/NestedCall` | bootstrap + `call`/`return` aninhados | ✅ Comparison ended successfully |

**1. BasicLoop**

![Teste BasicLoop no CPUEmulator](sucesso1.png)

**2. FibonacciSeries**

![Teste FibonacciSeries no CPUEmulator](sucesso2.png)

**3. SimpleFunction**

![Teste SimpleFunction no CPUEmulator](sucesso3.png)

**4. NestedCall**

![Teste NestedCall no CPUEmulator](sucesso4.png)

---

## Dificuldades e aprendizados

- O maior cuidado foi na implementação de `call`/`return`: como o `return` precisa ler o endereço de retorno e os valores salvos de `LCL`/`ARG`/`THIS`/ `THAT` **antes** de a pilha ser modificada, usar dois registradores temporários (`R13` e `R14`) para guardar essas informações logo no início evitou bugs de sobrescrita.
- Os rótulos de `label`/`goto` precisam ser únicos por função (não só por arquivo), por isso o nome da função atual é usado como prefixo.
- O bootstrap só deve ser escrito quando o programa é composto por vários arquivos `.vm` (um diretório); nos testes de arquivo único a inicialização já é feita pelo próprio script `.tst`.

---
- Testes oficiais: pacote Nand2Tetris, pasta `projects/08`