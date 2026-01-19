# Projeto de Processamento de Linguagens 

![Texto alternativo](uminho.png)

## Universidade Do Minho Ciências Da Computação

**Feito por:**
- **Luis Miguel Faria Lopes A108392**
- **Lara Catarina Vilaça Lopes A108655**

### 1. Introdução

Este projeto, desenvolvido no âmbito da unidade curricular de Processamento de Linguagens, tem como objetivo a implementação de um compilador para a linguagem Pascal Standard. O projeto visa consolidar os conceitos teóricos através da prática das principais fases de compilação: análise léxica, sintática, semântica e geração de código.

O compilador suporta um subconjunto significativo do Pascal, incluindo declaração de variáveis, tipos primitivos (inteiro, real, booleano, carácter, string), estruturas de controlo de fluxo (condicionais, ciclos), operações aritméticas, relacionais e lógicas, e arrays unidimensionais. A implementação de subprogramas foi considerada opcional no enunciado, pelo que não foi incluída.

A ferramenta foi desenvolvida em Python 3 com a biblioteca PLY (Python Lex-Yacc) para os analisadores léxico e sintático. A geração de código produz instruções para uma máquina virtual baseada em pilha fornecida pelo docente.

Este documento está organizado da seguinte forma: a Secção 2 descreve a metodologia; a Secção 3 apresenta a gramática; as Secções 4 e 5 detalham a análise léxica e sintática; a Secção 6 aborda a geração de código; a Secção 7 apresenta os testes; e a Secção 8 conclui o trabalho.

### 2. Abordagem e Metodologia

A implementação seguiu a arquitetura clássica de compiladores, adaptada aos requisitos do projeto. Foram implementadas as quatro fases fundamentais:

#### 2.1. Fases Implementadas
1. **Análise Léxica** - Conversão do código fonte em tokens
2. **Análise Sintática** - Validação da estrutura gramatical  
3. **Análise Semântica** - Verificação de tipos e contexto
4. **Geração de Código** - Tradução para código da VM

As fases de otimização e geração de código final foram consideradas extras no enunciado.

#### 2.2. Decisões de Projeto

**Implementado:**
- Tipos primitivos: `integer`, `real`, `boolean`, `char`, `string`
- Arrays unidimensionais com índices constantes ou variáveis
- Estruturas de controlo: `if-then-else`, `while-do`, `for-to/downto`, `repeat-until`
- Operadores aritméticos, relacionais e lógicos
- I/O: `readln`, `writeln`
- Função `length()` para strings

**Não implementado (opcional):**
- Subprogramas (`procedure`, `function`) - afeta o Exemplo 5
- Otimização de código
- Múltiplos ficheiros ou módulos
- Tipos estruturados além de arrays

A decisão de não implementar funções deve-se à sua complexidade (gestão de escopos, parâmetros, retorno de valores) e ao facto de serem opcionais no enunciado. Priorizou-se um núcleo sólido que cobre os exemplos 1-4.

#### 2.3. Ferramentas
- **Python 3** com **PLY (Python Lex-Yacc)** para análise léxica e sintática
- **Máquina Virtual** como alvo da geração de código
- **Git** para controlo de versões
- **VS Code** como ambiente de desenvolvimento









### 3. Gramática Implementada

A gramática do compilador foi definida em EBNF e implementada com PLY-Yacc. Define um subconjunto do Pascal Standard focado nos exemplos do enunciado.

#### 3.1. Especificação EBNF da Gramática

