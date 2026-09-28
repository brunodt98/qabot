import sqlite3


def buscar_cliente(conexao, nome_digitado):
    cursor = conexao.cursor()
    query = "SELECT * FROM clientes WHERE nome = '" + nome_digitado + "'"
    cursor.execute(query)
    return cursor.fetchall()


def remover_pedido(conexao, pedido_id):
    cursor = conexao.cursor()
    cursor.execute(f"DELETE FROM pedidos WHERE id = {pedido_id}")
    conexao.commit()
