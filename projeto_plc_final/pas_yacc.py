# IMPORTAÇÕES E CONFIGURAÇÃO INICIAL
from pas_lex import lexer, tokens, literals  # Importa o lexer e definições de tokens
import ply.yacc as yacc  # Biblioteca para construção de parsers LALR
import os  # Para operações com sistema de arquivos

# Remove arquivos de cache do parser para forçar regeneração
# Isso evita problemas com tabelas de parsing desatualizadas
for f in ['parser.out', 'parsetab.py', 'parsetab.pyc']:
    if os.path.exists(f):
        os.remove(f)

# Classe para representar um símbolo na tabela
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
        
    def __repr__(self):
        """Representação para debug: mostra tipo e limites se for array"""
        if self.is_array:
            return f"Symbol({self.name}, {self.type}[{self.array_start}..{self.array_end}])"
        return f"Symbol({self.name}, {self.type})"

def init():
    """
    Inicializa/reinicializa o estado do parser para compilar um novo programa.
    Deve ser chamada antes de cada análise de um programa Pascal.
    
    Returns:
        parser: O parser com estado limpo para nova compilação
    """
    parser.error = None                     # Limpa erros sintáticos anteriores
    parser.semantic_errors = []            # Lista vazia para novos erros semânticos
    parser.label = 0                       # Contador de labels (para saltos) reiniciado
    parser.vars = []                       # Lista de variáveis simples (não arrays)
    parser.arrays = []                     # Lista de arrays para alocação na VM
    parser.symbol_table = {}               # Tabela de símbolos vazia
    parser.current_scope = 0               # Escopo atual (0 = global)
    parser.next_address = 0                # Próximo endereço disponível na VM
    return parser                          # Retorna o parser inicializado

def add_semantic_error(message, line=None):
    """
    Adiciona um erro semântico à lista de erros do parser.
    
    Args:
        message (str): Descrição do erro semântico
        line (int, optional): Número da linha onde ocorreu o erro
    """
    if line:
        message = f"Linha {line}: {message}"  # Adiciona informação da linha ao erro
    if message not in parser.semantic_errors:  # Evita duplicação de erros
        parser.semantic_errors.append(message)

# ============================================================================
# FUNÇÕES AUXILIARES PARA VERIFICAÇÃO DE TIPOS
# ============================================================================

def is_numeric_type(type_):
    """Verifica se o tipo é numérico (integer ou real)"""
    return type_ in ['integer', 'real']

def is_boolean_type(type_):
    """Verifica se o tipo é boolean"""
    return type_ == 'boolean'

def is_string_type(type_):
    """Verifica se o tipo é string"""
    return type_ == 'string'

def is_char_type(type_):
    """Verifica se o tipo é char"""
    return type_ == 'char'

def is_string_or_char_type(type_):
    """Verifica se o tipo é string ou char (ambos para operações de texto)"""
    return type_ in ['string', 'char']

def get_expression_type(p, index):
    """
    Obtém o tipo de uma expressão a partir de uma produção do parser.
    
    As expressões são armazenadas como tuplas (tipo, código_VM).
    Retorna None se o elemento não for uma expressão tipada.
    """
    if isinstance(p[index], tuple) and len(p[index]) == 2:
        return p[index][0]  # Primeiro elemento da tupla é o tipo
    return None

def get_expression_code(p, index):
    """
    Obtém o código VM de uma expressão a partir de uma produção do parser.
    
    Retorna o código VM (lista de strings) ou lista vazia se não for expressão.
    """
    if isinstance(p[index], tuple) and len(p[index]) == 2:
        return p[index][1]  # Segundo elemento da tupla é o código VM
    return p[index] if isinstance(p[index], list) else []

def get_vm_operation(op, type1, type2):
    """
    Retorna a instrução VM correta para um operador, baseada nos tipos dos operandos.
    
    Escolhe entre versão inteira e ponto flutuante conforme necessário.
    """
    # Se algum operando for real, a operação deve ser em ponto flutuante
    is_float = (type1 == 'real' or type2 == 'real')
    
    if op == '+':
        return 'fadd' if is_float else 'add'
    elif op == '-':
        return 'fsub' if is_float else 'sub'
    elif op == '*':
        return 'fmul' if is_float else 'mul'
    elif op == '/':
        return 'fdiv' if is_float else 'div'
    elif op == '<':
        return 'finf' if is_float else 'inf'
    elif op == '>':
        return 'fsup' if is_float else 'sup'
    elif op == '<=':
        return 'finfeq' if is_float else 'infeq'
    elif op == '>=':
        return 'fsupeq' if is_float else 'supeq'
    else:
        return op  # Para operadores que não mudam (ex: equal, and, or)

def create_typed_expression(type_, code):
    """
    Cria uma expressão tipada no formato (tipo, código_VM).
    
    Retorna uma tupla que pode ser propagada nas regras do parser.
    """
    return (type_, code) if code else (type_, [])

def check_operation_compatibility(op, left_type, right_type, line=None):
    """
    Verifica se uma operação binária é compatível com os tipos dos operandos
    
    Args:
        op (str): Operador ('+', '-', '*', '/', '<', '>', '<=', '>=', '=', '<>', 'and', 'or', 'div', 'mod')
        left_type (str): Tipo do operando esquerdo
        right_type (str): Tipo do operando direito
        line (int, optional): Número da linha para mensagens de erro
    
    Returns:
        bool: True se a operação é compatível, False se não é
    """
    
    # Operações numéricas: +, -, *, /, comparações, div, mod
    if op in ['+', '-', '*', '/', '<', '>', '<=', '>=', 'div', 'mod']:
        # Verifica se ambos os operandos são numéricos (integer ou real)
        if not is_numeric_type(left_type) or not is_numeric_type(right_type):
            add_semantic_error(f"Erro: Operação '{op}' requer operandos numéricos, não {left_type} e {right_type}", line)
            return False
    
    # Operações booleanas: and, or
    elif op in ['and', 'or']:
        # Verifica se ambos os operandos são booleanos
        if not is_boolean_type(left_type) or not is_boolean_type(right_type):
            add_semantic_error(f"Erro: Operação '{op}' requer operandos booleanos, não {left_type} e {right_type}", line)
            return False
    
    # Operações de igualdade/desigualdade: =, <>
    elif op in ['=', '<>']:
        # Se os tipos forem diferentes, verifica compatibilidade
        if left_type != right_type:
            # Permite comparações entre:
            # 1. integer/real (conversão implícita)
            # 2. string/char (tipos de texto)
            # 3. boolean/boolean (já são iguais, não entra aqui)
            if not ((left_type in ['integer', 'real'] and right_type in ['integer', 'real']) or
                   (is_string_or_char_type(left_type) and is_string_or_char_type(right_type))):
                add_semantic_error(f"Erro: Comparação '{op}' entre tipos incompatíveis: {left_type} e {right_type}", line)
                return False
    
    # Operação é compatível
    return True

