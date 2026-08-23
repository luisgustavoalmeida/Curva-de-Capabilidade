"""
Exportação visual da curva de capabilidade para Elipse E3.

Objetivo:
    Gerar CSVs de envelope e limitadores para gráfico XY.
    No Elipse a curva é só representação visual (sem verificação/alarme).

Referências:
    - Documentação Elipse E3: gráficos XY
    - IEEE Std 1110-2002: Capability curves
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.curvas.construtor import PontosCurvaCapabilidade
from src.modelos.ponto_operacional import PontoOperacional
from src.modelos.resultado_capabilidade import ResultadoCapabilidade


class ExportadorElipseE3:
    """
    Exporta séries P–Q para exibição no Elipse E3 (somente visual).

    - CSVs do envelope e limitadores → séries estáticas no gráfico XY
    - Ponto operacional → tags P e Q no mesmo gráfico
    """

    def __init__(self, diretorio_saida: str):
        self.diretorio = Path(diretorio_saida)
        self.diretorio.mkdir(parents=True, exist_ok=True)

    def exportar_pontos_curva(
        self,
        pontos: PontosCurvaCapabilidade,
        prefixo: str = "CurvaCapabilidade",
    ) -> Dict[str, str]:
        """Exporta envelope e limitadores em CSV (Q × P em p.u.)."""
        arquivos = {}

        caminho_superior = self.diretorio / f"{prefixo}_LimiteSuperior.csv"
        self._salvar_csv(caminho_superior, pontos.limite_superior)
        arquivos["LimiteSuperior"] = str(caminho_superior)

        caminho_inferior = self.diretorio / f"{prefixo}_LimiteInferior.csv"
        self._salvar_csv(caminho_inferior, pontos.limite_inferior)
        arquivos["LimiteInferior"] = str(caminho_inferior)

        if pontos.contorno_fechado:
            caminho_contorno = self.diretorio / f"{prefixo}_ContornoFechado.csv"
            self._salvar_csv_grafico(caminho_contorno, pontos.contorno_fechado)
            arquivos["ContornoFechado"] = str(caminho_contorno)

        for nome, serie in pontos.curvas_individuais_superiores.items():
            caminho = self.diretorio / f"{prefixo}_{nome}_Superior.csv"
            self._salvar_csv(caminho, serie)
            arquivos[f"{nome}_Superior"] = str(caminho)

        for nome, serie in pontos.curvas_individuais_inferiores.items():
            caminho = self.diretorio / f"{prefixo}_{nome}_Inferior.csv"
            self._salvar_csv(caminho, serie)
            arquivos[f"{nome}_Inferior"] = str(caminho)

        return arquivos

    def exportar_resultado_operacional(
        self,
        ponto: PontoOperacional,
        resultado: ResultadoCapabilidade,
        nome_arquivo: str = "ResultadoOperacional.csv",
        grandezas_pu: Optional[Dict] = None,
        bases=None,
    ) -> str:
        """
        Exporta snapshot do ponto (referência / debug).

        Não é necessário para o gráfico visual no Elipse.
        """
        caminho = self.diretorio / nome_arquivo
        linhas = [
            "Grandeza,Valor,Unidade",
            f"PotenciaAtiva,{ponto.potencia_ativa},MW",
            f"PotenciaReativa,{ponto.potencia_reativa},Mvar",
            f"Tensao,{ponto.tensao},kV",
            f"CorrenteEstator,{ponto.corrente_estator},A",
            f"CorrenteCampo,{ponto.corrente_campo},A",
            f"Frequencia,{ponto.frequencia},Hz",
            f"Queda,{ponto.queda},m",
            f"PotenciaAparente,{resultado.potencia_aparente},MVA",
            f"FatorPotencia,{resultado.fator_potencia},pu",
            f"LimiteSuperiorEfetivo,{resultado.limite_superior_efetivo},pu",
            f"LimiteInferiorEfetivo,{resultado.limite_inferior_efetivo},pu",
        ]
        if grandezas_pu:
            linhas.extend(
                [
                    f"P_pu,{grandezas_pu.get('P', 0.0)},pu",
                    f"Q_pu,{grandezas_pu.get('Q', 0.0)},pu",
                    f"Vt_pu,{grandezas_pu.get('Vt', 0.0)},pu",
                    f"If_pu,{grandezas_pu.get('If', 0.0)},pu",
                    f"Is_pu,{grandezas_pu.get('Is', 0.0)},pu",
                    f"f_pu,{grandezas_pu.get('f', 0.0)},pu",
                    f"H_pu,{grandezas_pu.get('H', 0.0)},pu",
                    f"S_pu,{grandezas_pu.get('S', 0.0)},pu",
                ]
            )
        if bases is not None:
            resumo = bases.resumo_bases()
            linhas.extend(
                [
                    f"Base_Sn,{resumo['Sn_MVA']},MVA",
                    f"Base_Vn,{resumo['Vn_kV']},kV",
                    f"Base_In,{resumo['In_A']},A",
                    f"Base_If_FL,{resumo['If_FL_A']},A",
                    f"Base_fn,{resumo['fn_Hz']},Hz",
                    f"Base_Hn,{resumo['Hn_m']},m",
                ]
            )
        caminho.write_text("\n".join(linhas), encoding="utf-8")
        return str(caminho)

    def gerar_instrucoes_grafico(self) -> str:
        """Gera instruções para configuração do gráfico visual no Elipse E3."""
        caminho = self.diretorio / "INSTRUCOES_GRAFICO_ELIPSE.md"
        instrucoes = """# Gráfico da Curva de Capabilidade no Elipse E3 (somente visual)