```ebnf
Program           -> PROGRAM ID ";" VarDecls BEGIN Statements OptSemicolon END "."

VarDecls          -> VAR VarDeclList
                  | ε

VarDeclList       -> VarDeclList VarDecl ";"
                  | VarDecl ";"

VarDecl           -> IdList ":" Type

IdList            -> ID "," IdList
                  | ID

Type              -> SimpleType
                  | ArrayType

SimpleType        -> INTEGER
                  | BOOLEAN
                  | REAL
                  | CHAR
                  | STRING_TYPE

ArrayType         -> ARRAY "[" NUM DOTDOT NUM "]" OF SimpleType

Statements        -> Statement ";" Statements   
                  | Statement
                  | ε

Statement -> Assignment
           | Writeln
           | Write         
           | IfStatement
           | WhileStatement
           | ForStatement
           | RepeatStatement 
           | Readln
           | Block

Block             -> BEGIN Statements OptSemicolon END

OptSemicolon      -> ";"
                  | ε

Assignment        -> ID ASSIGN Expression                      # Variável simples
                  | ID "[" NUM "]" ASSIGN Expression          # Array índice constante
                  | ID "[" ID "]" ASSIGN Expression           # Array índice variável

Writeln           -> WRITELN "(" WritelnArgs ")"
                  | WRITELN                                  ← ADICIONADO (sem argumentos)

Write             -> WRITE "(" WritelnArgs ")"                ← NOVO!
                  | WRITE                                    ← NOVO! (sem argumentos)

WritelnArgs       -> WritelnArgs "," WritelnArg
                  | WritelnArg

WritelnArg        -> STRING
                  | Expression

Readln            -> READLN "(" ID ")"                         # Variável simples
                  | READLN "(" ID "[" ID "]" ")"              # Array índice variável
                  | READLN "(" ID "[" NUM "]" ")"             # Array índice constante

IfStatement       -> IF Expression THEN Statement ELSE Statement
                  | IF Expression THEN Statement

WhileStatement    -> WHILE Expression DO Statement

ForStatement      -> FOR ID ASSIGN Expression TO Expression DO Statement
                  | FOR ID ASSIGN Expression DOWNTO Expression DO Statement

RepeatStatement   -> REPEAT Statements UNTIL Expression  

Expression        -> LogicalOrExpression

LogicalOrExpression -> LogicalAndExpression
                    | LogicalOrExpression OR LogicalAndExpression

LogicalAndExpression -> RelationalExpression
                     | LogicalAndExpression AND RelationalExpression

RelationalExpression -> SimpleExpression
                     | SimpleExpression RELOP SimpleExpression

SimpleExpression  -> Term
                  | SimpleExpression ADDOP Term
                  | ADDOP Term                               # Operador unário + ou -

Term              -> Factor
                  | Term MULOP Factor
                  | Term DIV Factor                         # Divisão inteira
                  | Term MOD Factor                         # Módulo

Factor            -> ID                                       # Variável
                  | NUM                                      # Número (integer ou real)
                  | STRING                                   # String literal
                  | CHARLIT                                  # Caractere literal
                  | "(" Expression ")"
                  | NOT Factor                               # Negação booleana
                  | TRUE                                     # Booleano true
                  | FALSE                                    # Booleano false
                  | LENGTH "(" Expression ")"                # Função length
                  | ID "[" NUM "]"                           # Array índice constante
                  | ID "[" ID "]"                            # Array índice variável

RELOP             -> "<" | ">" | LE | GE | "=" | NE
ADDOP             -> "+" | "-"
MULOP             -> "*" | "/"
DOTDOT            -> ".."
DIV               -> "div"
MOD               -> "mod"

```

#### 3.2. Hierarquia de Operadores

A gramática implementa uma hierarquia de operadores completa, respeitando a precedência do Pascal:

1. **Parênteses**: `( expression )` - Maior precedência
2. **Operadores unários**: `-`, `+`, `NOT`
3. **Operadores multiplicativos**: `*`, `/`, `DIV`, `MOD`
4. **Operadores aditivos**: `+`, `-`
5. **Operadores relacionais**: `<`, `>`, `<=`, `>=`, `=`, `<>`
6. **Operadores lógicos**: `AND` (maior precedência), `OR` (menor precedência)

#### 3.3. Comparação com o Pascal Standard

| Característica | Pascal Standard | Implementação | Status |
|----------------|-----------------|---------------|--------|
| Estrutura básica | `PROGRAM ... BEGIN ... END.` | Implementado | Completo |
| Tipos de dados | `INTEGER, REAL, BOOLEAN, CHAR, STRING` | Implementado | Completo |
| Arrays | Unidimensionais com índices inteiros | Implementado | Completo |
| Declaração de variáveis | Seção `VAR` com múltiplas declarações | Implementado | Completo |
| Operadores aritméticos | `+ - * / DIV MOD` | Implementado | Completo |
| Operadores relacionais | `< > <= >= = <>` | Implementado | Completo |
| Operadores lógicos | `AND OR NOT` | Implementado | Completo |
| Estruturas de controle | `IF-THEN-ELSE, WHILE-DO, FOR-TO/DOWNTO, REPEAT-UNTIL` | Implementado | Completo |
| Entrada/Saída | `READLN, WRITELN` | Implementado | Completo |
| Blocos | `BEGIN ... END` | Implementado | Completo |
| Funções intrínsecas | `LENGTH()` | Implementado | Extensão útil |
| Subprogramas | `FUNCTION, PROCEDURE` | Não implementado | Opcional no enunciado |
| Arrays multidimensionais | Suportados | Não implementado | Além do escopo |
| Tipos estruturados | `RECORD, SET` | Não implementado | Além do escopo |

