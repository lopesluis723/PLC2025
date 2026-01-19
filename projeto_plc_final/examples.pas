// Exemplos fornecidos pelo docente 
// Exemplo 1: Olá, Mundo!
program HelloWorld;
begin
  writeln('Ola, Mundo!');
end.

// Exemplo 2: Fatorial
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

// Exemplo 3: Verificação de Número Primo
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

// Exemplo4: Soma de uma lista de inteiros
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

// Exemplos extra

// Exemplo 6: Array com Índices Variáveis
program ArrayVar;
var
  arr: array[0..9] of integer;
  i, j, temp: integer;
begin
  for i := 0 to 9 do
    arr[i] := i * 2;

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

  for i := 0 to 9 do
    writeln('arr[', i, '] = ', arr[i]);
end.

// Exemplo 7: Operações Complexas
program Calculos;
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
end.

// Exemplo 8: Estrutura Repeat-Until
program TestRepeat;
var i: integer;
begin
  i := 1;
  repeat
    writeln(i);
    i := i + 1;
  until i > 3;
end.

// Exemplo 9: Contagem Decrescente
program ContagemDecrescente;

var
  i: integer;

begin
  for i := 10 downto 1 do
  begin
    writeln(i);
  end;
end.