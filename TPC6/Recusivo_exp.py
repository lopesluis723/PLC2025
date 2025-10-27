from lexer import lexer
import re

prox_symb = None  # símbolo atual

def processa_terminal(tipo):
    global prox_symb
    if prox_symb and prox_symb.type == tipo:
        print(f"Consome {tipo}: {prox_symb.value}")
        prox_symb = lexer.token()
    else:
        raise ValueError(f"Erro: esperava {tipo}, mas encontrei {prox_symb.type if prox_symb else 'EOF'}")


# Gramática:
# Exp  -> Term Exp2
# Exp2 -> (+|-) Term Exp2 | ε
# Term -> Factor Term2
# Term2-> (*|/) Factor Term2 | ε
# Factor -> INT | ( Exp )

def rec_Exp():
    print("Regra Exp: Term Exp2")
    rec_Term()
    rec_Exp2()

def rec_Exp2():
    global prox_symb
    if prox_symb and prox_symb.type in ('SUM', 'SUB'):
        op = prox_symb.type
        print(f"Regra Exp2: {op} Term Exp2")
        processa_terminal(op)
        rec_Term()
        rec_Exp2()
    else:
        print("Regra Exp2: vazio")

def rec_Term():
    print("Regra Term: Factor Term2")
    rec_Factor()
    rec_Term2()

def rec_Term2():
    global prox_symb
    if prox_symb and prox_symb.type in ('MUL', 'DIV'):
        op = prox_symb.type
        print(f"Regra Term2: {op} Factor Term2")
        processa_terminal(op)
        rec_Factor()
        rec_Term2()
    else:
        print("Regra Term2: vazio")

def rec_Factor():
    global prox_symb
    if prox_symb and prox_symb.type == 'INT':
        print(f"Regra Factor: INT ({prox_symb.value})")
        processa_terminal('INT')
    elif prox_symb and prox_symb.type == 'PA':
        print("Regra Factor: ( Exp )")
        processa_terminal('PA')
        rec_Exp()
        processa_terminal('PF')
    else:
        raise ValueError(f"Erro: esperava INT ou '(', encontrei {prox_symb.type if prox_symb else 'EOF'}")


def parser(linha):
    global prox_symb
    lexer.input(linha)
    prox_symb = lexer.token()
    rec_Exp()
    if prox_symb is not None:
        print(f"Erro: símbolos a mais após a expressão: {prox_symb.value}")
    else:
        print("Expressão reconhecida com sucesso.")


if __name__ == "__main__":
    expr = input("Introduza uma expressão: ")
    parser(expr)