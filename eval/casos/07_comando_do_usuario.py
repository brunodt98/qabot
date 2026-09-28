import os
import logging


def compactar_pasta(nome_da_pasta):
    os.system("tar -czf backup.tar.gz " + nome_da_pasta)


def autenticar(usuario, senha):
    logging.info("Tentativa de login: usuario=%s senha=%s", usuario, senha)
    return usuario == "admin" and senha == "admin"
