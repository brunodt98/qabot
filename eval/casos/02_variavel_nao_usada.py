def calcular_media(notas):
    quantidade = len(notas)
    soma = sum(notas)
    media_ponderada = 0
    if quantidade == 0:
        return 0
    return soma / quantidade
