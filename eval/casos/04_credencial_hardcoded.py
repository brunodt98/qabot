import requests

API_TOKEN = "EXEMPLO-NAO-E-UMA-CHAVE-REAL-0000000000"
DB_SENHA = "exemplo123"


def buscar_usuarios():
    resposta = requests.get(
        "https://api.interno.local/usuarios",
        headers={"Authorization": "Bearer " + API_TOKEN},
    )
    return resposta.json()