#### 3.4. Limitações Conhecidas

1. **Subprogramas:**: Não implementados (opcional)

2. **Arrays:**: Apenas unidimensionais

3. **Escopo:**: Todas variáveis globais

4. **Índices de array:**: Apenas inteiros, não expressões

5. **Conversões implícitas:**: Limitadas às mais comuns

6. **Compatibilidade de Tipos Restrita**: Embora haja verificação de tipos, algumas conversões implícitas do Pascal Standard (como `char` para `string` em contextos específicos) podem não estar totalmente implementadas.

A gramática equilibra completude funcional e complexidade, cobrindo os exemplos 1-4 do enunciado.






### 4. Análise Léxica (Lexer)

A análise léxica converte o código fonte Pascal numa sequência de tokens. Implementada com PLY, o lexer reconhece todos os elementos léxicos necessários.

#### 4.1. Tokens Definidos

**Símbolos Literais**

```python
literals = ['+', '-', '*', '/', '(', ')', ';', '.', ',', ':', '>', '<', '=', '[', ']']
```

**Tokens Simbólicos**

-  `ASSIGN` (`:=`), `GE` (`>=`), `LE` (`<=v`), `NE` (`<>`), `DOTDOT` (`..`)

**Palavras-Chave**

28 palavras-chave organizadas por categoria:

| Categoria | Palavras-Chave |
|-----------|----------------|
| Estrutura Programa | `PROGRAM`, `BEGIN`, `END`, `VAR` |
| Tipos | `INTEGER`, `REAL`, `BOOLEAN`, `CHAR`, `STRING` |
| Controle | `IF`, `THEN`, `ELSE`, `WHILE`, `DO`, `FOR`, `TO`, `DOWNTO`, `REPEAT`, `UNTIL` |
| Operadores | `AND`, `OR`, `NOT`, `DIV`, `MOD` |
| I/O | `READLN`, `WRITELN`, `WRITE`|
| Arrays | `ARRAY`, `OF` |


**Outros Tokens**

- `ID`: Identificadores (`[a-zA-Z_][a-zA-Z0-9_]*`)
- `NUM`: Números inteiros/reais (`\d+(\.\d+)?([eE][+-]?\d+)?`)
- `STRING`: Strings (`'[^']*'` ou `"[^"]*"`)
- `CHARLIT`: Caractere literal ('[^']') 

#### 4.2. Expressões Regulares

```python
# Palavras-chave com limites exatos
def t_PROGRAM(t):
    r'\bprogram\b'  # Evita conflito com "programa"
    return t

# Números com conversão automática
def t_NUM(t):
    r'\d+(\.\d+)?([eE][+-]?\d+)?'  # Números: inteiros, reais com ponto decimal, ou notação científica
    # Converte o valor para int ou float conforme a presença de ponto decimal ou expoente
    if '.' in t.value or 'e' in t.value.lower():
        t.value = float(t.value)  # Se for real, converte para float
    else:
        t.value = int(t.value)    # Caso contrário, converte para int
    return t

# Comentários (3 estilos suportados)
def t_COMMENT(t):
    r'(\{[^}]*\}|//.*|\#.*)'
    pass
```

#### 4.3. Funcionalidades Essenciais

- **Case-insensitive:** `lexer = lex.lex(reflags=re.IGNORECASE)`
- **Contagem de linhas:** `t.lexer.lineno += len(t.value)` em `t_newline`
- **Tratamento de erros:** Reporta caracteres inválidos com número da linha

#### 4.4. Exemplo de Tokenização

Para `x := 42;`:

1. `ID ("x")`
2. `ASSIGN (":=")`
3. `NUM (42)`
4. `    ;`




### 5. Análise Sintática (Parser)

A análise sintática constitui a segunda fase do processo de compilação, responsável por validar a estrutura gramatical do programa fonte segundo as regras da linguagem Pascal. Implementada através da ferramenta PLY-Yacc, o parser utiliza uma abordagem bottom-up (LALR) e executa simultaneamente análise semântica e geração de código numa única passagem.

#### 5.1. Arquitetura e Estrutura Gramatical

