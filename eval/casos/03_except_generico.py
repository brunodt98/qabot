import json


def ler_configuracao(caminho):
    try:
        with open(caminho) as arquivo:
            return json.load(arquivo)
    except:
        return {}


def gravar(caminho, dados):
    try:
        with open(caminho, "w") as arquivo:
            json.dump(dados, arquivo)
    except Exception:
        pass
