' =============================================================================
' 04_Utilitarios.vbs — Funções auxiliares (arquivo, número, tags)
' =============================================================================
' Dependências: constantes de 00_Config.vbs (CAMINHO_RAIZ_DADOS, etc.)
'
' No Elipse E3: coloque estas funções em um Library / Script compartilhado
' ou cole no início de 01_ / 02_ / 03_.
' =============================================================================

Option Explicit

' --- Conversão numérica (pt-BR → ponto decimal) ------------------------------
Function NumeroParaTextoJson(valor)
    Dim s
    If IsNull(valor) Or IsEmpty(valor) Then
        NumeroParaTextoJson = "0"
        Exit Function
    End If
    s = CStr(CDbl(valor))
    s = Replace(s, ",", ".")
    NumeroParaTextoJson = s
End Function

Function TextoParaNumero(texto)
    Dim s
    s = Trim(CStr(texto))
    s = Replace(s, ",", ".")
    If s = "" Then
        TextoParaNumero = 0
    Else
        TextoParaNumero = CDbl(s)
    End If
End Function

' --- Leitura segura de tag (retorna default se falhar) -----------------------
' No Elipse Viewer o mais comum é Tags("Nome"). Ajuste se necessário.
Function LerTag(nomeTag, valorDefault)
    On Error Resume Next
    Dim v
    v = Tags(nomeTag)
    ' v = Application.GetObject(nomeTag).Value
    If Err.Number <> 0 Then
        Err.Clear
        LerTag = valorDefault
    ElseIf IsNull(v) Or IsEmpty(v) Then
        LerTag = valorDefault
    Else
        LerTag = CDbl(v)
    End If
    On Error GoTo 0
End Function

Function EscreverTag(nomeTag, valor)
    On Error Resume Next
    Tags(nomeTag) = valor
    ' Application.GetObject(nomeTag).Value = valor
    If Err.Number <> 0 Then
        Err.Clear
        EscreverTag = False
    Else
        EscreverTag = True
    End If
    On Error GoTo 0
End Function

' --- Parse da linha de definição da UG ---------------------------------------
' Retorna array: (0)IdPasta (1)Prefixo (2)Sn (3)Vn (4)IfFL (5)fn (6)Hn (7)TemTurbina
Function ParseUg(linhaDefinicao)
    Dim p
    p = Split(linhaDefinicao, "|")
    ParseUg = p
End Function

Function CaminhoPastaUg(idPasta)
    CaminhoPastaUg = CAMINHO_RAIZ_DADOS & "\" & idPasta
End Function

Function CaminhoCampoJson(idPasta)
    CaminhoCampoJson = CaminhoPastaUg(idPasta) & "\campo.json"
End Function

Function CaminhoExportacao(idPasta)
    CaminhoExportacao = CaminhoPastaUg(idPasta) & "\exportacao_elipse"
End Function

' --- FileSystemObject --------------------------------------------------------
Function CriarFso()
    Set CriarFso = CreateObject("Scripting.FileSystemObject")
End Function

' Gravação atômica: escreve .tmp e renomeia para o destino
Sub GravarTextoAtomico(caminhoFinal, conteudo)
    Dim fso, tmp, ts
    Set fso = CriarFso()
    tmp = caminhoFinal & ".tmp"
    Set ts = fso.CreateTextFile(tmp, True, False) ' ASCII/UTF-8 sem BOM (ANSI)
    ts.Write conteudo
    ts.Close
    If fso.FileExists(caminhoFinal) Then
        fso.DeleteFile caminhoFinal, True
    End If
    fso.MoveFile tmp, caminhoFinal
End Sub

Function ArquivoExiste(caminho)
    Dim fso
    Set fso = CriarFso()
    ArquivoExiste = fso.FileExists(caminho)
End Function

' --- Preferência: tag pu se existir e for “válida”, senão SI / base ----------
Function ObterGrandezaPu(prefixo, sufixoPu, sufixoSi, valorSi, base, defaultPu)
    Dim vPu, vSi
    vPu = LerTag(prefixo & sufixoPu, -99999)
    If vPu > -99990 Then
        ObterGrandezaPu = vPu
        Exit Function
    End If
    vSi = LerTag(prefixo & sufixoSi, valorSi)
    If base = 0 Then
        ObterGrandezaPu = defaultPu
    Else
        ObterGrandezaPu = vSi / base
    End If
End Function
