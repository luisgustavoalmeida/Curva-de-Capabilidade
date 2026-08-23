' =============================================================================
' 00_Config.vbs — Configuração compartilhada (Curva de Capabilidade × Elipse E3)
' =============================================================================
' INCLUIR as constantes/funções nos outros scripts (copiar ou Library do E3).
'
' Responsabilidade:
'   - Caminho raiz dos dados Python (pastas ug01, ug02, …)
'   - Lista de unidades geradoras
'   - Bases de conversão SI → p.u. (quando as tags estiverem em MW/kV/A/Hz)
'
' Ajuste as constantes abaixo para a usina ANTES de colocar em produção.
' =============================================================================

Option Explicit

' --- Pasta raiz onde o Python espera dados/<ug>/campo.json -------------------
' AJUSTE para o caminho do clone neste servidor (pasta dados/ do repositório).
Public Const CAMINHO_RAIZ_DADOS = "C:\CurvaDeCapabilidade\dados"

' --- Intervalo sugerido do timer no Elipse (ms) — alinhar ao --intervalo -----
Public Const INTERVALO_TIMER_MS = 1000

' -----------------------------------------------------------------------------
' Catálogo de UGs: adicione uma linha por máquina.
' Formato:
'   IdPasta | PrefixoTag | Sn_MVA | Vn_kV | IfFL_A | fn_Hz | Hn_m | TemTurbina
' IdPasta     = nome da pasta em dados/ (ex.: ug01)
' PrefixoTag  = prefixo das tags no Elipse (ex.: UG01) → Tags("UG01.P_MW")
' TemTurbina  = 1 se hidro com H; 0 caso contrário
' -----------------------------------------------------------------------------
Public Function ObterDefinicaoUGs()
    Dim lista
    ' >>> EDITE ESTA LISTA CONFORME A USINA <<<
    lista = Array( _
        "usina|USINA|194.5|13.8|1780|60|27.5|1", _
        "ug01|UG01|194.5|13.8|1780|60|27.5|1", _
        "ug02|UG02|194.5|13.8|1780|60|27.5|1" _
    )
    ObterDefinicaoUGs = lista
End Function

' -----------------------------------------------------------------------------
' Sufixos das tags de campo. Prefixo vem da UG (ex.: UG01).
'
' Tags em engenharia (SI) — o script converte para p.u. ao gravar campo.json:
'   <Prefixo>.P_MW, .Q_Mvar, .Vt_kV, .If_A, .f_Hz
' Opcionais: .Is_A (0 = Python calcula), .H_m
'
' Se existirem tags já em p.u., têm PRIORIDADE:
'   <Prefixo>.P_pu, .Q_pu, .Vt_pu, .If_pu, .f_pu, .Is_pu, .H_pu
' -----------------------------------------------------------------------------
Public Const TAG_P_MW = ".P_MW"
Public Const TAG_Q_MVAR = ".Q_Mvar"
Public Const TAG_VT_KV = ".Vt_kV"
Public Const TAG_IF_A = ".If_A"
Public Const TAG_F_HZ = ".f_Hz"
Public Const TAG_IS_A = ".Is_A"
Public Const TAG_H_M = ".H_m"

Public Const TAG_P_PU = ".P_pu"
Public Const TAG_Q_PU = ".Q_pu"
Public Const TAG_VT_PU = ".Vt_pu"
Public Const TAG_IF_PU = ".If_pu"
Public Const TAG_F_PU = ".f_pu"
Public Const TAG_IS_PU = ".Is_pu"
Public Const TAG_H_PU = ".H_pu"

' Tags de status / plot (preenchidas após ler CSV)
Public Const TAG_QSUP_PU = ".Qsup_pu"
Public Const TAG_QINF_PU = ".Qinf_pu"
Public Const TAG_PONTO_P_PU = ".PontoP_pu"
Public Const TAG_PONTO_Q_PU = ".PontoQ_pu"
Public Const TAG_CSV_OK = ".EnvelopeCsvOk"
Public Const TAG_CAMPO_OK = ".CampoJsonOk"
Public Const TAG_TIMESTAMP = ".CurvaTimestamp"
Public Const TAG_N_PONTOS_SUP = ".NPontosSup"
Public Const TAG_N_PONTOS_INF = ".NPontosInf"

' Arquivos gerados pelo Python (não renomear)
Public Const ARQ_LIMITE_SUP = "CurvaCapabilidade_LimiteSuperior.csv"
Public Const ARQ_LIMITE_INF = "CurvaCapabilidade_LimiteInferior.csv"
Public Const ARQ_RESULTADO = "ResultadoOperacional.csv"

' Máximo de pontos do CSV carregados para tags de série
Public Const MAX_PONTOS_CSV = 500
