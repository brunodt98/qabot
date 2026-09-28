import os
import json
import datetime


def somar_precos(itens):
    total = 0
    for item in itens:
        total += item["preco"]
    print("DEBUG total:", total)
    return total
