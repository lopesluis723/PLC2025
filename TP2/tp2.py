import re

def md_para_html(texto_md):
    linhas = texto_md.split("\n")
    resultado = []
    em_lista = False

    for linha in linhas:
        linha_convertida = ""

        # Cabeçalhos
        if linha.startswith("### "):
            linha_convertida = f"<h3>{linha[4:]}</h3>"
        elif linha.startswith("## "):
            linha_convertida = f"<h2>{linha[3:]}</h2>"
        elif linha.startswith("# "):
            linha_convertida = f"<h1>{linha[2:]}</h1>"

        # Listas numeradas
        elif re.match(r"^\\d+\\.\\s", linha):
            if not em_lista:
                resultado.append("<ol>")
                em_lista = True
            conteudo = linha.split(". ", 1)[1]
            linha_convertida = f"<li>{conteudo}</li>"

        else:
            # fecha lista se necessário
            if em_lista:
                resultado.append("</ol>")
                em_lista = False

            # Imagens: ![alt](src)
            linha = re.sub(r"!\\[(.*?)\\]\\((.*?)\\)", r'<img src="\\2" alt="\\1"/>', linha)

            # Links: [texto](url)
            linha = re.sub(r"\\[(.*?)\\]\\((.*?)\\)", r'<a href="\\2">\\1</a>', linha)

            # Negrito: **texto**
            linha = re.sub(r"\\*\\*(.*?)\\*\\*", r"<b>\\1</b>", linha)

            # Itálico: *texto*
            linha = re.sub(r"\\*(.*?)\\*", r"<i>\\1</i>", linha)

            linha_convertida = linha

        # adiciona linha processada
        if linha_convertida:
            resultado.append(linha_convertida)

    # Fecha lista se ficou aberta
    if em_lista:
        resultado.append("</ol>")

    return "\n".join(resultado)