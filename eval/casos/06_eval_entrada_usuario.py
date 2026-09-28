def calculadora():
    expressao = input("Digite a conta: ")
    resultado = eval(expressao)
    print("Resultado:", resultado)
    return resultado


def aplicar_regra(regra_do_usuario, valor):
    return eval(regra_do_usuario.replace("x", str(valor)))
