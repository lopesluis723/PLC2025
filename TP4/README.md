 PLC2025

## Título
Trabalho Prático 4 - Construir um analisador léxico para uma liguagem de query com a qual se podem escrever frases do
género:

DBPedia: obras de Chuck Berry

select ?nome ?desc where {
    ?s a dbo:MusicalArtist.
    ?s foaf:name "Chuck Berry"@en .
    ?w dbo:artist ?s.
    ?w foaf:name ?nome.
    ?w dbo:abstract ?desc
} LIMIT 1000

## Autor
- **Nome:** Luís Miguel Faria Lopes  
- **ID:** A108392  
- **Foto:** ![Foto](Foto_Luis.png)
