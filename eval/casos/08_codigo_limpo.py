"""Conversão de temperaturas entre Celsius e Fahrenheit."""


def celsius_para_fahrenheit(celsius: float) -> float:
    """Converte uma temperatura de Celsius para Fahrenheit."""
    return celsius * 9 / 5 + 32


def fahrenheit_para_celsius(fahrenheit: float) -> float:
    """Converte uma temperatura de Fahrenheit para Celsius."""
    return (fahrenheit - 32) * 5 / 9


def media(temperaturas: list[float]) -> float:
    """Devolve a media das temperaturas, ou 0.0 para lista vazia."""
    if not temperaturas:
        return 0.0
    return sum(temperaturas) / len(temperaturas)
