"""
Fábrica compartilhada do simulador (gerador ou compensador).
"""

from src.simulador.motor import SimuladorCapabilidade
from src.utilitarios.carregador import CarregadorDados
from src.utilitarios.validador import ValidadorDados


def CriarSimuladorDeDiretorio(diretorio_dados: str) -> SimuladorCapabilidade:
    """
    Carrega dados da usina e cria o simulador.

    - Gerador: exige curvas; turbina opcional (hidro/térmica).
    - CompensadorSincrono: Pmec = 0; turbina ausente.
    """
    carregador = CarregadorDados(diretorio_dados)
    gerador = carregador.carregar_gerador()
    turbina = carregador.carregar_turbina()
    configuracao = carregador.carregar_configuracao_curvas()

    ValidadorDados.validar_gerador(gerador)
    if turbina is not None:
        ValidadorDados.validar_turbina(turbina)

    if gerador.eh_compensador():
        configuracao.potencia_mecanica_maxima_pu = 0.0
        configuracao.potencia_mecanica_minima_pu = 0.0
        configuracao.potencia_ativa_maxima = 0.0
    elif configuracao.unidade == "pu":
        if configuracao.potencia_mecanica_maxima_pu <= 0:
            configuracao.potencia_mecanica_maxima_pu = gerador.fator_potencia_nominal
        if configuracao.potencia_ativa_maxima <= 0:
            configuracao.potencia_ativa_maxima = configuracao.potencia_mecanica_maxima_pu
    else:
        if configuracao.potencia_ativa_maxima <= 0:
            configuracao.potencia_ativa_maxima = gerador.potencia_ativa_maxima
        if configuracao.potencia_ativa_maxima <= 0:
            configuracao.potencia_ativa_maxima = gerador.potencia_ativa_nominal

    return SimuladorCapabilidade(gerador, configuracao, turbina)
