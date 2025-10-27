import ply.lex as lex

tokens = ('INT', 'SUM', 'SUB', 'MUL', 'DIV', 'PA', 'PF')

t_SUM = r'\+'
t_SUB = r'-'
t_MUL = r'\*'
t_DIV = r'/'
t_PA = r'\('
t_PF = r'\)'
t_INT = r'\d+'

t_ignore = ' \t'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Carácter desconhecido: {t.value[0]}")
    t.lexer.skip(1)

lexer = lex.lex()