def check_assignment_compatibility(var_type, expr_type, var_name, line=None):
    """
    Verifica se uma atribuição é válida conforme as regras de tipos do Pascal.
    
    Args:
        var_type (str): Tipo da variável que recebe o valor
        expr_type (str): Tipo da expressão que está sendo atribuída
        var_name (str): Nome da variável (para mensagens de erro)
        line (int, optional): Número da linha no código fonte
    
    Returns:
        bool: True se a atribuição é válida, False caso contrário
    """
    
    # Tipos iguais: sempre permitido (ex: integer := integer)
    if var_type == expr_type:
        return True
    
    # CONVERSÕES IMPLÍCITAS PERMITIDAS (seguras)
    
    # 1. integer -> real (promoção numérica sem perda)
    if var_type == 'real' and expr_type == 'integer':
        return True  # Ex: real_var := 10 (10 -> 10.0)
    
    # 2. integer -> boolean (0 = false, qualquer outro = true)
    if var_type == 'boolean' and expr_type == 'integer':
        return True  # Ex: bool_var := 1 (1 -> true)
    
    # 3. char -> string (um caractere pode ser string de tamanho 1)
    if var_type == 'string' and expr_type == 'char':
        return True  # Ex: string_var := 'A'
    
    # CONVERSÕES NÃO PERMITIDAS (geram erro)
    
    # 1. real -> integer (perde parte decimal)
    if var_type == 'integer' and expr_type == 'real':
        add_semantic_error(
            f"Erro: Atribuição de real para integer na variável '{var_name}' requer conversão explícita", 
            line
        )
        return False  # Ex: integer_var := 3.14 -> ERRO
    
    # 2. string -> char (string pode ter múltiplos caracteres)
    if var_type == 'char' and expr_type == 'string':
        add_semantic_error(
            f"Aviso: Atribuindo string a char na variável '{var_name}' - em runtime será verificado se tem 1 caractere", 
            line
        )
        return True  # Ex: char_var := 'ABC' -> ERRO
    
    # 3. Tipos incompatíveis: string/char <- número
    if is_string_or_char_type(var_type) and is_numeric_type(expr_type):
        add_semantic_error(
            f"Erro: Atribuição de {expr_type} para {var_type} na variável '{var_name}' não permitida", 
            line
        )
        return False  # Ex: string_var := 123 -> ERRO
    
    # 4. Tipos incompatíveis: número <- string/char
    if is_numeric_type(var_type) and is_string_or_char_type(expr_type):
        add_semantic_error(
            f"Erro: Atribuição de {expr_type} para {var_type} na variável '{var_name}' não permitida", 
            line
        )
        return False  # Ex: integer_var := '123' -> ERRO
    
    # Caso geral: qualquer outra combinação não suportada
    add_semantic_error(
        f"Erro: Atribuição de tipo incompatível na variável '{var_name}': {expr_type} para {var_type}", 
        line
    )
    return False



# REGRAS DO PARSER


#"""Regra principal: define a estrutura de um programa Pascal"""
def p_program(p):
    # Sintaxe: program -> PROGRAM ID ; declarações BEGIN statements END .
    r'program : PROGRAM ID ";" var_decls BEGIN statements opt_semicolon END "."'
    
    # Verifica se houve erros semânticos durante o parsing
    if parser.semantic_errors:
        # Junta todos os erros semânticos em uma única mensagem
        error_msg = "\n".join(parser.semantic_errors)
        parser.error = f"Erros semânticos:\n{error_msg}"
        p[0] = ""  # Programa inválido, não gera código
    else:
        # Fase 1: Inicializar variáveis simples com valores padrão
        init_code = []
        for var in parser.vars:  # Percorre lista de variáveis não-arrays
            if var in parser.symbol_table and not parser.symbol_table[var].is_array:
                idx = parser.symbol_table[var].address  # Endereço na VM
                var_type = parser.symbol_table[var].type  # Tipo da variável
                
                # Gera código de inicialização conforme o tipo
                if var_type == 'real':
                    init_code.append(f"pushf 0.0")
                    init_code.append(f"storeg {idx}")
                elif var_type == 'boolean':
                    init_code.append(f"pushi 0")
                    init_code.append(f"storeg {idx}")
                elif var_type == 'string' or var_type == 'char':
                    init_code.append(f"pushs \"\"")  # String/char inicia vazio
                    init_code.append(f"storeg {idx}")  # Armazena na posição idx
                else:  # integer ou tipo não especificado
                    init_code.append(f"pushi 0")    # Integer inicia com 0
                    init_code.append(f"storeg {idx}")  # Armazena na posição idx
        
        # Fase 2: Alocação de arrays no heap da VM
        array_alloc_code = []
        for array_info in parser.arrays:  # Percorre lista de arrays
            size = array_info['size']  # Tamanho do array (end-start+1)
            address_idx = array_info['address_idx']  # Onde guardar o ponteiro
            # Gera código: push tamanho, aloca, armazena ponteiro
            array_alloc_code.append(f"pushi {size}")
            array_alloc_code.append("allocn")
            array_alloc_code.append(f"storeg {address_idx}")
        
        # Fase 3: Código dos statements (parte executável do programa)
        # p[6] corresponde aos statements do programa
        stmt_code = p[6] if isinstance(p[6], list) else []
        
        # Fase 4: Junta todo o código VM na ordem correta:
        # 1. Inicialização de variáveis
        # 2. Alocação de arrays
        # 3. Instrução START (inicializa frame pointer)
        # 4. Código dos statements
        # 5. Instrução STOP (termina execução)
        p[0] = "\n".join(init_code + array_alloc_code + ["start"] + stmt_code + ["stop"])

def p_opt_semicolon(p):
    r'opt_semicolon : ";"'
    """Regra para ponto e vírgula opcional (com ponto e vírgula)"""
    p[0] = None  # Retorna None, indicando que há um ponto e vírgula

def p_opt_semicolon_empty(p):
    r'opt_semicolon : '
    """Regra para ponto e vírgula opcional (vazio)"""
    p[0] = None  # Retorna None, indicando que não há ponto e vírgula

def p_var_decls(p):
    r'var_decls : VAR var_decl_list'
    """Regra para declarações de variáveis (com VAR)"""
    p[0] = p[2]  # Retorna a lista de declarações de variáveis

def p_var_decls_empty(p):
    r'var_decls : '
    """Regra para declarações de variáveis (vazia - sem VAR)"""
    p[0] = []  # Retorna lista vazia

def p_var_decl_list(p):
    r'var_decl_list : var_decl_list var_decl ";"'
    """Regra para lista de declarações (múltiplas)"""
    # Concatena a lista existente (p[1]) com a nova declaração (p[2])
    p[0] = p[1] + p[2]

def p_var_decl_list_one(p):
    r'var_decl_list : var_decl ";"'
    """Regra para lista de declarações (uma única)"""
    p[0] = p[1]  # Retorna a declaração como lista (é uma lista de nomes)

def p_var_decl(p):
    r'var_decl : id_list ":" type'
    """
    Regra de declaração de variáveis: id_list ':' type
    
    Exemplos:
        x, y: integer
        vetor: array[1..10] of integer
    """
    var_names = p[1]      # Lista de nomes de variáveis (ex: ['x', 'y'])
    type_info = p[3]      # Informação do tipo (ex: 'integer' ou ('array', 1, 10, 'integer'))
    
    # Processa cada variável na lista
    for var_name in var_names:
        # Verifica se variável já foi declarada
        if var_name in parser.symbol_table:
            add_semantic_error(f"Erro: Variável '{var_name}' já declarada")
            continue  # Pula para próxima variável
        
        # Se for array (tipo_info é uma tupla começando com 'array')
        if isinstance(type_info, tuple) and type_info[0] == 'array':
            # Extrai limites do array: ('array', inicio, fim, tipo_elemento)
            array_start = int(type_info[1].value) if hasattr(type_info[1], 'value') else int(type_info[1])
            array_end = int(type_info[2].value) if hasattr(type_info[2], 'value') else int(type_info[2])
            elem_type = type_info[3]  # Tipo dos elementos do array
            size = array_end - array_start + 1  # Tamanho do array
            
            # Cria símbolo para o array
            symbol = Symbol(var_name, elem_type, parser.current_scope, 
                          is_array=True, array_start=array_start, array_end=array_end)
            symbol.address = parser.next_address  # Atribui endereço na VM
            
            # Adiciona à tabela de símbolos
            parser.symbol_table[var_name] = symbol
            
            # Guarda informação para alocação posterior na VM
            parser.arrays.append({
                'name': var_name,
                'size': size,
                'address_idx': parser.next_address
            })
            
            parser.next_address += 1  # Próximo endereço livre
            
        # Se for variável simples
        else:
            # Cria símbolo para variável simples
            symbol = Symbol(var_name, type_info, parser.current_scope)
            symbol.address = parser.next_address  # Atribui endereço na VM
            parser.symbol_table[var_name] = symbol  # Adiciona à tabela
            
            # Guarda na lista de variáveis simples (para inicialização)
            if var_name not in parser.vars:
                parser.vars.append(var_name)
                
            parser.next_address += 1  # Próximo endereço livre
    
    # Retorna lista de nomes (usado para propagação)
    p[0] = var_names

