# Importação da biblioteca PLY para análise léxica e da biblioteca 're' para expressões regulares
import ply.lex as lex
import re  # Utilizada para configurar flags no lexer (ex: case-insensitive)

# Lista de literais - caracteres individuais que são retornados como tokens diretamente
# Estes incluem operadores aritméticos, pontuação e delimitadores
literals = ['+', '-', '*', '/', '(', ')', ';', '.', ',', ':', '>', '<', '=', '[', ']']

# Lista de tokens - todos os tokens que não são literais (precisam de regras específicas)
# Inclui:
# - Tokens básicos: números, identificadores, strings
# - Operadores compostos: atribuição (:=), comparações (>=, <=, <>), intervalo (..)
# - Palavras-chave da linguagem Pascal: program, begin, end, var, tipos, estruturas de controle, etc.
# - Palavras-chave para subprogramas (function, procedure) e arrays (array, of)
# - Valores booleanos (true, false) e função intrínseca (length)
tokens = ['NUM', 'ID', 'CHARLIT', 'STRING',  # <-- ADICIONE CHARLIT aqui
          'ASSIGN', 'GE', 'LE', 'NE', 'DOTDOT',
          'PROGRAM', 'BEGIN', 'END', 'VAR', 'INTEGER', 'BOOLEAN', 'REAL', 'CHAR', 'STRING_TYPE',
          'IF', 'THEN', 'ELSE', 'WHILE', 'DO', 'FOR', 'TO', 'DOWNTO', 'REPEAT', 'UNTIL',
          'AND', 'OR', 'NOT', 'DIV', 'MOD',
          'WRITELN', 'READLN', 'FUNCTION', 'PROCEDURE', 'ARRAY', 'OF', 'WRITE',
          'TRUE', 'FALSE', 'LENGTH']

# Definição das regras para as palavras-chave usando expressões regulares com \b (boundary)
# O \b assegura que a palavra seja reconhecida apenas como uma palavra completa, evitando
# que seja confundida com parte de um identificador (ex: 'end' em 'endpoint').

def t_PROGRAM(t):
    r'\bprogram\b'  # Reconhece a palavra 'program' como token PROGRAM
    return t        # Retorna o token

def t_BEGIN(t):
    r'\bbegin\b'    # Reconhece 'begin'
    return t

def t_END(t):
    r'\bend\b'      # Reconhece 'end'
    return t

def t_WRITE(t):
    r'\bwrite\b'  # Reconhece 'write' (sem pular linha)
    return t

def t_VAR(t):
    r'\bvar\b'      # Reconhece 'var'
    return t

def t_INTEGER(t):
    r'\binteger\b'  # Reconhece 'integer' (tipo inteiro)
    return t

def t_BOOLEAN(t):
    r'\bboolean\b'  # Reconhece 'boolean' (tipo lógico)
    return t

def t_REAL(t):
    r'\breal\b'     # Reconhece 'real' (tipo real)
    return t

def t_CHAR(t):
    r'\bchar\b'     # Reconhece 'char' (tipo caractere)
    return t

def t_STRING_TYPE(t):
    r'\bstring\b'   # Reconhece 'string' (tipo string)
    return t

def t_ARRAY(t):
    r'\barray\b'    # Reconhece 'array'
    return t

def t_OF(t):
    r'\bof\b'       # Reconhece 'of'
    return t

def t_FUNCTION(t):
    r'\bfunction\b' # Reconhece 'function' (não implementada, mas reconhecida lexicalmente)
    return t

def t_PROCEDURE(t):
    r'\bprocedure\b' # Reconhece 'procedure' (não implementada, mas reconhecida lexicalmente)
    return t

def t_IF(t):
    r'\bif\b'       # Reconhece 'if'
    return t

def t_THEN(t):
    r'\bthen\b'     # Reconhece 'then'
    return t

def t_ELSE(t):
    r'\belse\b'     # Reconhece 'else'
    return t

def t_WHILE(t):
    r'\bwhile\b'    # Reconhece 'while'
    return t

def t_DO(t):
    r'\bdo\b'       # Reconhece 'do'
    return t

def t_FOR(t):
    r'\bfor\b'      # Reconhece 'for'
    return t

def t_TO(t):
    r'\bto\b'       # Reconhece 'to' (usado em loops for)
    return t

def t_DOWNTO(t):
    r'\bdownto\b'   # Reconhece 'downto' (usado em loops for decrescentes)
    return t

def t_REPEAT(t):
    r'\brepeat\b'   # Reconhece 'repeat'
    return t