O parser implementa uma gramática LALR(1) organizada hierarquicamente:

**Níveis de Abstração:**

1. **Nível de Programa:** `PROGRAM ID ; declarações BEGIN comandos END .`
2. **Nível de Declarações:** Seções `VAR` com múltiplas variáveis e tipos
3. **Nível de Comandos:** Atribuições, estruturas de controle, I/O, blocos
4. **Nível de Expressões:** Sistema completo de operadores com precedência

**Principais Componentes Sintáticos:**

- **Declarações:** Variáveis simples (`x: integer`) e arrays (`vetor: array[1..10] of integer`)
- **Estruturas de Controle:** `IF-THEN[-ELSE]`, `WHILE-DO`, `FOR-TO/DOWNTO`, `REPEAT-UNTIL`
- **Entrada/Saída:** `READLN`, `WRITELN` com múltiplos argumentos
- **Expressões:** Hierarquia completa de operadores aritméticos, relacionais e lógicos

#### 5.2. Sistema de Precedência de Operadores

A gramática implementa a precedência exata do Pascal através da estrutura hierárquica das regras:

| Nível | Operadores | Descrição |
|-------|------------|-----------|
| 1 (maior) | `( )` | Parênteses |
| 2 | `NOT`, `+`, `-` unários | Operadores unários |
| 3 | `*`, `/`, `DIV`, `MOD` | Multiplicativos |
| 4 | `+`, `-` binários | Aditivos |
| 5 | `<`, `>`, `<=`, `>=` | Relacionais |
| 6 | `=`, `<>` | Igualdade |
| 7 | `AND` | Conjunção lógica |
| 8 (menor) | `OR` | Disjunção lógica |

Esta estrutura garante que expressões como `a + b * c` sejam interpretadas como `a + (b * c)`, e `x > y AND z < w` como `(x > y) AND (z < w)`.



#### 5.3. Tabela de Símbolos Integrada

A tabela de símbolos é uma estrutura central que armazena informações sobre todos os identificadores:

**Estrutura `Symbol`:**

```python
class Symbol:
    """Classe para representar um símbolo (variável/array) na tabela de símbolos"""
    
    def __init__(self, name, type_, scope=0, is_array=False, array_start=None, array_end=None):
        """Inicializa um símbolo com nome, tipo e atributos"""
        self.name = name                # Nome da variável (ex: 'x', 'vetor')
        self.type = type_               # Tipo: 'integer', 'real', 'boolean', 'char', 'string'
        self.scope = scope              # Escopo (0=global)
        self.is_array = is_array        # True se for array
        self.array_start = array_start  # Índice inicial do array
        self.array_end = array_end      # Índice final do array
        self.declared = True            # Símbolo foi declarado
        self.address = None             # Endereço na VM (atribuído depois)
        self.is_global = True           # Todas variáveis são globais
```
**Funcionalidades da Tabela:**

- **Registo Automático:**: Variáveis são registadas durante a declaração
- **Verificação de Unicidade:** Evita declarações duplicadas
- **Gestão de Endereços:**  Atribui endereços únicos na VM
- **Suporte a Arrays:** Armazena limites e tipo dos elementos

**Tipos Suportados:**

1. **Tipos Escalares:** `integer`, `real`, `boolean`, `char`, `string`
2. **Arrays Unidimensionais:** `array[início..fim] of tipo`
 


#### 5.4. Verificação Semântica em Tempo Real

A análise semântica é integrada nas ações do parser, realizando verificações contextuais:

**Sistema de Tipos Forte:**

- **Verificação de Declarações:** Uso de variáveis não declaradas gera erro
- **Compatibilidade em Operações:**
    - Numéricas: `integer` ou `real` apenas
    - Booleanas: `boolean` apenas
    - Comparações: tipos idênticos ou compatíveis

- **Verificação em Atribuições:** Compatibilidade entre tipo da variável e da expressão

**Política de Conversões:**

- Permitidas (seguras): `integer→real`, `integer→boolean`, `char→string`
- Proibidas (perigosas): `real→integer`, `string→char`, entre categorias

**Verificações Específicas:**

- **Arrays:** Índices devem ser `integer` e dentro dos limites declarados
- **Estruturas de Controle:** Condições devem ser booleanas
- **FOR:** Variável de controle e limites devem ser `integer`


#### 5.5. Sistema de Tratamento de Erros

O compilador implementa um sistema robusto de reporte de erros:

