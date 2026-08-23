Option Explicit

' BibliotecaCompleta.vbs — ver elipse_e3/GUIA_IMPLEMENTACAO.md

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


' =============================================================================
' 04_Utilitarios.vbs — Funções auxiliares (arquivo, número, tags)
' =============================================================================
' Dependências: constantes de 00_Config.vbs (CAMINHO_RAIZ_DADOS, etc.)
'
' No Elipse E3: coloque estas funções em um Library / Script compartilhado
' ou cole no início de 01_ / 02_ / 03_.
' =============================================================================


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
' O Python NÃO precisa estar no mesmo script — só precisa do arquivo atualizado.
' =============================================================================


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
'   A) RECOMENDADA — Gráfico XY ligado ao arquivo CSV
'      No Studio: ChartXY → Pen → Data Source = arquivo
'      (ou “User File” / importação periódica, conforme versão do E3)
'      Este script apenas valida se o arquivo existe e atualiza tags de status
'      + Qsup/Qinf no ponto atual (ResultadoOperacional.csv).
'
'   B) TAGS DE SÉRIE — Carrega pontos em tags indexadas para alimentar o XY
'      <Prefixo>.EnvSup_Q[0..N], <Prefixo>.EnvSup_P[0..N]
'      <Prefixo>.EnvInf_Q[0..N], <Prefixo>.EnvInf_P[0..N]
'      Crie arrays/Internal Tags no Domain com tamanho >= MAX_PONTOS_CSV
'      e vincule as pens do ChartXY a esses arrays.
'
' O Elipse DESENHA o gráfico; o Python NÃO envia imagem.
' =============================================================================


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
                ' Escrita em tag array — ajuste a sintaxe à sua versão do E3:
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
' Percorre todas as UGs — chame no Timer DEPOIS de EnviarCampoTodasUGs
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


' =============================================================================
' 03_TimerCicloCompleto.vbs — Ciclo Elipse × Python (todas as UGs)
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