def t_UNTIL(t):
    r'\buntil\b'    # Reconhece 'until'
    return t

def t_AND(t):
    r'\band\b'      # Reconhece 'and' (operador lógico)
    return t

def t_OR(t):
    r'\bor\b'       # Reconhece 'or' (operador lógico)
    return t

def t_NOT(t):
    r'\bnot\b'      # Reconhece 'not' (operador lógico) - agora só como palavra completa
    return t

def t_DIV(t):
    r'\bdiv\b'      # Reconhece 'div' (divisão inteira)
    return t

def t_MOD(t):
    r'\bmod\b'      # Reconhece 'mod' (resto da divisão inteira)
    return t

def t_WRITELN(t):
    r'\bwriteln\b'  # Reconhece 'writeln' (saída de dados)
    return t

def t_READLN(t):
    r'\breadln\b'   # Reconhece 'readln' (entrada de dados)
    return t

def t_LENGTH(t):
    r'\blength\b'   # Reconhece 'length' (função intrínseca para strings)
    return t

def t_TRUE(t):
    r'\btrue\b'     # Reconhece 'true' (valor booleano)
    t.value = True  # Converte o valor do token para o booleano Python True
    return t

def t_FALSE(t):
    r'\bfalse\b'    # Reconhece 'false' (valor booleano)
    t.value = False # Converte o valor do token para o booleano Python False
    return t

# Regras para tokens não-palavras-chave (operadores compostos, identificadores, números, strings, etc.)

def t_ASSIGN(t):
    r':='           # Operador de atribuição do Pascal (dois pontos e igual)
    return t

def t_GE(t):
    r'>='           # Operador relacional "maior ou igual"
    return t

def t_LE(t):
    r'<='           # Operador relacional "menor ou igual"
    return t

def t_NE(t):
    r'<>'           # Operador relacional "diferente"
    return t

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'  # Identificadores: começam com letra ou underscore, seguido por zero ou mais letras, dígitos ou underscores
    return t

def t_DOTDOT(t):
    r'\.\.'         # Operador de intervalo (ex: 1..10)
    return t

def t_NUM(t):
    r'\d+(\.\d+)?([eE][+-]?\d+)?'  # Números: inteiros, reais com ponto decimal, ou notação científica
    # Converte o valor para int ou float conforme a presença de ponto decimal ou expoente
    if '.' in t.value or 'e' in t.value.lower():
        t.value = float(t.value)  # Se for real, converte para float
    else:
        t.value = int(t.value)    # Caso contrário, converte para int
    return t

# --- NOVA REGRA: CHARLIT (UM caractere) ---
def t_CHARLIT(t):
    r"'(\\'|[^'])'"  # Exatamente UM caractere entre aspas simples
    # Aceita: 'A', ' ', '\'' (caractere aspa escapada)
    t.value = t.value[1:-1]  # Remove as aspas
    # Se for caractere escapado (\'), converte para '
    if t.value == "\\'":
        t.value = "'"
    return t

# --- REGRA STRING MODIFICADA (2+ caracteres) ---
def t_STRING(t):
    r"'(\\'|[^'])*'|\"(\\\"|[^\"])*\""  # Zero ou mais caracteres entre aspas
    # Remove as aspas delimitadoras
    t.value = t.value[1:-1]
    # Processa caracteres escapados
    t.value = t.value.replace("\\'", "'").replace('\\"', '"')
    return t

def t_COMMENT(t):
    r'(\{[^}]*\}|//.*|\#.*)'  # Comentários: estilo Pascal { ... }, estilo C++ //, ou estilo shell #
    pass  # Descarta comentários (não retorna token)

def t_newline(t):
    r'\n+'          # Reconhece uma ou mais novas linhas
    t.lexer.lineno += len(t.value)  # Incrementa o contador de linhas do lexer
    # Não retorna token (apenas atualiza o estado)

# Caracteres a ignorar: espaços, tabs e retornos de carro
t_ignore = ' \t\r'

# Função de tratamento de erros léxicos
def t_error(t):
    print(f"Caractere inválido: '{t.value[0]}' na linha {t.lineno}")  # Imprime mensagem de erro com o caractere e linha
    t.lexer.skip(1)  # Pula o caractere inválido e continua a análise

# Criação do lexer com a flag re.IGNORECASE para tornar as regras case-insensitive (Pascal não diferencia maiúsculas/minúsculas)
lexer = lex.lex(reflags=re.IGNORECASE)