**Características:**

**Acumulação:** Detecta múltiplos erros numa única compilação
**Contexto:** Mensagens incluem número de linha
**Clareza:** Descrições específicas do erro
**Recuperação:** Continua análise após erros para encontrar mais problemas

**Categorias de Erros:**

1. **Sintáticos:** Violações da gramática (ex: ponto e vírgula a faltar)
2. **Semânticos:** Violações de contexto (ex: tipo incompatível)
3. **Warnings:** Avisos não fatais (ex: índice fora dos limites)

**Exemplo de Saída:**

```text
Erros semânticos:
Linha 5: Erro: Variável 'x' não declarada
Linha 7: Erro: Operação '+' requer operandos numéricos, não boolean e integer
```

#### 5.6. Integração com Geração de Código

O parser segue uma abordagem de tradução dirigida pela sintaxe:

**Princípios:**

1. **Geração Incremental:** Código VM é gerado à medida que construções são reconhecidas
2. **Propagação de Informação:** Tipos e código são propagados através da árvore sintática
3. **Labels Automáticos:** Sistema de geração de labels únicos para controle de fluxo

**Exemplo de Regra Integrada:**

```python
def p_assignment(p):
    r'assignment : ID ASSIGN expression'
    # 1. Validação sintática (regra)
    # 2. Verificação semântica (declaração, tipos)
    # 3. Geração de código (expressão + store)
```

#### 5.7. Otimizações e Decisões de Design

1. **Expressões Tipadas:** Armazenamento de `(tipo, código)` para evitar recálculos
2. **Conversões Eficientes:** Apenas quando necessário (ex: `integer→real`)
3. **Labels Únicos:** Contador global evita conflitos
4. **Acesso a Arrays:** Otimização para índices constantes

**Decisões de Projeto:**

1. **Abordagem Integrada:** Análise sintática, semântica e geração de código numa passagem
2. **Tabela de Símbolos Simples:** Escopo único adequado ao subconjunto implementado
3. **Verificação de Tipos Forte:** Prevenção de erros comuns em tempo de compilação
4. **Extensibilidade:** Arquitetura preparada para adição de funcionalidades

#### 5.8. Conformidade com os Exemplos do Enunciado

O parser suporta integralmente as construções necessárias para os 4 primeiros exemplos:

**Exemplo 1:** Saída simples com `WRITELN`
**Exemplo 2:** `FOR`, multiplicação, I/O com conversão
**Exemplo 3:** `WHILE`, operadores AND, DIV, MOD, condições complexas
**Exemplo 4:** `Arrays`, FOR com índices, acumulação

Esta implementação representa um equilíbrio entre completude funcional e simplicidade de implementação, formando a base robusta do compilador Pascal.







### 6. Geração de Código

A geração de código traduz a representação interna do programa Pascal em instruções executáveis para a Máquina Virtual (VM) fornecida. Esta fase implementa um mapeamento direto e sistemático entre as construções de alto nível do Pascal e as instruções de baixo nível da VM, aproveitando a arquitetura baseada em pilha da máquina-alvo.

#### 6.1. Mapeamento Geral

O compilador segue uma abordagem de tradução dirigida pela sintaxe, gerando código incrementalmente à medida que as construções são reconhecidas. A tabela abaixo resume os principais mapeamentos:

| Construção Pascal       | Instruções VM                     | Descrição                                 |
|-------------------------|-----------------------------------|-------------------------------------------|
| Variáveis escalares     | `PUSHG` / `STOREG`               | Acesso à memória global                   |
| Arrays unidimensionais  | `ALLOCN`, `PADD`, `LOAD`/`STORE` | Alocação no heap e acesso indexado        |
| Operações aritméticas   | `ADD`/`FADD`, `SUB`/`FSUB`, etc. | Seleção automática inteiro/real           |
| Operações relacionais   | `INF`/`FINF`, `SUP`/`FSUP`, etc. | Comparações com tipos adequados           |
| Operações lógicas       | `AND`, `OR`, `NOT`                | Apenas para booleanos                     |
| Controle de fluxo       | `JZ`, `JUMP` + labels             | Saltos condicionais e incondicionais      |
| Entrada/Saída           | `READ`, `WRITEI`/`WRITEF`/`WRITES` | Com conversão automática de tipos        |
| Função `LENGTH()`       | `STRLEN`                         | Comprimento de strings                    |

#### 6.2. Variáveis e Arrays

