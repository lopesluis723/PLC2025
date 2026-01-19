# Importa a função init do módulo entre_parser, que inicializa o parser
from pas_yacc import init
# Importa o módulo os para operações do sistema, como remover arquivos
import os

# Remove arquivos de cache do parser para forçar a regeneração das tabelas
# Isso garante que mudanças na gramática sejam refletidas imediatamente
os.system("rm -f parser.out parsetab.py parsetab.pyc 2>/dev/null")

def test_program(name, code):
    """
    Função para testar um programa Pascal específico.
    
    Args:
        name (str): Nome descritivo do teste (ex: "Exemplo 1 - Olá Mundo")
        code (str): Código fonte Pascal a ser compilado
    """
    
    # Imprime um cabeçalho para identificar o teste
    print(f"\n{'='*60}")
    print(f"Teste: {name}")
    print(f"{'='*60}")
    
    # Inicializa o parser (limpa tabelas de símbolos, erros, etc.)
    parser = init()
    
    # Executa o parser no código fonte fornecido
    # O resultado é o código VM gerado ou None em caso de erro
    result = parser.parse(code)
    
    # Verifica se houve erro sintático (erro na estrutura do programa)
    if parser.error:
        print(f"ERRO: {parser.error}")
    
    # Verifica se houve erros semânticos (tipos, declarações, etc.)
    elif parser.semantic_errors:
        print("ERROS SEMÂNTICOS:")
        for err in parser.semantic_errors:
            print(f"  - {err}")
    
    # Se o programa compilou com sucesso (tem código VM gerado)
    if result and result.strip():
        # Divide o código VM em linhas, removendo linhas vazias
        lines = [line.strip() for line in result.strip().split('\n') if line.strip()]
        
        # Imprime estatísticas sobre o código gerado
        print(f"Código VM gerado ({len(lines)} instruções):")
        
        # Imprime o código VM formatado, com separadores para clareza
        print("-" * 40)
        for line in lines:
            print(line)
        print("-" * 40)
    else:
        # Se não houver código gerado (erro ou programa vazio)
        print("Nenhum código gerado!")

# Cabeçalho principal dos testes
print("TESTES DO COMPILADOR PASCAL")
print("="*60)

# Teste 1: Exemplo mais simples - Olá Mundo
# Demonstra funcionalidade básica de saída de texto
test_program("Exemplo 1 - Olá Mundo", """
program HelloWorld;
begin
  writeln('Ola, Mundo!');
end.
""")

# Teste 2: Exemplo de cálculo de fatorial
# Demonstra: declaração de variáveis, entrada do usuário, loop FOR, operações aritméticas
test_program("Exemplo 2 - Fatorial", """
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
""")

# Teste 3: Exemplo de verificação de número primo
# Demonstra: tipos booleanos, loops WHILE, operadores DIV e MOD, estruturas IF aninhadas
test_program("Exemplo 3 - Número Primo", """
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
""")

# Teste 4: Exemplo com arrays
# Demonstra: declaração de arrays unidimensionais, acesso indexado, loops com arrays
test_program("Exemplo 4 - Soma Array", """
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
""")


#Exemplos a mais:


# 5. Operações Matemáticas Complexas
test_program("5. Operações Complexas", """program Calculos;
var
  a, b: integer;
  x, y: real;
  r1, r2: real;
  logico: boolean;
begin
  a := 10;
  b := 3;
  x := 5.5;
  y := 2.0;
  
  r1 := (a + b) * (x - y);
  r2 := a / b + x * y;
  
  logico := (a > b) and (x < y) or (r1 = r2);
  
  writeln('r1 = ', r1);
  writeln('r2 = ', r2);
  writeln('logico = ', logico);
  
  if logico then
    writeln('Condicao verdadeira')
  else
    writeln('Condicao falsa');
end.""")

# 6. Array com Índices Variáveis
test_program("6. Array com Índices Variáveis", """program ArrayVar;
var
  arr: array[0..9] of integer;
  i, j, temp: integer;
begin
  // Preencher array
  for i := 0 to 9 do
    arr[i] := i * 2;
  
  // Trocar elementos usando índices variáveis
  i := 0;
  j := 9;
  while i < j do
  begin
    temp := arr[i];
    arr[i] := arr[j];
    arr[j] := temp;
    i := i + 1;
    j := j - 1;
  end;
  
  // Imprimir array invertido
  for i := 0 to 9 do
    writeln('arr[', i, '] = ', arr[i]);
end.""")

# 7. Booleanos e Operadores Lógicos
test_program("7. Booleanos Complexos", """program BooleanTest;
var
  a, b, c: boolean;
  x, y: integer;
begin
  x := 10;
  y := 20;
  
  a := (x < y) and (y > 0);
  b := (x = 10) or (y = 30);
  c := not a;
  
  writeln('a = ', a);
  writeln('b = ', b);
  writeln('c = ', c);
  
  if a and b then
    writeln('Ambos verdadeiros')
  else if a or b then
    writeln('Pelo menos um verdadeiro')
  else
    writeln('Ambos falsos');
end.""")

# 8. Exemplo com repeat
test_program("Exemplo Repeat Until", """
program TestRepeat;
var i: integer;
begin
  i := 1;
  repeat
    writeln(i);
    i := i + 1;
  until i > 3;
end.
""")

# 9. Exemplo com repeat
test_program("Exemplo Contagem Decrescente", """
program ContagemDecrescente;
var
  i: integer;
begin
  for i := 10 downto 1 do
  begin
    writeln(i);
  end;
end.
""")
# Erro - Acesso a array fora dos limites
test_program("Erro - Array fora dos limites", """
program ErroArrayLimites;
var
  arr: array[1..5] of integer;
begin
  arr[0] := 10;  { índice 0 está fora de 1..5 }
  arr[6] := 20;  { índice 6 está fora de 1..5 }
end.
""")

# Erro - Atribuição direta a array
test_program("Erro - Atribuição direta a array", """
program ErroArrayDireto;
var
  arr: array[1..3] of integer;
begin
  arr := 10;  { não pode atribuir diretamente a array }
end.
""")



# Nota: O Exemplo 5 do enunciado (conversão binário-decimal) não é testado
# pois requer funções definidas pelo usuário, que não foram implementadas
# (funcionalidade opcional no enunciado)