def p_id_list(p):
    r'id_list : ID "," id_list'
    """Regra para lista de identificadores com múltiplos elementos"""
    # p[1] é o primeiro ID, p[3] é a lista restante de IDs
    # Concatena o primeiro ID com a lista dos demais
    p[0] = [p[1]] + p[3]

def p_id_list_single(p):
    r'id_list : ID'
    """Regra para lista de identificadores com um único elemento"""
    # Cria uma lista contendo apenas o ID
    p[0] = [p[1]]

def p_type(p):
    r'''type : simple_type
             | array_type'''
    """Regra que define um tipo como simples ou array"""
    # Retorna o tipo (simples ou array) reconhecido
    p[0] = p[1]

def p_simple_type(p):
    r'''simple_type : INTEGER
                    | BOOLEAN
                    | REAL
                    | CHAR
                    | STRING_TYPE'''
    """Regra para tipos de dados simples do Pascal"""
    # Converte a palavra-chave para minúsculas (ex: INTEGER -> 'integer')
    p[0] = p[1].lower()

def p_array_type(p):
    r'array_type : ARRAY "[" NUM DOTDOT NUM "]" OF simple_type'
    """Regra para declaração de arrays unidimensionais"""
    # Extrai os valores numéricos dos limites do array
    start_val = int(p[3].value) if hasattr(p[3], 'value') else int(p[3])
    end_val = int(p[5].value) if hasattr(p[5], 'value') else int(p[5])
    # Retorna uma tupla: ('array', início, fim, tipo_do_elemento)
    p[0] = ('array', start_val, end_val, p[8].lower())




# STATEMENTS



#"""Regra para lista de statements vazia (ε na gramática)"""
#"""Regra para lista de statements vazia (ε na gramática)"""
def p_statements_empty(p):
    r'statements : '
    p[0] = []  # Nenhum statement, lista vazia de código

#"""Regra para lista com apenas um statement"""
def p_statements_one(p):
    r'statements : statement'
    # Se p[1] já for uma lista (código VM), usa-a; senão, lista vazia
    p[0] = p[1] if isinstance(p[1], list) else []

#"""Regra para concatenar múltiplos statements separados por ponto e vírgula"""
def p_statements_many(p):
    r'statements : statement ";" statements'
    # Combina código do statement atual (p[1]) com os seguintes (p[3])
    # NOTA: Alterei de "statements ";" statement" para "statement ";" statements"
    # Isso é recursão à DIREITA, que evita conflitos
    left = p[1] if isinstance(p[1], list) else []
    right = p[3] if isinstance(p[3], list) else []
    p[0] = left + right  # Concatena listas de instruções VM

#    """Regra geral para um statement (pode ser vários tipos)"""
def p_statement(p):
    '''statement : assignment
                 | writeln
                 | write       
                 | if_statement
                 | while_statement
                 | for_statement
                 | repeat_statement
                 | readln
                 | block'''
    # Repassa o código gerado pelo statement específico
    p[0] = p[1] if isinstance(p[1], list) else []

#    """Regra para blocos BEGIN ... END"""
def p_block(p):
    r'block : BEGIN statements opt_semicolon END'
    # Um bloco contém uma lista de statements; repassa seu código
    p[0] = p[2] if isinstance(p[2], list) else []




# REPEAT..UNTIL



# REPEAT..UNTIL



def p_repeat_statement(p):
    r'repeat_statement : REPEAT statements UNTIL expression'
    """
    Regra para REPEAT-UNTIL: REPEAT statements UNTIL expression
    """
    
    # Verificar se a expressão do UNTIL é booleana
    expr_type = get_expression_type(p, 4)
    
    if expr_type and not is_boolean_type(expr_type):
        add_semantic_error(f"Erro: Condição do UNTIL deve ser booleana, não {expr_type}", p.lineno(4))
    
    # Gerar um label único para este loop
    label = parser.label
    parser.label += 1
    
    # Obter código dos statements (corpo do repeat) e da condição
    # p[2] é a lista de statements
    stmt_code = p[2] if isinstance(p[2], list) else []
    cond_code = get_expression_code(p, 4)  # p[4] é a expressão
    
    # Gerar código VM:
    # 1. Label de início
    # 2. Código do corpo
    # 3. Código da condição
    # 4. Se condição for FALSA (0), salta para início
    p[0] = [f"repeatstart{label}:"] + stmt_code + cond_code + [f"jz repeatstart{label}"]



# ATRIBUIÇÃO COM VERIFICAÇÃO DE TIPOS MELHORADA




def p_assignment(p):
    r'assignment : ID ASSIGN expression'
    # Regra de atribuição para variáveis simples: ID := expressão
    # Exemplo: x := 10 + y
    
    var_name = p[1]  # Nome da variável (token ID)
    
    # Verificar se a variável foi declarada
    if var_name not in parser.symbol_table:
        add_semantic_error(f"Erro: Variável '{var_name}' não declarada", p.lineno(1))
        # Adiciona à lista de variáveis para inicialização (mesmo com erro)
        if var_name not in parser.vars:
            parser.vars.append(var_name)
    
    # Obter tipo da variável (se existir na tabela)
    var_type = None
    if var_name in parser.symbol_table:
        var_type = parser.symbol_table[var_name].type
    
    # Obter tipo e código VM da expressão do lado direito
    expr_type = get_expression_type(p, 3)
    expr_code = get_expression_code(p, 3)
    
    # Verificar compatibilidade de tipos entre variável e expressão
    if var_type and expr_type:
        if not check_assignment_compatibility(var_type, expr_type, var_name, p.lineno(1)):
            p[0] = []  # Em caso de erro, não gerar código
            return
    
    # Verificar se é tentativa de atribuir a um array sem índice
    if var_name in parser.symbol_table and parser.symbol_table[var_name].is_array:
        add_semantic_error(f"Erro: Não é possível atribuir diretamente a um array '{var_name}' (use índice)", p.lineno(1))
        p[0] = []
        return
    
    # Aplicar conversões implícitas necessárias
    if var_type == 'real' and expr_type == 'integer':
        # Conversão integer → real: adiciona instrução ITOF
        expr_code = expr_code + ["itof"]
    elif var_type == 'boolean' and expr_type == 'integer':
        expr_code = expr_code + ["pushi 0", "sup"]
    
    # Obter endereço da variável na VM (se declarada) ou usar 0 como fallback
    idx = parser.symbol_table[var_name].address if var_name in parser.symbol_table else 0
    
    # Gerar código: código da expressão seguido de STOREG para armazenar no endereço
    p[0] = expr_code + [f"storeg {idx}"]