**Variáveis Simples:** Cada variável recebe um endereço único na memória global da VM. O carregamento usa `PUSHG` e o armazenamento `STOREG`.

**Arrays:** São alocados dinamicamente no heap com `ALLOCN`. O acesso a elementos envolve:

1. Calcular o endereço base (`PUSHG` do endereço do array)
2. Calcular o offset (`PUSH` do índice, ajustar para base 0, `PADD`)
3. Para leitura: `LOAD 0`
4. Para escrita: `STORE 0`

#### 6.3. Controle de Fluxo

As estruturas de controle são implementadas com saltos e labels únicos gerados automaticamente:

- **IF-THEN-ELSE:** Avalia condição, JZ para o bloco ELSE, JUMP para o final.
- **WHILE-DO:** Label no início, avalia condição, JZ para sair.
- **FOR-TO/DOWNTO:** Inicialização, label no início, verificação de limite, incremento/decremento no final.
- **REPEAT-UNTIL:** Executa pelo menos uma vez, avalia condição no final.

Labels são gerados sequencialmente (`parser.label`) para evitar conflitos, mesmo em estruturas aninhadas.

#### 6.4. Operadores

Os operadores são mapeados para instruções VM específicas, com seleção automática baseada nos tipos dos operandos:

- **Aritméticos**: `ADD`/`FADD`, `SUB`/`FSUB`, `MUL`/`FMUL`, `DIV`/`FDIV`
- **Relacionais**: `INF`/`FINF`, `SUP`/`FSUP`, `INFEQ`/`FINFEQ`, `SUPEQ`/`FSUPEQ`
- **Igualdade**: `EQUAL` (funciona para todos os tipos compatíveis)
- **Lógicos**: `AND`, `OR`, `NOT` (apenas para booleanos)
- **Específicos Pascal**: `DIV` e `MOD` para divisão inteira

A função `get_vm_operation()` no parser seleciona a versão inteira ou real baseada nos tipos dos operandos.

#### 6.5. Entrada e Saída

As operações de I/O utilizam instruções específicas da VM com tratamento automático de tipos:

**WRITELN**: Suporta múltiplos argumentos. Para cada argumento, gera código específico:
- **Strings**: `pushs` + `writes`
- **Inteiros**: código da expressão + `writei`
- **Reais**: código da expressão + `writef`
- **Booleanos**: converte para string "true"/"false" + `writes`
- **Chars**: código da expressão + `writechr`

**READLN**: Lê uma string e converte para o tipo da variável destino:
- **integer**: `read` + `atoi`
- **real**: `read` + `atof`
- **boolean**: `read` + `atoi` (0 = false, ≠0 = true)
- **string/char**: `read` (sem conversão)

#### 6.6. Inicialização e Finalização

Todo programa gerado segue uma estrutura padrão:
1. **Inicialização de variáveis**: Valores padrão (0, 0.0, false, "") armazenados com `storeg`
2. **Alocação de arrays**: `allocn` para cada array declarado
3. **Corpo do programa**: Delimitado por `start` e `stop`
4. **Labels e controle de fluxo**: Gerados conforme necessário

#### 6.7. Otimizações e Princípios de Design

**Otimizações Implementadas:**
1. **Conversões seletivas**: Apenas quando necessário (ex: `integer` → `real`)
2. **Reutilização de resultados**: Expressões tipadas `(type, code)` evitam recálculos
3. **Labels únicos**: Sistema automático evita conflitos
4. **Acesso otimizado a arrays**: Cálculo de offset para índices constantes

**Princípios de Design:**
1. **Semântica preservada**: Cada construção Pascal tem comportamento equivalente na VM
2. **Geração incremental**: Código é produzido durante o parsing
3. **Tipagem forte**: Instruções selecionadas com base em tipos estáticos
4. **Extensibilidade**: Arquitetura permite adição de novas construções

#### 6.8. Exemplo de Tradução Completa

O exemplo 4 do enunciado (Soma Array) ilustra a integração de vários conceitos:
- Declaração e alocação de array
- Loop `FOR` com índice variável
- Acesso a array com índice (`PADD`, `STORE`)
- Acumulação e saída formatada

O mapeamento sistemático garante que os programas Pascal compilados executam corretamente na VM, mantendo a semântica original enquanto aproveita eficientemente a arquitetura baseada em pilha.

### 7. Testes e Resultados

#### 7.1. Exemplos do Enunciado

**Exemplo 1: Olá, Mundo!** 