## Ideia

1. Python calcula o envelope e exporta CSVs (`python main.py servico` ou `exportar`).
2. Elipse **plota** no Chart XY (séries CSV + ponto P–Q). Não use imagem do Python.
3. Scripts prontos do supervisório: pasta `elipse_e3/` do repositório
   (`GUIA_IMPLEMENTACAO.md`, `scripts/BibliotecaCompleta.vbs`).

## Configuração do Gráfico XY

1. Criar objeto **Gráfico XY**.
2. Eixo X: Potência Reativa Q (p.u.).
3. Eixo Y: Potência Ativa P (p.u.).
4. Séries de referência (esta pasta):
   - `CurvaCapabilidade_LimiteSuperior.csv`
   - `CurvaCapabilidade_LimiteInferior.csv`
   - (opcional) limitadores individuais e `ContornoFechado`
5. Ponto operacional dinâmico:
   - X = tag `…PontoQ_pu` (ou Q_pu)
   - Y = tag `…PontoP_pu` (ou P_pu)
6. Timer Elipse: `Call CicloCurvaCapabilidade()` (envia `campo.json` + lê CSV).

## Arquivos nesta pasta

- `CurvaCapabilidade_LimiteSuperior.csv`
- `CurvaCapabilidade_LimiteInferior.csv`
- `ResultadoOperacional.csv` (snapshot; opcional)

## Documentação

- `elipse_e3/GUIA_IMPLEMENTACAO.md`
- `documentacao/COMUNICACAO_ELIPSE_PYTHON.md`
"""
        caminho.write_text(instrucoes, encoding="utf-8")
        return str(caminho)

    def copiar_scripts_elipse(self, raiz_projeto: Optional[Path] = None) -> str:
        """Copia o pacote elipse_e3/scripts para esta pasta de exportação."""
        import shutil

        if raiz_projeto is None:
            raiz_projeto = Path(__file__).resolve().parents[2]
        origem = raiz_projeto / "elipse_e3"
        destino = self.diretorio / "scripts_elipse_e3"
        if origem.is_dir():
            if destino.exists():
                shutil.rmtree(destino)
            shutil.copytree(origem, destino)
        return str(destino)

    @staticmethod
    def _salvar_csv_grafico(caminho: Path, pontos: List[Tuple[float, float]]) -> None:
        """Salva pontos já em coordenadas (Q, P) em p.u."""
        linhas = ["PotenciaReativaPu,PotenciaAtivaPu"]
        for potencia_reativa, potencia_ativa in pontos:
            linhas.append(f"{potencia_reativa},{potencia_ativa}")
        caminho.write_text("\n".join(linhas), encoding="utf-8")

    @staticmethod
    def _salvar_csv(caminho: Path, pontos: List[Tuple[float, float]]) -> None:
        """Salva pontos em CSV no formato gráfico Q × P em p.u."""
        linhas = ["PotenciaReativaPu,PotenciaAtivaPu"]
        for potencia_ativa, potencia_reativa in pontos:
            linhas.append(f"{potencia_reativa},{potencia_ativa}")
        caminho.write_text("\n".join(linhas), encoding="utf-8")