def p_assignment_array_num(p):
    r'assignment : ID "[" NUM "]" ASSIGN expression'
    # Atribuição a elemento de array com índice constante (numérico)
    # Exemplo: vetor[5] := 100
    
    array_name = p[1]  # Nome do array (token ID)
    index = p[3]       # Índice numérico (token NUM)
    
    # Verificar se o array foi declarado
    if array_name not in parser.symbol_table:
        add_semantic_error(f"Erro: Array '{array_name}' não declarado", p.lineno(1))
        p[0] = []  # Não gera código
        return
    
    symbol = parser.symbol_table[array_name]
    
    # Verificar se o símbolo é realmente um array
    if not symbol.is_array:
        add_semantic_error(f"Erro: '{array_name}' não é um array", p.lineno(1))
        p[0] = []
        return
    
    # Converter o índice para valor numérico
    # p[3] pode ser um token NUM (com atributo value) ou já um número
    if hasattr(index, 'value'):
        index_val = index.value
    else:
        index_val = index
    
    # Verificar se o índice está dentro dos limites declarados do array
    # Apenas emite aviso (não erro fatal) para permitir compilação
    if index_val < symbol.array_start or index_val > symbol.array_end:
        add_semantic_error(f"Aviso: Índice {index_val} fora dos limites do array {array_name}[{symbol.array_start}..{symbol.array_end}]", p.lineno(3))
    
    # Obter tipo e código da expressão a ser atribuída
    expr_type = get_expression_type(p, 6)  # p[6] é a expressão
    expr_code = get_expression_code(p, 6)
    
    # Verificar compatibilidade entre tipo do array e tipo da expressão
    if expr_type and expr_type != symbol.type:
        if not check_assignment_compatibility(symbol.type, expr_type, f"{array_name}[{index_val}]", p.lineno(6)):
            p[0] = []  # Erro de tipo - não gera código
            return
    
    # Calcular offset: converter índice Pascal (ex: 1..10) para base 0 da VM
    # Exemplo: array[1..10], índice 5 -> offset = 5-1 = 4
    offset = index_val - symbol.array_start
    
    # Gerar código VM para atribuição a array com índice constante:
    # 1. pushg: empilha endereço base do array (armazenado em symbol.address)
    # 2. pushi: empilha offset calculado
    # 3. padd: calcula endereço do elemento (endereço_base + offset)
    # 4. expr_code: código que calcula o valor a ser armazenado
    # 5. swap: corrige ordem (store espera valor no topo, endereço abaixo)
    # 6. store 0: armazena valor no endereço calculado
    p[0] = [
        f"pushg {symbol.address}",  # Endereço base do array
        f"pushi {offset}",           # Offset (índice convertido para base 0)
        "padd",                      # Calcula endereço do elemento
    ] + expr_code + [                # Código que calcula o valor
        "store 0"                    # Armazena valor no endereço
    ]

def p_assignment_array_var(p):
    r'assignment : ID "[" ID "]" ASSIGN expression'

    """
    Regra para atribuição a elemento de array com índice variável.
    Exemplo: vetor[i] := expressão
    """

    # p[1] = nome do array, p[3] = nome da variável índice
    array_name = p[1]
    index_var = p[3]
    
    # Verificar se o array foi declarado
    if array_name not in parser.symbol_table:
        add_semantic_error(f"Erro: Array '{array_name}' não declarado", p.lineno(1))
        p[0] = []
        return
    
    symbol = parser.symbol_table[array_name]
    
    # Verificar se é realmente um array
    if not symbol.is_array:
        add_semantic_error(f"Erro: '{array_name}' não é um array", p.lineno(1))
        p[0] = []
        return
    
    # Verificar se a variável índice foi declarada
    if index_var not in parser.symbol_table:
        add_semantic_error(f"Erro: Índice '{index_var}' não declarado", p.lineno(3))
        p[0] = []
        return
    
    index_symbol = parser.symbol_table[index_var]
    
    # Verificar tipo do índice (deve ser integer)
    if index_symbol.type != 'integer':
        add_semantic_error(f"Erro: Índice do array deve ser integer, não {index_symbol.type}", p.lineno(3))
    
    # Obter tipo e código da expressão do lado direito (p[6])
    expr_type = get_expression_type(p, 6)
    expr_code = get_expression_code(p, 6)
    
    # Verificar compatibilidade entre tipo do array e tipo da expressão
    if expr_type and expr_type != symbol.type:
        if not check_assignment_compatibility(symbol.type, expr_type, f"{array_name}[{index_var}]", p.lineno(6)):
            p[0] = []
            return
    
    # Gerar código VM para atribuição a array com índice variável
    p[0] = [
        f"pushg {symbol.address}",      # Empilha endereço base do array (alocado no heap)
        f"pushg {index_symbol.address}", # Empilha valor do índice (variável)
        f"pushi {symbol.array_start}",   # Empilha início do array
        "sub",                           # Subtrai: índice - array_start (converte para base 0)
        "padd",                          # Soma ao endereço base: endereço do elemento
    ] + expr_code + [                    # Adiciona código da expressão (valor a armazenar)
        "store 0"                        # Armazena valor no endereço calculado
    ]


# WRITELN



def p_writeln(p):
    r'writeln : WRITELN "(" writeln_args ")"'
    args_code = p[3] if isinstance(p[3], list) else []
    p[0] = args_code + ["writeln"]  # Código dos argumentos + writeln

# E adicione esta nova regra:
def p_writeln_empty(p):
    r'writeln : WRITELN'
    p[0] = ["writeln"]

def p_writeln_args_one(p):
    r'writeln_args : writeln_arg'
    # Regra para um único argumento em WRITELN
    # Retorna o código desse argumento diretamente
    p[0] = p[1] if isinstance(p[1], list) else []

def p_writeln_args_many(p):
    r'writeln_args : writeln_args "," writeln_arg'
    # Regra para múltiplos argumentos em WRITELN (separados por vírgula)
    # Concatena código dos argumentos anteriores com o novo argumento
    left = p[1] if isinstance(p[1], list) else []
    right = p[3] if isinstance(p[3], list) else []
    p[0] = left + right

def p_writeln_arg_string(p):
    r'writeln_arg : STRING'
    # Processa argumento do tipo string literal em WRITELN
    # Gera código para empilhar a string e escrevê-la
    p[0] = [f'pushs "{p[1]}"', 'writes']

def p_writeln_arg_expression(p):
    r'writeln_arg : expression'
    # Processa argumento que é uma expressão em WRITELN
    # O tipo da expressão determina a instrução de escrita apropriada
    
    # Obtém código e tipo da expressão
    expr_code = get_expression_code(p, 1)
    expr_type = get_expression_type(p, 1)
    
    # Escolhe instrução de escrita baseada no tipo
    if expr_type == 'real':
        # Para reais: usa WRITEF
        p[0] = expr_code + ["writef"]
    elif expr_type == 'boolean':
        # Para booleanos: converte para string "true" ou "false"
        label = parser.label
        parser.label += 1
        p[0] = expr_code + [
            f"jz boolfalse{label}",  # Salta se falso
            f'pushs "true"',         # Empilha "true"
            f"jump boolend{label}",  # Salta para o fim
            f"boolfalse{label}:",    # Label para falso
            f'pushs "false"',        # Empilha "false"
            f"boolend{label}:",      # Label do fim
            "writes"                 # Escreve a string
        ]
    elif expr_type == 'string' or expr_type == 'char':
        # Para strings e chars: usa WRITES
        p[0] = expr_code + ["writes"]
    else:
        # Para inteiros (default): usa WRITEI
        p[0] = expr_code + ["writei"]


def p_write(p):
    r'write : WRITE "(" writeln_args ")"'
    args_code = p[3] if isinstance(p[3], list) else []
    p[0] = args_code  # Apenas escreve, não pula linha

# Se quiser write sem argumentos (menos comum, mas válido):
def p_write_empty(p):
    r'write : WRITE'
    p[0] = []  # write sem argumentos não faz nada




# READLN




