import sys
import re

def tokenize(input_string):
    reconhecidos = []
    linha = 1
    mo = re.finditer(r'(?P<COMMENT>#.*)|(?P<SELECT>(?i)\bselect\b)|(?P<WHERE>(?i)\bwhere\b)|(?P<LIMIT>(?i)\blimit\b)|(?P<VAR>\?[A-Za-z_][A-Za-z0-9_]*)|(?P<IRI>[A-Za-z_][A-Za-z0-9_]*:[A-Za-z_][A-Za-z0-9_]*)|(?P<STRING>\".*?\"(@[a-z]+)?)|(?P<NUMBER>[0-9]+)|(?P<SYMBOL>[{}.;])|(?P<SKIP>[ \t])|(?P<NEWLINE>\n)|(?P<ERRO>.)', input_string)
    for m in mo:
        dic = m.groupdict()
        if dic['COMMENT']:
            t = ("COMMENT", dic['COMMENT'], linha, m.span())

        elif dic['SELECT']:
            t = ("SELECT", dic['SELECT'], linha, m.span())

        elif dic['WHERE']:
            t = ("WHERE", dic['WHERE'], linha, m.span())

        elif dic['LIMIT']:
            t = ("LIMIT", dic['LIMIT'], linha, m.span())

        elif dic['VAR']:
            t = ("VAR", dic['VAR'], linha, m.span())

        elif dic['IRI']:
            t = ("IRI", dic['IRI'], linha, m.span())

        elif dic['STRING']:
            t = ("STRING", dic['STRING'], linha, m.span())

        elif dic['NUMBER']:
            t = ("NUMBER", dic['NUMBER'], linha, m.span())

        elif dic['SYMBOL']:
            t = ("SYMBOL", dic['SYMBOL'], linha, m.span())

        elif dic['SKIP']:
            t = ("SKIP", dic['SKIP'], linha, m.span())

        elif dic['NEWLINE']:
            linha += 1
            t = ("NEWLINE", dic['NEWLINE'], linha, m.span())

        elif dic['ERRO']:
            t = ("ERRO", dic['ERRO'], linha, m.span())

        else:
            t = ("UNKNOWN", m.group(), linha, m.span())

        if t[0] not in ('SKIP', 'COMMENT', 'UNKNOWN'):
            reconhecidos.append(t)
    return reconhecidos


if __name__ == "__main__":
    for linha in sys.stdin:
        for tok in tokenize(linha):
            print(tok)
