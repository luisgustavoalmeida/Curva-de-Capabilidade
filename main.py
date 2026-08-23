#!/usr/bin/env python3
"""
Ponto de entrada da Curva de Capabilidade.

Uso:
    python main.py
    python main.py simulador
    python main.py calcular --dados dados/usina
    python main.py exportar --dados dados/usina
    python main.py nova-usina --pasta minha_usina --nome "Usina X"
    python main.py servico
    python main.py servico --intervalo 1 --uma-vez
"""

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from src.exportacao.elipse_e3 import ExportadorElipseE3
from src.servico.envelope_dinamico import RodarServico
from src.simulador.fabrica import CriarSimuladorDeDiretorio
from src.utilitarios.nova_usina import CriarUsina

DADOS_PADRAO = str(RAIZ / "dados" / "usina")
RAIZ_DADOS = str(RAIZ / "dados")


def criar_simulador(diretorio_dados: str):
    return CriarSimuladorDeDiretorio(diretorio_dados)


def comando_calcular(diretorio_dados: str) -> None:
    simulador = criar_simulador(diretorio_dados)
    resultado = simulador.executar_simulacao_completa()
    res = resultado["ResultadoCapabilidade"]
    ponto = resultado["PontoOperacional"]

    print("=== Curva de Capabilidade ===")
    print(f"Máquina: {simulador.gerador.identificacao}")
    print(f"Tipo: {simulador.gerador.tipo_maquina.value}")
    print(f"Ponto: P={ponto.potencia_ativa:.2f} MW, Q={ponto.potencia_reativa:.2f} Mvar")
    p_pu, q_pu, v_pu = resultado["PontoOperacionalPu"]
    print(
        f"Ponto p.u.: P={p_pu:.4f}, Q={q_pu:.4f}, V={v_pu:.4f} "
        f"(base Sn={simulador.bases.potencia_aparente_base} MVA)"
    )
    print(f"Dentro da curva: {res.dentro_da_curva}")
    print(f"Margem operacional: {res.margem_operacional:.2f} %")
    print(
        f"Limites Q (pu): [{res.limite_inferior_efetivo:.4f}, "
        f"{res.limite_superior_efetivo:.4f}]"
    )
    print(f"Limite restritivo: {res.limite_restritivo}")
    if res.mensagens:
        print("Mensagens:")
        for msg in res.mensagens:
            print(f"  - {msg}")


def comando_exportar(diretorio_dados: str) -> None:
    simulador = criar_simulador(diretorio_dados)
    resultado = simulador.executar_simulacao_completa()
    diretorio_saida = str(Path(diretorio_dados) / "exportacao_elipse")
    exportador = ExportadorElipseE3(diretorio_saida)
    arquivos = exportador.exportar_pontos_curva(resultado["PontosCurva"])
    exportador.exportar_resultado_operacional(
        resultado["PontoOperacional"],
        resultado["ResultadoCapabilidade"],
        grandezas_pu=resultado["GrandezasCampoPu"],
        bases=resultado["Bases"],
    )
    exportador.gerar_instrucoes_grafico()
    exportador.copiar_scripts_elipse(RAIZ)
    print(f"Exportação visual concluída em: {diretorio_saida}")
    for nome, caminho in arquivos.items():
        print(f"  {nome}: {caminho}")
    print(f"  Scripts Elipse: {diretorio_saida}/scripts_elipse_e3/")


def comando_simulador(diretorio_dados: str) -> None:
    from interface.simulador_gui import executar_interface

    executar_interface(diretorio_dados)


def comando_nova_usina(args: argparse.Namespace) -> None:
    destino = CriarUsina(
        RAIZ / "dados",
        args.pasta,
        identificacao=args.nome or None,
    )
    print(f"Usina criada (cópia do template): {destino}")
    print("  Edite gerador.json / curvas.json / turbina.json e os CSVs conforme a placa.")
    print(f"  Simulador: python main.py simulador --dados {destino}")
    print("  Serviço multi-UG: python main.py servico")


def comando_servico(args: argparse.Namespace) -> None:
    apenas = [x.strip() for x in args.apenas.split(",") if x.strip()] or None
    RodarServico(
        args.raiz_dados,
        intervalo_s=args.intervalo,
        apenas=apenas,
        uma_vez=args.uma_vez,
    )


def main() -> None:
    if len(sys.argv) == 1:
        comando_simulador(DADOS_PADRAO)
        return

    parser = argparse.ArgumentParser(
        description=(
            "Curva de Capabilidade — gerador ou compensador. "
            "Template: dados/usina | Serviço: envelope dinâmico multi-UG."
        )
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    for nome in ("simulador", "calcular", "exportar"):
        p = sub.add_parser(nome)
        p.add_argument(
            "--dados",
            default=DADOS_PADRAO,
            help="Diretório da usina (JSON + CSVs opcionais)",
        )

    p_nova = sub.add_parser(
        "nova-usina",
        help="Copia dados/usina para dados/<pasta> (depois edite os valores)",
    )
    p_nova.add_argument("--pasta", required=True, help="Nome da pasta em dados/")
    p_nova.add_argument("--nome", default="", help="Identificação em gerador.json")

    p_srv = sub.add_parser(
        "servico",
        help=(
            "Envelope dinâmico: um loop percorre todas as UGs em dados/, "
            "lê campo.json e atualiza exportacao_elipse/"
        ),
    )
    p_srv.add_argument(
        "--raiz-dados",
        default=RAIZ_DADOS,
        help="Pasta pai das UGs (default: dados/)",
    )
    p_srv.add_argument(
        "--intervalo",
        type=float,
        default=1.0,
        help="Segundos entre ciclos (default: 1)",
    )
    p_srv.add_argument(
        "--apenas",
        default="",
        help="Lista de pastas separadas por vírgula (ex.: usina,ug02)",
    )
    p_srv.add_argument(
        "--uma-vez",
        action="store_true",
        help="Executa um ciclo e encerra",
    )

    args = parser.parse_args()

    if args.comando == "simulador":
        comando_simulador(args.dados)
    elif args.comando == "calcular":
        comando_calcular(args.dados)
    elif args.comando == "exportar":
        comando_exportar(args.dados)
    elif args.comando == "nova-usina":
        comando_nova_usina(args)
    elif args.comando == "servico":
        comando_servico(args)


if __name__ == "__main__":
    main()