def p_readln(p):
    r'readln : READLN "(" ID ")"'
    """
    Regra para leitura de variável simples: readln(var)
    Exemplo: readln(x)
    """
    # Obtém o nome da variável (p[3] contém o ID entre parênteses)
    var_name = p[3]
    
    # Verifica se a variável foi declarada
    if var_name not in parser.symbol_table:
        add_semantic_error(f"Erro: Variável '{var_name}' não declarada", p.lineno(3))
        p[0] = []  # Não gera código se houver erro
        return
    
    # Obtém o símbolo da tabela de símbolos
    symbol = parser.symbol_table[var_name]
    
    # Adiciona a variável à lista de variáveis (para inicialização, se não estiver)
    if var_name not in parser.vars:
        parser.vars.append(var_name)
    
    # Endereço da variável na VM
    idx = symbol.address
    
    # Gera código VM conforme o tipo da variável:
    # 1. Mostra prompt "? "
    # 2. Lê string do teclado (READ)
    # 3. Converte para o tipo adequado (ATOI para inteiros, ATOF para reais)
    # 4. Armazena no endereço da variável (STOREG)
    if symbol.type == 'real':
        p[0] = [f'pushs "? "', 'writes', 'read', 'atof', f'storeg {idx}']
    elif symbol.type == 'integer':
        p[0] = [f'pushs "? "', 'writes', 'read', 'atoi', f'storeg {idx}']
    elif symbol.type == 'boolean':
        # Para booleanos, lê inteiro (0 ou 1)
        p[0] = [f'pushs "? "', 'writes', 'read', 'atoi', f'storeg {idx}']
    else:
        # Para char e string: lê string sem conversão
        p[0] = [f'pushs "? "', 'writes', 'read', f'storeg {idx}']

def p_readln_array_var(p):
    r'readln : READLN "(" ID "[" ID "]" ")"'
    """
    Regra para leitura de elemento de array: readln(array[index])
    Exemplo: readln(vetor[i])
    """
    # Obtém o nome do array (p[3]) e da variável índice (p[5])
    array_name = p[3]
    index_var = p[5]
    
    # Verifica se o array foi declarado
    if array_name not in parser.symbol_table:
        add_semantic_error(f"Erro: Array '{array_name}' não declarado", p.lineno(3))
        p[0] = []
        return
    
    symbol = parser.symbol_table[array_name]
    
    # Verifica se o símbolo é realmente um array
    if not symbol.is_array:
        add_semantic_error(f"Erro: '{array_name}' não é um array", p.lineno(3))
        p[0] = []
        return
    
    # Verifica se a variável índice foi declarada
    if index_var not in parser.symbol_table:
        add_semantic_error(f"Erro: Índice '{index_var}' não declarado", p.lineno(5))
        p[0] = []
        return
    
    index_symbol = parser.symbol_table[index_var]
    
    # Gera código VM para ler elemento de array com índice variável:
    # 1. Prompt e leitura de string
    # 2. Conversão para inteiro (ATOI) - assume-se que o array é de inteiros
    # 3. Calcula endereço do elemento: pushg (endereço base) + índice - início
    # 4. Troca (SWAP) porque STORE espera valor no topo e endereço abaixo
    # 5. Armazena (STORE 0)
    p[0] = [
        f"pushg {symbol.address}",      # Endereço base
        f"pushg {index_symbol.address}", # Valor do índice
        f"pushi {symbol.array_start}",   # Início do array
        "sub",                           # índice - início (base 0)
        "padd",                          # Endereço calculado (TOP)
        f'pushs "? "', 'writes', 'read', 'atoi',  # Valor lido (abaixo do endereço)
        "store 0"                        # Armazena (valor, endereço) - valor no topo
    ]


# ADICIONAR APÓS a função p_readln_array_var (por volta da linha 550)

def p_readln_array_num(p):
    r'readln : READLN "(" ID "[" NUM "]" ")"'
    """
    Regra para leitura com índice constante: readln(array[5])
    Exemplo: readln(numeros[2])
    """
    array_name = p[3]
    index_num = p[5]
    
    if array_name not in parser.symbol_table:
        add_semantic_error(f"Erro: Array '{array_name}' não declarado", p.lineno(3))
        p[0] = []
        return
    
    symbol = parser.symbol_table[array_name]
    
    if not symbol.is_array:
        add_semantic_error(f"Erro: '{array_name}' não é um array", p.lineno(3))
        p[0] = []
        return
    
    # Converter índice para número
    if hasattr(index_num, 'value'):
        index_val = index_num.value
    else:
        index_val = index_num
    
    # Verificar limites
    if index_val < symbol.array_start or index_val > symbol.array_end:
        add_semantic_error(f"Aviso: Índice {index_val} fora dos limites", p.lineno(5))
    
    # Calcular offset
    offset = index_val - symbol.array_start
    
    # Gerar código para índice CONSTANTE
    p[0] = [
        f"pushg {symbol.address}",      # Endereço base
        f"pushi {offset}",               # Offset constante
        "padd",                          # Endereço calculado (TOP)
        f'pushs "? "', 'writes', 'read', 'atoi',  # Valor lido (abaixo)
        "store 0"                        # Armazena
    ]




# IF-THEN-ELSE



def p_if_statement(p):
    r'if_statement : IF expression THEN statement ELSE statement'
    
    """
    Regra para IF com ELSE: IF expressão THEN statement ELSE statement
    Gera código VM com labels para salto condicional
    """

    # Verificar se a expressão da condição é booleana
    expr_type = get_expression_type(p, 2)
    if expr_type and not is_boolean_type(expr_type):
        add_semantic_error(f"Erro: Condição do IF deve ser booleana, não {expr_type}", p.lineno(2))
    
    # Criar labels únicos para esta estrutura
    label = parser.label
    parser.label += 1
    
    # Obter código da condição, bloco THEN e bloco ELSE
    cond_code = get_expression_code(p, 2)
    then_code = p[4] if isinstance(p[4], list) else []
    else_code = p[6] if isinstance(p[6], list) else []
    
    # Gerar código VM:
    # 1. Avaliar condição
    # 2. Se falsa (0), saltar para ELSE (JZ)
    # 3. Código THEN
    # 4. Saltar para fim (JUMP)
    # 5. Label ELSE
    # 6. Código ELSE
    # 7. Label fim
    p[0] = cond_code + [f"jz else{label}"] + then_code + \
           [f"jump endif{label}", f"else{label}:"] + else_code + [f"endif{label}:"]


def p_if_statement_no_else(p):
    r'if_statement : IF expression THEN statement'
    
    """
    Regra para IF sem ELSE: IF expressão THEN statement
    Gera código VM mais simples sem bloco ELSE
    """

    # Verificar se a expressão da condição é booleana
    expr_type = get_expression_type(p, 2)
    if expr_type and not is_boolean_type(expr_type):
        add_semantic_error(f"Erro: Condição do IF deve ser booleana, não {expr_type}", p.lineno(2))
    
    # Criar label único para esta estrutura
    label = parser.label
    parser.label += 1
    
    # Obter código da condição e bloco THEN
    cond_code = get_expression_code(p, 2)
    then_code = p[4] if isinstance(p[4], list) else []
    
    # Gerar código VM:
    # 1. Avaliar condição
    # 2. Se falsa (0), saltar para depois do THEN (JZ)
    # 3. Código THEN
    # 4. Label fim
    p[0] = cond_code + [f"jz endif{label}"] + then_code + [f"endif{label}:"]




# WHILE



