' =============================================================================
' 02_LerCsvEAtualizarPlot.vbs
' =============================================================================
' RESPONSABILIDADE PYTHON → ELIPSE (plot visual)
'
' Lê os CSV gerados pelo Python em:
'   dados/<ug>/exportacao_elipse/CurvaCapabilidade_LimiteSuperior.csv
'   dados/<ug>/exportacao_elipse/CurvaCapabilidade_LimiteInferior.csv
'
' Formato CSV (p.u.):
'   PotenciaReativaPu,PotenciaAtivaPu
'   Q,P
'
' ESTRATÉGIA DE PLOT NO ELIPSE E3 (duas opções)
'
'   A) RECOMENDADA - Gráfico XY ligado ao arquivo CSV
'      No Studio: ChartXY → Pen → Data Source = arquivo
'      (ou “User File” / importação periódica, conforme versão do E3)
'      Este script apenas valida se o arquivo existe e atualiza tags de status
'      + Qsup/Qinf no ponto atual (ResultadoOperacional.csv).
'
'   B) TAGS DE SÉRIE - Carrega pontos em tags indexadas para alimentar o XY
'      <Prefixo>.EnvSup_Q[0..N], <Prefixo>.EnvSup_P[0..N]
'      <Prefixo>.EnvInf_Q[0..N], <Prefixo>.EnvInf_P[0..N]
'      Crie arrays/Internal Tags no Domain com tamanho >= MAX_PONTOS_CSV
'      e vincule as pens do ChartXY a esses arrays.
'
' O Elipse DESENHA o gráfico; o Python NÃO envia imagem.
' =============================================================================

Option Explicit

' -----------------------------------------------------------------------------
' Lê um CSV Q,P e preenche tags de série (estratégia B).
' prefixoSerie = ex.: "UG01.EnvSup" → UG01.EnvSup_Q[i], UG01.EnvSup_P[i]
' Retorna quantidade de pontos lidos.
' -----------------------------------------------------------------------------
Function CarregarCsvEmTagsSerie(caminhoCsv, prefixoSerie)
    Dim fso, ts, linha, partes, n, q, p
    CarregarCsvEmTagsSerie = 0
    If Not ArquivoExiste(caminhoCsv) Then Exit Function

    Set fso = CriarFso()
    Set ts = fso.OpenTextFile(caminhoCsv, 1, False)
    n = 0
    Do While Not ts.AtEndOfStream
        linha = Trim(ts.ReadLine)
        If linha = "" Then
            ' ignora
        ElseIf Left(linha, 1) = "#" Then
            ' comentário
        ElseIf InStr(1, linha, "PotenciaReativa", vbTextCompare) > 0 Then
            ' cabeçalho
        Else
            partes = Split(linha, ",")
            If UBound(partes) >= 1 Then
                q = TextoParaNumero(partes(0))
                p = TextoParaNumero(partes(1))
                ' Escrita em tag array - ajuste a sintaxe à sua versão do E3:
                '   Tags(prefixoSerie & "_Q[" & n & "]") = q
                Call EscreverTag(prefixoSerie & "_Q[" & n & "]", q)
                Call EscreverTag(prefixoSerie & "_P[" & n & "]", p)
                n = n + 1
                If n >= MAX_PONTOS_CSV Then Exit Do
            End If
        End If
    Loop
    ts.Close
    CarregarCsvEmTagsSerie = n
End Function

' -----------------------------------------------------------------------------
' Lê ResultadoOperacional.csv e publica Qsup/Qinf (e P/Q pu se houver)
' -----------------------------------------------------------------------------
Sub AtualizarTagsResultado(idPasta, prefixo)
    Dim caminho, fso, ts, linha, partes, nome, valor
    caminho = CaminhoExportacao(idPasta) & "\" & ARQ_RESULTADO
    If Not ArquivoExiste(caminho) Then Exit Sub

    Set fso = CriarFso()
    Set ts = fso.OpenTextFile(caminho, 1, False)
    Do While Not ts.AtEndOfStream
        linha = Trim(ts.ReadLine)
        If InStr(linha, ",") > 0 And Left(linha, 8) <> "Grandeza" Then
            partes = Split(linha, ",")
            nome = Trim(partes(0))
            valor = TextoParaNumero(partes(1))
            Select Case nome
                Case "LimiteSuperiorEfetivo"
                    Call EscreverTag(prefixo & TAG_QSUP_PU, valor)
                Case "LimiteInferiorEfetivo"
                    Call EscreverTag(prefixo & TAG_QINF_PU, valor)
                Case "P_pu"
                    Call EscreverTag(prefixo & TAG_PONTO_P_PU, valor)
                Case "Q_pu"
                    Call EscreverTag(prefixo & TAG_PONTO_Q_PU, valor)
            End Select
        End If
    Loop
    ts.Close
End Sub

' -----------------------------------------------------------------------------
' Atualiza plot/status de UMA UG
' carregarArrays = True → estratégia B (tags de série)
'                  False → só status + Qsup/Qinf (estratégia A: XY no arquivo)
' -----------------------------------------------------------------------------
Function AtualizarPlotUmaUg(ugDef, carregarArrays)
    Dim p, idPasta, prefixo, pastaExp, nSup, nInf, ok

    p = ParseUg(ugDef)
    idPasta = p(0)
    prefixo = p(1)
    pastaExp = CaminhoExportacao(idPasta)
    ok = True

    If Not ArquivoExiste(pastaExp & "\" & ARQ_LIMITE_SUP) Then ok = False
    If Not ArquivoExiste(pastaExp & "\" & ARQ_LIMITE_INF) Then ok = False

    If carregarArrays And ok Then
        nSup = CarregarCsvEmTagsSerie( _
            pastaExp & "\" & ARQ_LIMITE_SUP, prefixo & ".EnvSup")
        nInf = CarregarCsvEmTagsSerie( _
            pastaExp & "\" & ARQ_LIMITE_INF, prefixo & ".EnvInf")
        Call EscreverTag(prefixo & TAG_N_PONTOS_SUP, nSup)
        Call EscreverTag(prefixo & TAG_N_PONTOS_INF, nInf)
        If nSup < 2 Or nInf < 2 Then ok = False
    End If

    Call AtualizarTagsResultado(idPasta, prefixo)
    Call EscreverTag(prefixo & TAG_CSV_OK, IIf(ok, 1, 0))
    Call EscreverTag(prefixo & TAG_TIMESTAMP, Now)
    AtualizarPlotUmaUg = ok
End Function

' Compatibilidade VBScript: IIf pode não existir em todas as hosts
Function IIf(cond, a, b)
    If cond Then IIf = a Else IIf = b
End Function

' -----------------------------------------------------------------------------
' Percorre todas as UGs - chame no Timer DEPOIS de EnviarCampoTodasUGs
' (ou no mesmo timer, após o envio, dando tempo ao Python: ver 03_)
' -----------------------------------------------------------------------------
Sub AtualizarPlotTodasUGs(carregarArrays)
    Dim ugs, i, nOk
    ugs = ObterDefinicaoUGs()
    nOk = 0
    For i = 0 To UBound(ugs)
        If AtualizarPlotUmaUg(ugs(i), carregarArrays) Then nOk = nOk + 1
    Next
    Call EscreverTag("CurvaCapabilidade.UGsCsvOk", nOk)
End Sub