```pascal
program HelloWorld;
begin
  writeln('Ola, Mundo!');
end.
```
**Resultado:**

```vm
start
pushs "Ola, Mundo!"
writes
writeln
stop
```

**Exemplo 2: Fatorial** 

```pascal
program Fatorial;
var
  n, i, fat: integer;
begin
  writeln('Introduza um número inteiro positivo:');
  readln(n);
  fat := 1;
  for i := 1 to n do
    fat := fat * i;
  writeln('Fatorial de ', n, ': ', fat);
end.
```
**Resultado:**

```vm
pushi 0
storeg 0
pushi 0
storeg 1
pushi 0
storeg 2
start
pushs "Introduza um número inteiro positivo:"
writes
writeln
pushs "? "
writes
read
atoi
storeg 0
pushi 1
storeg 2
pushi 1
storeg 1
forstart0:
pushg 1
pushg 0
infeq
jz forend0
pushg 2
pushg 1
mul
storeg 2
pushg 1
pushi 1
add
storeg 1
jump forstart0
forend0:
pushs "Fatorial de "
writes
pushg 0
writei
pushs ": "
writes
pushg 2
writei
writeln
stop
```


**Exemplo 3: Verificação de Número Primo** 

```pascal
program NumeroPrimo;
var
  num, i: integer;
  primo: boolean;
begin
  writeln('Introduza um número inteiro positivo:');
  readln(num);
  primo := true;
  i := 2;
  while (i <= (num div 2)) and primo do
  begin
    if (num mod i) = 0 then
      primo := false;
    i := i + 1;
  end;
  if primo then
    writeln(num, ' é um número primo')
  else
    writeln(num, ' não é um número primo')
end.
```
**Resultado:**

```vm
pushi 0
storeg 0
pushi 0
storeg 1
pushi 0
storeg 2
start
pushs "Introduza um número inteiro positivo:"
writes
writeln
pushs "? "
writes
read
atoi
storeg 0
pushi 1
storeg 2
pushi 2
storeg 1
while1:
pushg 1
pushg 0
pushi 2
div
infeq
pushg 2
and
jz endwhile1
pushg 0
pushg 1
mod
pushi 0
equal
jz endif0
pushi 0
storeg 2
endif0:
pushg 1
pushi 1
add
storeg 1
jump while1
endwhile1:
pushg 2
jz else2
pushg 0
writei
pushs " é um número primo"
writes
writeln
jump endif2
else2:
pushg 0
writei
pushs " não é um número primo"
writes
writeln
endif2:
stop
```

**Exemplo 4: Soma de uma lista de inteiros** 

```pascal
program SomaArray;
var
  numeros: array[1..5] of integer;
  i, soma: integer;
begin
  soma := 0;
  writeln('Introduza 5 números inteiros:');
  for i := 1 to 5 do
  begin
    readln(numeros[i]);
    soma := soma + numeros[i];
  end;
  writeln('A soma dos números é: ', soma);
end.
```
**Resultado:**

```vm
pushi 0
storeg 1
pushi 0
storeg 2
pushi 5
allocn
storeg 0
start
pushi 0
storeg 2
pushs "Introduza 5 números inteiros:"
writes
writeln
pushi 1
storeg 1
forstart0:
pushg 1
pushi 5
infeq
jz forend0
pushs "? "
writes
read
atoi
pushg 0
pushg 1
pushi 1
sub
padd
swap
store 0
pushg 2
pushg 0
pushg 1
pushi 1
sub
padd
load 0
add
storeg 2
pushg 1
pushi 1
add
storeg 1
jump forstart0
forend0:
pushs "A soma dos números é: "
writes
pushg 2
writei
writeln
stop
```


**Exemplo 5: Conversão binário-decimal** 

```pascal
program BinarioParaInteiro;
function BinToInt(bin: string): integer;
var
  i, valor, potencia: integer;
begin
  valor := 0;
  potencia := 1;
  for i := length(bin) downto 1 do
  begin
    if bin[i] = '1' then
      valor := valor + potencia;
    potencia := potencia * 2;
  end;
  BinToInt := valor;
end;
var
  bin: string;
  valor: integer;
begin
  writeln('Introduza uma string binária:');
  readln(bin);
  valor := BinToInt(bin);
  writeln('O valor inteiro correspondente é: ', valor);
end.
```
**Resultado:**