def p_while_statement(p):
    r'while_statement : WHILE expression DO statement'
    """Regra para a estrutura WHILE-DO do Pascal"""
    
    # Verificar se a expressão da condição é do tipo booleano
    expr_type = get_expression_type(p, 2)
    if expr_type and not is_boolean_type(expr_type):
        add_semantic_error(f"Erro: Condição do WHILE deve ser booleana, não {expr_type}", p.lineno(2))
    
    # Gerar labels únicos para este while
    label = parser.label
    parser.label += 1
    
    # Obter código da condição e do corpo do while
    cond_code = get_expression_code(p, 2)  # p[2] é a expressão
    stmt_code = p[4] if isinstance(p[4], list) else []  # p[4] é o statement
    
    # Gerar código VM para while:
    # 1. Label do início do loop
    # 2. Código da condição (resultado booleano no topo da pilha)
    # 3. JZ salta para o final se condição for falsa (0)
    # 4. Código do corpo do loop
    # 5. JUMP de volta ao início
    # 6. Label do final do loop
    p[0] = [f"while{label}:"] + cond_code + [f"jz endwhile{label}"] + \
           stmt_code + [f"jump while{label}", f"endwhile{label}:"]

# FOR


def p_for_statement(p):
    '''for_statement : FOR ID ASSIGN expression TO expression DO statement
                     | FOR ID ASSIGN expression DOWNTO expression DO statement'''
    # Regra para declaração FOR com duas variantes: TO (incremento) e DOWNTO (decremento)
    
    # Obtém o nome da variável de controle do loop (p[2] é o ID após FOR)
    var_name = p[2]
    
    # Verifica se a variável de controle foi declarada
    if var_name not in parser.symbol_table:
        add_semantic_error(f"Erro: Variável '{var_name}' não declarada", p.lineno(2))
        p[0] = []  # Retorna lista vazia para indicar erro
        return
    
    # Verifica se a variável de controle é do tipo integer (exigência do Pascal)
    var_type = parser.symbol_table[var_name].type if var_name in parser.symbol_table else None
    if var_type and var_type != 'integer':
        add_semantic_error(f"Erro: Variável de controle do FOR deve ser integer, não {var_type}", p.lineno(2))
    
    # Verifica o tipo da expressão inicial (deve ser integer)
    start_type = get_expression_type(p, 4)
    if start_type and start_type != 'integer':
        add_semantic_error(f"Erro: Valor inicial do FOR deve ser integer, não {start_type}", p.lineno(4))
    
    # Verifica o tipo da expressão final (deve ser integer)
    end_type = get_expression_type(p, 6)
    if end_type and end_type != 'integer':
        add_semantic_error(f"Erro: Valor final do FOR deve ser integer, não {end_type}", p.lineno(6))
    
    # Obtém o endereço da variável de controle na VM
    idx = parser.symbol_table[var_name].address
    # Determina a direção do loop: 'to' (crescente) ou 'downto' (decrescente)
    direction = p[5]
    
    # Cria um label único para este loop FOR
    label = parser.label
    parser.label += 1  # Incrementa o contador global de labels
    
    # Obtém o código VM para as expressões inicial e final
    init_expr = get_expression_code(p, 4)  # Código para expressão inicial
    end_expr = get_expression_code(p, 6)   # Código para expressão final
    # Obtém o código do corpo do loop (statement)
    body_code = p[8] if isinstance(p[8], list) else []
    
    # Geração de código para FOR TO (incremento)
    if direction == 'to':
        p[0] = (
            init_expr + [f"storeg {idx}",        # Armazena valor inicial na variável
            f"forstart{label}:",                 # Label início do loop
            f"pushg {idx}"] + end_expr + ["infeq",  # Carrega variável e expressão final, compara <=
            f"jz forend{label}"]                # Se falso, salta para fora do loop
            + body_code                          # Código do corpo do loop
            + [f"pushg {idx}", "pushi 1", "add", # Incrementa a variável em 1
            f"storeg {idx}",                    # Armazena novo valor
            f"jump forstart{label}",             # Volta para início do loop
            f"forend{label}:"]                   # Label final do loop
        )
    # Geração de código para FOR DOWNTO (decremento)
    else:  # downto
        p[0] = (
            init_expr + [f"storeg {idx}",        # Armazena valor inicial na variável
            f"forstart{label}:",                 # Label início do loop
            f"pushg {idx}"] + end_expr + ["supeq",  # Carrega variável e expressão final, compara >=
            f"jz forend{label}"]                # Se falso, salta para fora do loop
            + body_code                          # Código do corpo do loop
            + [f"pushg {idx}", "pushi 1", "sub", # Decrementa a variável em 1
            f"storeg {idx}",                    # Armazena novo valor
            f"jump forstart{label}",             # Volta para início do loop
            f"forend{label}:"]                   # Label final do loop
        )



# EXPRESSÕES COM VERIFICAÇÃO DE TIPOS MELHORADA




# Regra para expressões no nível mais alto (apenas redireciona)
def p_expression(p):
    '''expression : logical_or_expression'''
    p[0] = p[1]  # Passa o resultado da expressão OR para cima


# Regra para expressões OR (||) com verificação de tipos
def p_logical_or_expression(p):
    '''logical_or_expression : logical_and_expression
                             | logical_or_expression OR logical_and_expression'''
    if len(p) == 2:
        # Caso simples: apenas uma expressão AND
        p[0] = p[1]
    else:
        # Caso OR: expr1 OR expr2
        # Obter tipos dos operandos
        left_type = get_expression_type(p, 1)
        right_type = get_expression_type(p, 3)
        
        # Verificar se ambos são booleanos
        if not check_operation_compatibility('or', left_type, right_type, p.lineno(2)):
            # Se erro, criar expressão boolean vazia
            p[0] = create_typed_expression('boolean', [])
            return
        
        # Obter códigos VM dos operandos
        left_code = get_expression_code(p, 1)
        right_code = get_expression_code(p, 3)
        
        # Gerar código: eval(left), eval(right), OR
        p[0] = create_typed_expression('boolean', left_code + right_code + ["or"])


# Regra para expressões AND (&&) com verificação de tipos
def p_logical_and_expression(p):
    '''logical_and_expression : relational_expression
                              | logical_and_expression AND relational_expression'''
    if len(p) == 2:
        # Caso simples: apenas uma expressão relacional
        p[0] = p[1]
    else:
        # Caso AND: expr1 AND expr2
        # Obter tipos dos operandos
        left_type = get_expression_type(p, 1)
        right_type = get_expression_type(p, 3)
        
        # Verificar se ambos são booleanos
        if not check_operation_compatibility('and', left_type, right_type, p.lineno(2)):
            # Se erro, criar expressão boolean vazia
            p[0] = create_typed_expression('boolean', [])
            return
        
        # Obter códigos VM dos operandos
        left_code = get_expression_code(p, 1)
        right_code = get_expression_code(p, 3)
        
        # Gerar código: eval(left), eval(right), AND
        p[0] = create_typed_expression('boolean', left_code + right_code + ["and"])


# Regra para expressões relacionais (<, >, <=, >=, =, <>)
def p_relational_expression(p):
    '''relational_expression : simple_expression
                            | simple_expression RELOP simple_expression'''
    if len(p) == 2:
        # Caso simples: apenas uma expressão simples
        p[0] = p[1]
    else:
        # Caso relação: expr1 RELOP expr2
        # Obter tipos dos operandos
        left_type = get_expression_type(p, 1)
        right_type = get_expression_type(p, 3)
        
        # Verificar compatibilidade dos tipos para o operador
        if not check_operation_compatibility(p[2], left_type, right_type, p.lineno(2)):
            # Se erro, criar expressão boolean vazia
            p[0] = create_typed_expression('boolean', [])
            return
        
        # Obter códigos VM dos operandos
        left_code = get_expression_code(p, 1)
        right_code = get_expression_code(p, 3)
        
        # Converter integer para real se necessário (promoção de tipo)
        if left_type == 'integer' and right_type == 'real':
            left_code = left_code + ["itof"]  # Converte left para real
            left_type = 'real'
        elif left_type == 'real' and right_type == 'integer':
            right_code = right_code + ["itof"]  # Converte right para real
            right_type = 'real'
        
        op = p[2]  # Operador relacional (<, >, <=, >=, =, <>)
        
        # Escolher operador VM correto baseado nos tipos (inteiro ou real)
        if left_type == 'real' or right_type == 'real':
            # Usar operadores de ponto flutuante
            if op == '<': vm_op = "finf"
            elif op == '>': vm_op = "fsup"
            elif op == '<=': vm_op = "finfeq"
            elif op == '>=': vm_op = "fsupeq"
            elif op == '=': vm_op = "equal"
            elif op == '<>': vm_op = "equal" + "\n" + "not"  # equal seguido de not
            else: vm_op = "error"
        else:
            # Usar operadores inteiros
            if op == '<': vm_op = "inf"
            elif op == '>': vm_op = "sup"
            elif op == '<=': vm_op = "infeq"
            elif op == '>=': vm_op = "supeq"
            elif op == '=': vm_op = "equal"
            elif op == '<>': vm_op = "equal" + "\n" + "not"  # equal seguido de not
            else: vm_op = "error"
        
        # Gerar código: eval(left), eval(right), operador relacional
        p[0] = create_typed_expression('boolean', left_code + right_code + [vm_op])

