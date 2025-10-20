import json
from datetime import datetime

FICHEIRO_STOCK = "stock.json"

MOEDAS = {
    "2e": 200, "1e": 100,
    "50c": 50, "20c": 20, "10c": 10,
    "5c": 5, "2c": 2, "1c": 1
}

saldo = 0
stock = []


def carregar_stock():
    global stock
    data = datetime.now().strftime("%Y-%m-%d")
    try:
        with open(FICHEIRO_STOCK, "r", encoding="utf-8") as f:
            stock = json.load(f)
        print(f"maq: {data}, Stock carregado, Estado atualizado.")
    except FileNotFoundError:
        print(f"maq: {data}, 'stock.json' não encontrado. Novo stock.")
        stock = []


def guardar_stock():
    with open(FICHEIRO_STOCK, "w", encoding="utf-8") as f:
        json.dump(stock, f, indent=2, ensure_ascii=False)


def listar_produtos():
    print("maq:")
    print(f"{'cod':<5} | {'nome':<20} | {'quantidade':<10} | {'preço':<6}")
    print("-" * 55)
    for produto in stock:
        print(f"{produto['cod']:<5} | {produto['nome']:<20} | "
              f"{produto['quant']: <10} | {produto['preco']:<.2f}")


def formatar_saldo(cents):
    euros = cents // 100
    centimos = cents % 100
    return f"{euros}e{centimos:02d}c"


def inserir_moeda(entrada):
    global saldo
    entrada = entrada.replace(".", "").strip()
    moedas = [m.strip() for m in entrada.split(",")]

    for m in moedas:
        if m in MOEDAS:
            saldo += MOEDAS[m]
        else:
            print(f"maq: Moeda '{m}' inválida.")
    print(f"maq: Saldo = {formatar_saldo(saldo)}")


def selecionar_produto(cod):
    global saldo
    cod = cod.strip()

    for produto in stock:
        if produto["cod"] == cod:
            if produto["quant"] <= 0:
                print(f"maq: Produto '{produto['nome']}' esgotado.")
                return

            preco_cent = int(produto["preco"] * 100)
            if saldo >= preco_cent:
                saldo -= preco_cent
                produto["quant"] -= 1
                print(f"maq: Pode retirar o produto dispensado \"{produto['nome']}\"")
                print(f"maq: Saldo = {formatar_saldo(saldo)}")
            else:
                print("maq: Saldo insufuciente para satisfazer o seu pedido")
                print(f"maq: Saldo = {formatar_saldo(saldo)}; "
                      f"Pedido = {formatar_saldo(preco_cent)}")
            return

    print(f"maq: Produto com código '{cod}' não encontrado.")


def calcular_troco():
    global saldo
    troco = {}
    restante = saldo

    for moeda, val in MOEDAS.items():
        qtd = restante // val
        if qtd > 0:
            troco[moeda] = qtd
            restante -= qtd * val

    if troco:
        partes = [f"{qtd}x {moeda}" for moeda, qtd in troco.items()]
        print("maq: Pode retirar o troco: " + ", ".join(partes) + ".")
    else:
        print("maq: Não há troco a devolver.")

    saldo = 0


def main():
    carregar_stock()
    print("maq: Bom dia. Estou disponível para atender o seu pedido.")

    while True:
        comando = input(">> ").strip()

        if comando.upper() == "LISTAR":
            listar_produtos()

        elif comando.upper().startswith("MOEDA"):
            moedas = comando[6:].strip()
            inserir_moeda(moedas)

        elif comando.upper().startswith("SELECIONAR"):
            cod = comando[10:].strip()
            selecionar_produto(cod)

        elif comando.upper() == "SAIR":
            calcular_troco()
            guardar_stock()
            print("maq: Até à próxima")
            break

        else:
            print("maq: Comando não reconhecido.")


if __name__ == "__main__":
    main()
