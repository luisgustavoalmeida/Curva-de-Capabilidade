"""
Funções matemáticas básicas.

Objetivo:
    Fornecer operações matemáticas elementares de forma independente,
    facilitando portabilidade para VBScript no Elipse E3.

Entradas/Saídas:
    Valores numéricos em ponto flutuante.

Equações:
    Hipotenusa: c = sqrt(a² + b²)
    Distância: d = sqrt((x2-x1)² + (y2-y1)²)
    Conversão graus-radianos: rad = graus * π/180

Hipóteses:
    Utiliza math da biblioteca padrão Python apenas como implementação interna.

Limitações:
    Não trata números complexos.

Referências:
    - Apostilas de matemática aplicada à engenharia elétrica.
"""

import math


def RaizQuadrada(valor: float) -> float:
    """
    Calcula a raiz quadrada de um valor não negativo.

    Entrada:
        valor: número real >= 0

    Saída:
        Raiz quadrada do valor informado.
    """
    if valor < 0:
        raise ValueError("RaizQuadrada não definida para valor negativo.")
    return math.sqrt(valor)


def Quadrado(valor: float) -> float:
    """Retorna o quadrado de um valor."""
    return valor * valor


def Hipotenusa(cateto_a: float, cateto_b: float) -> float:
    """
    Calcula a hipotenusa de um triângulo retângulo.

    Equação: c = sqrt(a² + b²)
    """
    return RaizQuadrada(Quadrado(cateto_a) + Quadrado(cateto_b))


def Distancia(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calcula a distância euclidiana entre dois pontos no plano P-Q.

    Equação: d = sqrt((x2-x1)² + (y2-y1)²)
    """
    return Hipotenusa(x2 - x1, y2 - y1)


def Modulo(valor: float) -> float:
    """Retorna o valor absoluto."""
    return abs(valor)


def ConversaoGraus(radianos: float) -> float:
    """Converte radianos para graus."""
    return math.degrees(radianos)


def ConversaoRadianos(graus: float) -> float:
    """Converte graus para radianos."""
    return math.radians(graus)


def Seno(angulo_radianos: float) -> float:
    """Calcula o seno de um ângulo em radianos."""
    return math.sin(angulo_radianos)


def Cosseno(angulo_radianos: float) -> float:
    """Calcula o cosseno de um ângulo em radianos."""
    return math.cos(angulo_radianos)


def Tangente(angulo_radianos: float) -> float:
    """Calcula a tangente de um ângulo em radianos."""
    return math.tan(angulo_radianos)


def ArcoTangente(valor: float) -> float:
    """Retorna o arco tangente em radianos."""
    return math.atan(valor)