def p_simple_expression(p):
    '''simple_expression : term
                        | simple_expression ADDOP term
                        | ADDOP term'''
    # Caso 1: expressão simples é apenas um termo (ex: 5, x, 3.14)
    if len(p) == 2:
        p[0] = p[1]
    
    # Caso 2: operador unário (+ ou -) aplicado a um termo (ex: -5, +x)
    elif len(p) == 3:  
        # Obter tipo do termo (p[2] é o termo, p[1] é o operador unário)
        term_type = get_expression_type(p, 2)
        
        # Verificar se operador unário '-' está sendo aplicado a tipo não numérico
        if p[1] == '-':
            if term_type and not is_numeric_type(term_type):
                add_semantic_error(f"Erro: Operador unário '-' requer operando numérico, não {term_type}", p.lineno(1))
        
        # Obter código do termo
        term_code = get_expression_code(p, 2)
        
        # Se for operador unário negativo: gerar código para 0 - termo
        if p[1] == '-':
            if term_type == 'real':
                # Para real: 0.0 - termo_real
                p[0] = create_typed_expression(term_type, [f"pushf 0.0"] + term_code + ["fsub"])
            else:
                # Para inteiro: 0 - termo_inteiro
                p[0] = create_typed_expression(term_type, [f"pushi 0"] + term_code + ["sub"])
        else:
            # Operador unário positivo: não faz nada, mantém o termo
            p[0] = p[2]
    
    # Caso 3: operação binária (adição ou subtração) entre duas expressões
    else:
        # Obter tipos das expressões esquerda e direita
        left_type = get_expression_type(p, 1)
        right_type = get_expression_type(p, 3)
        
        # Verificar se é concatenação de strings (operador + com strings/chars)
        if p[2] == '+' and is_string_or_char_type(left_type) and is_string_or_char_type(right_type):
            # Concatenação de strings: gera código para concatenar
            left_code = get_expression_code(p, 1)
            right_code = get_expression_code(p, 3)
            p[0] = create_typed_expression('string', left_code + right_code + ["concat"])
            return
        
        # Verificar compatibilidade da operação (se não for concatenação)
        if not check_operation_compatibility(p[2], left_type, right_type, p.lineno(2)):
            # Se houver erro, cria expressão vazia do tipo integer (default)
            p[0] = create_typed_expression('integer', [])
            return
        
        # Determinar tipo resultante da operação
        result_type = 'integer'
        if left_type == 'real' or right_type == 'real':
            result_type = 'real'
        
        # Obter códigos das expressões esquerda e direita
        left_code = get_expression_code(p, 1)
        right_code = get_expression_code(p, 3)
        
        # Converter inteiros para reais se necessário (para operações com reais)
        if result_type == 'real':
            if left_type == 'integer':
                left_code = left_code + ["itof"]  # Converte inteiro para real
            if right_type == 'integer':
                right_code = right_code + ["itof"]  # Converte inteiro para real
        
        # Obter a operação VM correta (ADD/FADD, SUB/FSUB, etc.)
        vm_op = get_vm_operation(p[2], left_type, right_type)
        
        # Criar expressão resultante com tipo e código VM
        p[0] = create_typed_expression(result_type, left_code + right_code + [vm_op])

def p_term(p):
    '''term : factor
            | term MULOP factor
            | term DIV factor
            | term MOD factor'''
    
    # Caso 1: term -> factor (apenas um fator)
    if len(p) == 2:
        p[0] = p[1]
    # Caso 2: term -> term operador factor (operação binária)
    else:
        # Obter tipos dos operandos
        left_type = get_expression_type(p, 1)
        right_type = get_expression_type(p, 3)
        
        # Verificar compatibilidade dos tipos para a operação
        if not check_operation_compatibility(p[2], left_type, right_type, p.lineno(2)):
            # Se erro, retorna expressão com tipo integer padrão e código vazio
            p[0] = create_typed_expression('integer', [])
            return
        
        # Determinar tipo resultante da operação
        result_type = 'integer'
        # Divisão normal (/) sempre resulta em real
        if p[2] == '/':
            result_type = 'real'
        # Se qualquer operando for real, resultado é real
        elif left_type == 'real' or right_type == 'real':
            result_type = 'real'
        
        # Obter código VM dos operandos
        left_code = get_expression_code(p, 1)
        right_code = get_expression_code(p, 3)
        
        # Converter operandos integer para real se necessário
        if result_type == 'real':
            if left_type == 'integer':
                left_code = left_code + ["itof"]  # Converter left para float
            if right_type == 'integer':
                right_code = right_code + ["itof"]  # Converter right para float
        
        # Escolher instrução VM correta baseada no operador e tipo
        if p[2] == '*':
            vm_op = 'fmul' if result_type == 'real' else 'mul'
        elif p[2] == '/':
            vm_op = 'fdiv' if result_type == 'real' else 'div'
        elif p[2] == 'div':
            vm_op = 'div'  # div é sempre divisão inteira
        elif p[2] == 'mod':
            vm_op = 'mod'  # mod é sempre módulo inteiro
        
        # Retornar expressão tipada com código concatenado
        p[0] = create_typed_expression(result_type, left_code + right_code + [vm_op])



# REGRAS DE FACTOR COM SUPORTE PARA LENGTH()



def p_factor_string(p):
    r'factor : STRING'
    # String como factor: converte para pushs "texto" com tipo string
    p[0] = create_typed_expression('string', [f'pushs "{p[1]}"'])

def p_factor_charlit(p):
    r'factor : CHARLIT'
    # CHAR literal: um único caractere
    # Na VM, tratamos como string de 1 caractere
    p[0] = create_typed_expression('char', [f'pushs "{p[1]}"'])

def p_factor_id(p):
    r'factor : ID'
    # Variável como factor: verifica declaração e gera pushg endereço
    var_name = p[1]
    if var_name not in parser.symbol_table:
        # Erro: variável não declarada, usa valor padrão 0
        add_semantic_error(f"Erro: Variável '{var_name}' não declarada", p.lineno(1))
        p[0] = create_typed_expression('integer', [f"pushi 0"])
        return
    
    symbol = parser.symbol_table[var_name]
    
    if symbol.is_array:
        # Erro: array usado como variável simples
        add_semantic_error(f"Erro: '{var_name}' é um array, não pode ser usado como valor simples", p.lineno(1))
        p[0] = create_typed_expression('integer', [f"pushi 0"])
        return
    
    # Variável válida: gera pushg endereço
    idx = symbol.address
    p[0] = create_typed_expression(symbol.type, [f"pushg {idx}"])

