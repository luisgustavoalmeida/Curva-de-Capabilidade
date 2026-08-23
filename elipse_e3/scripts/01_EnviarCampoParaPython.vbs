' =============================================================================
' 01_EnviarCampoParaPython.vbs
' =============================================================================
' RESPONSABILIDADE DO ELIPSE → PYTHON
'
' Lê as tags de cada UG (P, Q, Vt, If, f, Is, H), converte para p.u. se
' necessário e grava dados/<ug>/campo.json para o serviço:
'   python main.py servico
'
' COMO USAR NO ELIPSE E3
'   1) Cole 00_Config + 04_Utilitarios + este arquivo em um Library, OU
'      chame EnviarCampoTodasUGs a partir de um Timer (1 s).
'   2) Crie as tags listadas em elipse_e3/tags/CATALOGO_TAGS.md
'   3) Ajuste CAMINHO_RAIZ_DADOS e ObterDefinicaoUGs() em 00_Config.vbs
'
' O Python NÃO precisa estar no mesmo script - só precisa do arquivo atualizado.
' =============================================================================

Option Explicit

' -----------------------------------------------------------------------------
' Envia campo.json de UMA unidade geradora
' ugDef = string "id|prefixo|Sn|Vn|IfFL|fn|Hn|TemTurbina"
' -----------------------------------------------------------------------------
Function EnviarCampoUmaUg(ugDef)
    Dim p, idPasta, prefixo, sn, vn, ifFl, fn, hn, temTurbina
    Dim pPu, qPu, vtPu, ifPu, fPu, isPu, hPu
    Dim json, caminho, ok

    p = ParseUg(ugDef)
    idPasta = p(0)
    prefixo = p(1)
    sn = TextoParaNumero(p(2))
    vn = TextoParaNumero(p(3))
    ifFl = TextoParaNumero(p(4))
    fn = TextoParaNumero(p(5))
    hn = TextoParaNumero(p(6))
    temTurbina = CInt(p(7))

    ' --- Grandezas em p.u. (prioridade tags *_pu; senão SI / base) -----------
    pPu = ObterGrandezaPu(prefixo, TAG_P_PU, TAG_P_MW, 0, sn, 0)
    qPu = ObterGrandezaPu(prefixo, TAG_Q_PU, TAG_Q_MVAR, 0, sn, 0)
    vtPu = ObterGrandezaPu(prefixo, TAG_VT_PU, TAG_VT_KV, vn, vn, 1)
    ifPu = ObterGrandezaPu(prefixo, TAG_IF_PU, TAG_IF_A, ifFl, ifFl, 1)
    fPu = ObterGrandezaPu(prefixo, TAG_F_PU, TAG_F_HZ, fn, fn, 1)
    isPu = ObterGrandezaPu(prefixo, TAG_IS_PU, TAG_IS_A, 0, sn, 0)
    ' Nota: base de Is em pu é In; se não houver tag In, deixe Is=0 (Python calcula)
    If temTurbina = 1 And hn > 0 Then
        hPu = ObterGrandezaPu(prefixo, TAG_H_PU, TAG_H_M, hn, hn, 1)
    Else
        hPu = 0
    End If

    ' --- Monta JSON no formato esperado pelo Python (campo.json) ------------
    json = "{" & vbCrLf
    json = json & "  ""EmPorUnidade"": true," & vbCrLf
    json = json & "  ""P"": " & NumeroParaTextoJson(pPu) & "," & vbCrLf
    json = json & "  ""Q"": " & NumeroParaTextoJson(qPu) & "," & vbCrLf
    json = json & "  ""Vt"": " & NumeroParaTextoJson(vtPu) & "," & vbCrLf
    json = json & "  ""If"": " & NumeroParaTextoJson(ifPu) & "," & vbCrLf
    json = json & "  ""Is"": " & NumeroParaTextoJson(isPu) & "," & vbCrLf
    json = json & "  ""f"": " & NumeroParaTextoJson(fPu) & "," & vbCrLf
    json = json & "  ""H"": " & NumeroParaTextoJson(hPu) & vbCrLf
    json = json & "}" & vbCrLf

    caminho = CaminhoCampoJson(idPasta)

    On Error Resume Next
    GravarTextoAtomico caminho, json
    If Err.Number <> 0 Then
        Call EscreverTag(prefixo & TAG_CAMPO_OK, 0)
        EnviarCampoUmaUg = False
        Err.Clear
        Exit Function
    End If
    On Error GoTo 0

    Call EscreverTag(prefixo & TAG_CAMPO_OK, 1)
    Call EscreverTag(prefixo & TAG_PONTO_P_PU, pPu)
    Call EscreverTag(prefixo & TAG_PONTO_Q_PU, qPu)
    EnviarCampoUmaUg = True
End Function

' -----------------------------------------------------------------------------
' Percorre TODAS as UGs definidas em 00_Config.vbs
' Chame esta função no Timer do Elipse (a cada INTERVALO_TIMER_MS).
' -----------------------------------------------------------------------------
Sub EnviarCampoTodasUGs()
    Dim ugs, i, ok, nOk
    ugs = ObterDefinicaoUGs()
    nOk = 0
    For i = 0 To UBound(ugs)
        ok = EnviarCampoUmaUg(ugs(i))
        If ok Then nOk = nOk + 1
    Next
    ' Opcional: tag global de diagnóstico
    Call EscreverTag("CurvaCapabilidade.UGsCampoOk", nOk)
End Sub
