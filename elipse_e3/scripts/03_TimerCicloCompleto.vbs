' =============================================================================
' 03_TimerCicloCompleto.vbs - Ciclo Elipse × Python (todas as UGs)
' =============================================================================
'
' FLUXO A CADA TICK DO TIMER (recomendado: 1000 ms)
'
'   1) Elipse → Python:  EnviarCampoTodasUGs()
'        grava dados/<ug>/campo.json com P,Q,Vt,If,f,H
'
'   2) Python (serviço separado, já rodando):
'        python main.py servico --intervalo 1
'        lê campo.json → calcula envelope → grava exportacao_elipse/*.csv
'
'   3) Elipse ← Python:  AtualizarPlotTodasUGs(...)
'        valida CSV / carrega séries / atualiza Qsup Qinf e status
'
' IMPORTANTE
'   - O Python NÃO é chamado por este script. Ele deve estar rodando em paralelo.
'   - O Elipse PLOTA o gráfico XY; não se exibe imagem gerada no Python.
'   - Atraso típico: 1 ciclo (campo gravado → Python processa → CSV lido no
'     próximo tick). Para reduzir, use intervalo 0,5 s nos dois lados.
'
' COMO LIGAR NO ELIPSE E3
'   1) Domain / Viewer → Script → Timer (Enabled, Interval = 1000)
'   2) No evento do Timer:
'         Call CicloCurvaCapabilidade()
'   3) Em cada tela de UG: ChartXY com
'         - Pen envelope superior / inferior (arquivo CSV ou tags EnvSup/EnvInf)
'         - Pen/ponto: X = <Prefixo>.PontoQ_pu (ou Q_pu), Y = <Prefixo>.PontoP_pu
' =============================================================================

Option Explicit

' True  = carrega pontos CSV em tags array (estratégia B)
' False = só status + Qsup/Qinf; ChartXY aponta direto aos arquivos (estratégia A)
Public Const CARREGAR_ARRAYS_NO_TIMER = False

Sub CicloCurvaCapabilidade()
    ' 1) Envia variáveis necessárias ao Python
    Call EnviarCampoTodasUGs()

    ' 2) Python roda fora deste script (serviço Windows / Agendador)

    ' 3) Lê CSV e atualiza plot/status
    Call AtualizarPlotTodasUGs(CARREGAR_ARRAYS_NO_TIMER)
End Sub

' --- Atalhos para teste manual no Studio (botão / Execute) -------------------
Sub Teste_SoEnviarCampo()
    Call EnviarCampoTodasUGs()
End Sub

Sub Teste_SoAtualizarPlot()
    Call AtualizarPlotTodasUGs(True)
End Sub