def p_factor_num(p):
    r'factor : NUM'
    # Número como factor: determina se é integer ou real e gera push correspondente
    if isinstance(p[1], float):
        p[0] = create_typed_expression('real', [f"pushf {p[1]}"])
    else:
        p[0] = create_typed_expression('integer', [f"pushi {p[1]}"])

def p_factor_paren(p):
    r'factor : "(" expression ")"'
    # Parênteses: retorna a expressão interna sem modificação
    p[0] = p[2]

def p_factor_not(p):
    r'factor : NOT factor'
    # Operador NOT: aplica negação booleana
    factor_type = get_expression_type(p, 2)
    
    if factor_type and not is_boolean_type(factor_type):
        # Verifica se o operando é booleano
        add_semantic_error(f"Erro: Operador NOT requer operando booleano, não {factor_type}", p.lineno(1))
    
    factor_code = get_expression_code(p, 2)
    p[0] = create_typed_expression('boolean', factor_code + ["not"])

def p_factor_true(p):
    r'factor : TRUE'
    # Valor booleano TRUE: representa como 1
    p[0] = create_typed_expression('boolean', [f"pushi 1"])

def p_factor_false(p):
    r'factor : FALSE'
    # Valor booleano FALSE: representa como 0
    p[0] = create_typed_expression('boolean', [f"pushi 0"])




# NOVA REGRA: função length()

# Função para processar a função intrínseca LENGTH(expressão)
# Retorna o comprimento de uma string ou char como integer
def p_factor_length(p):
    r'factor : LENGTH "(" expression ")"'
    # Verificar se o argumento é string ou char
    arg_type = get_expression_type(p, 3)
    
    # Validar tipo: length só funciona com string ou char
    if arg_type and not is_string_or_char_type(arg_type):
        add_semantic_error(f"Erro: Função 'length' requer argumento do tipo string ou char, não {arg_type}", p.lineno(1))
        # Retorna expressão com tipo integer e código vazio (erro)
        p[0] = create_typed_expression('integer', [])
        return
    
    # Obter código da expressão do argumento
    arg_code = get_expression_code(p, 3)
    # A VM tem a instrução STRLEN que retorna o comprimento da string
    # Cria expressão tipada: tipo integer, código = código do argumento + strlen
    p[0] = create_typed_expression('integer', arg_code + ["strlen"])


# Função para acesso a array com índice constante (número)
# Exemplo: vetor[5] (onde 5 é constante)
def p_factor_array_num(p):
    r'factor : ID "[" NUM "]"'
    array_name = p[1]    # Nome do array (ID)
    index = p[3]         # Índice constante (NUM)
    
    # Verificar se array foi declarado
    if array_name not in parser.symbol_table:
        add_semantic_error(f"Erro: Array '{array_name}' não declarado", p.lineno(1))
        # Retorna valor default (0) em caso de erro
        p[0] = create_typed_expression('integer', [f"pushi 0"])
        return
    
    # Obter símbolo do array da tabela
    symbol = parser.symbol_table[array_name]
    
    # Verificar se realmente é um array
    if not symbol.is_array:
        add_semantic_error(f"Erro: '{array_name}' não é um array", p.lineno(1))
        p[0] = create_typed_expression('integer', [f"pushi 0"])
        return
    
    # Converter índice para número inteiro
    # p[3] pode ser token NUM (com atributo value) ou já ser int
    if hasattr(index, 'value'):
        index_val = index.value
    else:
        index_val = index
    
    # Verificar se índice está dentro dos limites declarados (apenas warning)
    if index_val < symbol.array_start or index_val > symbol.array_end:
        add_semantic_error(f"Aviso: Índice {index_val} fora dos limites do array {array_name}[{symbol.array_start}..{symbol.array_end}]", p.lineno(3))
    
    # Calcular offset: converter índice Pascal (base 1) para base 0 da VM
    offset = index_val - symbol.array_start
    
    # Gerar código VM para acessar array com índice constante:
    # 1. pushg address: empilha endereço base do array
    # 2. pushi offset: empilha offset calculado
    # 3. padd: calcula endereço do elemento (base + offset)
    # 4. load 0: carrega valor do endereço calculado
    p[0] = create_typed_expression(symbol.type, [
        f"pushg {symbol.address}",
        f"pushi {offset}",
        "padd",
        "load 0"
    ])

def p_factor_array_var(p):
    # Regra para acesso a elemento de array com índice variável: arr[i]
    # Reconhece expressões como: vetor[indice], lista[pos]
    r'factor : ID "[" ID "]"'
    
    # Extrair nome do array (primeiro ID) e nome da variável índice (segundo ID)
    array_name = p[1]
    index_var = p[3]
    
    # Verificar se o array foi declarado
    if array_name not in parser.symbol_table:
        add_semantic_error(f"Erro: Array '{array_name}' não declarado", p.lineno(1))
        # Retorna expressão tipada com valor padrão 0 (integer) em caso de erro
        p[0] = create_typed_expression('integer', [f"pushi 0"])
        return
    
    # Obter símbolo do array da tabela
    symbol = parser.symbol_table[array_name]
    
    # Verificar se realmente é um array
    if not symbol.is_array:
        add_semantic_error(f"Erro: '{array_name}' não é um array", p.lineno(1))
        p[0] = create_typed_expression('integer', [f"pushi 0"])
        return
    
    # Verificar se a variável índice foi declarada
    if index_var not in parser.symbol_table:
        add_semantic_error(f"Erro: Índice '{index_var}' não declarado", p.lineno(3))
        p[0] = create_typed_expression('integer', [f"pushi 0"])
        return
    
    # Obter símbolo da variável índice
    index_symbol = parser.symbol_table[index_var]
    
    # Verificar se o índice é do tipo integer (requisito do Pascal)
    if index_symbol.type != 'integer':
        add_semantic_error(f"Erro: Índice do array deve ser integer, não {index_symbol.type}", p.lineno(3))
        # Continua mesmo com erro, mas gera código com valor 0
        # (poderia retornar aqui se quisesse parar completamente)
    
    # Gerar código VM para acesso a array com índice variável:
    # 1. pushg {symbol.address}    - empilha endereço base do array
    # 2. pushg {index_symbol.address} - empilha valor do índice
    # 3. pushi {symbol.array_start} - empilha início do array
    # 4. sub                         - converte índice para base 0
    # 5. padd                        - calcula endereço do elemento
    # 6. load 0                      - carrega valor da posição calculada
    
    p[0] = create_typed_expression(symbol.type, [
        f"pushg {symbol.address}",
        f"pushg {index_symbol.address}",
        f"pushi {symbol.array_start}",
        "sub",  # índice - array_start (converte para base 0)
        "padd",
        "load 0"
    ])

"""Regras para operadores relacionais: <, >, <=, >=, =, <>"""
def p_relop(p):
    r'''RELOP : "<"
              | ">"
              | LE
              | GE
              | "="
              | NE'''
    p[0] = p[1] # Retorna o próprio operador

"""Regras para operadores aditivos: + e -"""
def p_addop(p):
    r'''ADDOP : "+"
              | "-"'''
    p[0] = p[1] # Retorna o próprio operador

"""Regras para operadores multiplicativos: * e /"""
def p_mulop(p):
    r'''MULOP : "*"
              | "/"'''
    p[0] = p[1] # Retorna o próprio operador

"""Função de tratamento de erros do parser (PLY)"""
def p_error(p):
    if p:
        # Erro com token específico: mostra token, tipo e linha
        parser.error = f"Erro de sintaxe no token '{p.value}' (tipo: {p.type}) na linha {p.lineno}"
    else:
        # Erro no final do arquivo (ex: programa incompleto)
        parser.error = "Erro de sintaxe no final do arquivo"

# FORÇAR REGENERAÇÃO DAS TABELAS SEM CACHE
parser = yacc.yacc(debug=False, write_tables=False, errorlog=yacc.NullLogger())