```
ERRO: Erro de sintaxe no token 'function' (tipo: FUNCTION) na linha 3
Nenhum código gerado!
```

Motivo: Funções definidas pelo utilizador não foram implementadas (opcional no enunciado)


#### 7.2. Resultados dos Testes
| Exemplo       | Linhas VM | Variáveis | Arrays | Labels | Status |
|---------------|-----------|-----------|--------|--------|--------|
| Olá Mundo     | 5         | 0         | 0      | 0      | FUNCIONOU|
| Fatorial      | 44        | 3         | 0      | 1      | FUNCIONOU |
| Número Primo  | 58        | 3         | 0      | 3      | FUNCIONOU |
| Soma Array    | 51        | 2         | 1      | 1      | FUNCIONOU |




#### 8. Síntese dos Resultados

**Objetivos Alcançados:**

1. **Pipeline Completo de Compilação**: Implementação das quatro fases fundamentais: análise léxica (lexer PLY), análise sintática (parser PLY-Yacc), análise semântica integrada e geração de código VM.

2. **Cobertura dos Exemplos Obrigatórios**: Suporte integral aos exemplos 1-4 do enunciado:
   - *Exemplo 1*: Estrutura básica e saída simples
   - *Exemplo 2*: Controlo de fluxo (FOR), operações aritméticas, I/O
   - *Exemplo 3*: Estruturas complexas (WHILE, IF), operadores lógicos e aritméticos (MOD, DIV)
   - *Exemplo 4*: Arrays unidimensionais com índices constantes e variáveis

3. **Extensões Úteis Implementadas**:
   - Função intrínseca `LENGTH()` para strings
   - Suporte a tipos `real` com conversões automáticas
   - Estrutura `REPEAT..UNTIL`
   - Sistema de warnings para índices de array fora dos limites

4. **Qualidade do Código Gerado**: O compilador produz código VM correto, eficiente e compatível com a máquina fornecida, preservando a semântica original dos programas Pascal.

#### 9. Análise das Limitações

**Principais Restrições:**

1. **Subprogramas Não Implementados**: A ausência de funções e procedimentos impede o suporte ao Exemplo 5, seguindo a classificação desta funcionalidade como opcional no enunciado.

2. **Escopo Simplificado**: Todas as variáveis são tratadas como globais, não havendo suporte a variáveis locais ou parâmetros.

3. **Tipos de Dados Básicos**: Limitado aos tipos primitivos (`integer`, `real`, `boolean`, `char`, `string`) e arrays unidimensionais.

4. **Otimizações Limitadas**: Geração de código direta sem otimizações avançadas.


#### 10. Possíveis Melhorias

**Melhorias Imediatas (Alta Prioridade):**

1. **Implementação de Subprogramas**: Adicionar suporte a `FUNCTION` e `PROCEDURE` com gestão de escopos
2. **Expansão do Sistema de Tipos**: Tipos enumerados, subintervalo e records
3. **Arrays Multidimensionais**: Extensão da gramática e geração de código

**Otimizações (Média Prioridade):**

1. **Constant Folding**: Avaliação de expressões constantes em tempo de compilação
2. **Propagação de Constantes**: Substituição de variáveis com valor conhecido
3. **Eliminação de Código Morto**: Remoção de código inalcançável

**Extensões (Baixa Prioridade):**

1. **Suporte a Múltiplos Ficheiros**: Compilação separada e ligação
2. **Sistema de Módulos**: Organização modular de código
3. **Depurador Integrado**: Instrumentação para debugging



#### 11. Conclusão 


Neste projeto foi implementado um compilador que constitui uma aplicação bem-sucedida e funcional dos conceitos fundamentais da construção de compiladores. Apesar das limitações deliberadas, nomeadamente a ausência de subprogramas considerada opcional no enunciado, o sistema cumpre integralmente todos os requisitos obrigatórios processando corretamente os exemplos 1 a 4. A implementação atual estabelece uma base sólida para futuras extensões, apresentando uma arquitetura que facilita a integração de funcionalidades adicionais, como subprogramas, tipos de dados mais avançados e possíveis otimizações. Mesmo com recursos limitados, foi possível desenvolver um compilador funcional, capaz de traduzir de forma eficiente construções de alto nível para código executável.

Em síntese, este projeto não apenas atingiu os objetivos académicos definidos, mas também proporcionou uma compreensão profunda e prática dos princípios de construção de compiladores, constituindo uma base sólida para trabalho futuro na área de processamento de linguagens.