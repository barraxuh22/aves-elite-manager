import ast
import copy
import csv
import hashlib
import io
import json
import re
import uuid

from datetime import datetime
from pathlib import Path

import streamlit as st


# ============================================================
# CONFIGURAÇÃO E CONTEÚDOS ORIGINAIS
# Não importa nem executa o programa Tkinter.
# ============================================================

st.set_page_config(
    page_title="Aves Elite Manager",
    page_icon="🐦",
    layout="wide",
)


@st.cache_data
def ler_configuracao(texto):
    nomes = {
        "PADRAO", "TODAS", "GERAL", "DATA", "DATA_HORA",
        "SEXOS", "CATEGORIAS", "ESPECIES", "NOTA",
        "BASE_CUIDADOS", "BASE_ALIMENTACAO", "BASE_CICLO", "PERFIS",
    }
    resultado = {}

    for no in ast.parse(texto).body:
        if not isinstance(no, ast.Assign):
            continue

        for alvo in no.targets:
            if isinstance(alvo, ast.Name) and alvo.id in nomes:
                resultado[alvo.id] = ast.literal_eval(no.value)

    em_falta = nomes - resultado.keys()

    if em_falta:
        raise ValueError(
            "Configurações em falta: " + ", ".join(sorted(em_falta))
        )

    return resultado


try:
    origem = Path(__file__).with_name("aves_elite_manager.py")
    CFG = ler_configuracao(origem.read_text(encoding="utf-8-sig"))
except Exception as erro:
    st.error(
        "Não foi possível ler as configurações do ficheiro "
        "'aves_elite_manager.py'."
    )
    st.code(str(erro))
    st.stop()


PADRAO = CFG["PADRAO"]
TODAS = CFG["TODAS"]
GERAL = CFG["GERAL"]
DATA = CFG["DATA"]
DATA_HORA = CFG["DATA_HORA"]
SEXOS = CFG["SEXOS"]
CATEGORIAS = CFG["CATEGORIAS"]


# ============================================================
# FUNÇÕES DE APOIO
# ============================================================

def uid():
    return uuid.uuid4().hex


def normal(valor):
    return str(valor or "").strip().casefold()


def natural(valor):
    return tuple(
        (1, int(p)) if p.isdigit() else (0, p.casefold())
        for p in re.split(r"(\d+)", str(valor or ""))
    )


def data_valida(valor, hora=False):
    formato = DATA_HORA if hora else DATA
    resultado = datetime.strptime(str(valor).strip(), formato)

    if resultado.year < 1900:
        raise ValueError("O ano não pode ser anterior a 1900.")

    return resultado


def ano_valido(valor):
    return (
        bool(re.fullmatch(r"\d{4}", str(valor)))
        and 1900 <= int(valor) <= datetime.now().year
    )


def novos_dados():
    return {
        "versao": 7,
        "especies": dict(CFG["ESPECIES"]),
        "registos": [],
        "plantel": [],
        "crias": [],
    }


def procurar(dados, grupo, identificador):
    return next(
        (
            item for item in dados[grupo]
            if item["id"] == identificador
        ),
        None,
    )


def serializar(dados):
    return json.dumps(
        dados, ensure_ascii=False, indent=4
    ).encode("utf-8")


def assinatura(dados):
    return hashlib.sha256(serializar(dados)).hexdigest()


def preparar_importacao(conteudo):
    dados = json.loads(conteudo.decode("utf-8-sig"))

    if isinstance(dados, list):
        dados = {"registos": dados}

    if not isinstance(dados, dict):
        raise ValueError("A estrutura principal deve ser um objeto JSON.")

    dados = copy.deepcopy(dados)

    especies = dados.setdefault("especies", dict(CFG["ESPECIES"]))

    if not isinstance(especies, dict):
        raise ValueError("O campo 'especies' deve ser um objeto.")

    limpas = {}

    for nome, cientifico in especies.items():
        if (
            not isinstance(nome, str)
            or not nome.strip()
            or not isinstance(cientifico, str)
        ):
            raise ValueError("Existe uma espécie inválida.")

        nome = nome.strip()

        if normal(nome) in {normal(TODAS), normal(GERAL)}:
            raise ValueError("Existe um nome de espécie reservado.")

        existente = next(
            (n for n in limpas if normal(n) == normal(nome)), None
        )

        if existente is not None:
            raise ValueError(
                f"Espécies repetidas com grafias diferentes: {nome}."
            )

        limpas[nome] = cientifico.strip()

    for nome, cientifico in CFG["ESPECIES"].items():
        existente = next(
            (n for n in limpas if normal(n) == normal(nome)), None
        )
        if existente is None:
            limpas[nome] = cientifico

    dados["especies"] = limpas

    campos = {
        "registos": ["data", "categoria", "texto"],
        "plantel": ["anilha", "sexo", "ano", "casal"],
        "crias": [
            "anilha", "nascimento", "sexo", "casal", "ninhada",
            "observacoes", "pai_id", "pai_anilha",
            "mae_id", "mae_anilha", "plantel_id",
        ],
    }

    opcionais = [
        "pai_id", "mae_id", "pai_anilha", "mae_anilha",
        "nascimento", "cria_origem_id",
    ]

    for grupo, nomes in campos.items():
        lista = dados.setdefault(grupo, [])

        if not isinstance(lista, list):
            raise ValueError(f"O grupo '{grupo}' deve ser uma lista.")

        for item in lista:
            if not isinstance(item, dict):
                raise ValueError(f"Registo inválido em '{grupo}'.")

            item["id"] = str(item.get("id") or uid())

            for campo in nomes:
                valor = item.get(campo)
                item[campo] = "" if valor is None else str(valor).strip()

            if grupo == "plantel":
                for campo in opcionais:
                    if campo in item:
                        item[campo] = str(item[campo] or "").strip()

            especie = str(item.get("especie") or PADRAO).strip()

            if normal(especie) == normal(GERAL):
                if grupo != "registos":
                    raise ValueError("Uma ave não pode ter espécie geral.")
                especie = GERAL
            else:
                especie = next(
                    (
                        n for n in limpas
                        if normal(n) == normal(especie)
                    ),
                    especie,
                )
                limpas.setdefault(especie, "")

            item["especie"] = especie

            if grupo == "registos":
                item["categoria"] = item["categoria"] or "Geral"
            else:
                item["sexo"] = item["sexo"] or "Indeterminado"

    validar_dados(dados)
    return dados


# ============================================================
# INTEGRIDADE DOS DADOS
# ============================================================

def validar_dados(dados):
    ids = set()

    for grupo in ("registos", "plantel", "crias"):
        for item in dados[grupo]:
            identificador = item.get("id")

            if not identificador or identificador in ids:
                raise ValueError("Existem identificadores vazios ou repetidos.")

            ids.add(identificador)

            especie = item.get("especie")

            if especie not in dados["especies"]:
                if not (grupo == "registos" and especie == GERAL):
                    raise ValueError("Existe uma espécie inválida.")

    aves = {a["id"]: a for a in dados["plantel"]}
    ligacoes = {}
    anilhas = {}
    casais = {}

    for registo in dados["registos"]:
        data_valida(registo["data"], True)

        if registo["categoria"] not in CATEGORIAS:
            raise ValueError("Existe uma categoria inválida no Diário.")

        if not registo["texto"].strip():
            raise ValueError("Existe um registo do Diário sem texto.")

    for ave in dados["plantel"]:
        if (
            not ave["anilha"].strip()
            or ave["sexo"] not in SEXOS
            or not ano_valido(ave["ano"])
        ):
            raise ValueError(
                f"Ave com anilha, sexo ou ano inválido: {ave['anilha']}."
            )

        chave = normal(ave["anilha"])

        if chave in anilhas:
            raise ValueError(f"Anilha repetida: {ave['anilha']}.")

        anilhas[chave] = ave["id"]

        if ave.get("nascimento"):
            nascimento = data_valida(ave["nascimento"])

            if (
                nascimento.date() > datetime.now().date()
                or str(nascimento.year) != ave["ano"]
            ):
                raise ValueError(
                    f"Nascimento incoerente na ave {ave['anilha']}."
                )

        if ave["casal"].strip():
            chave_casal = (ave["especie"], normal(ave["casal"]))
            casais.setdefault(chave_casal, []).append(ave)

    for membros in casais.values():
        sexos = [a["sexo"] for a in membros]

        if (
            len(membros) > 2
            or sexos.count("Macho") > 1
            or sexos.count("Fêmea") > 1
            or (len(membros) > 1 and "Indeterminado" in sexos)
        ):
            raise ValueError(
                "Existe um casal com membros incompatíveis. "
                "Corrija a identificação do casal ou os sexos."
            )

    for cria in dados["crias"]:
        nascimento = data_valida(cria["nascimento"])

        if nascimento.date() > datetime.now().date():
            raise ValueError("Existe uma cria com nascimento futuro.")

        if cria["sexo"] not in SEXOS:
            raise ValueError("Existe uma cria com sexo inválido.")

        ligada_id = cria.get("plantel_id", "")
        ligada = aves.get(ligada_id)

        if ligada_id:
            if ligada is None:
                raise ValueError(
                    "Uma cria aponta para uma ave inexistente no Plantel."
                )

            if ligada_id in ligacoes:
                raise ValueError(
                    "Duas crias estão ligadas à mesma ave do Plantel."
                )

            ligacoes[ligada_id] = cria["id"]

            for campo in ("anilha", "sexo", "especie"):
                if cria[campo] != ligada[campo]:
                    raise ValueError(
                        "Uma cria e a respetiva ave do Plantel "
                        f"divergem no campo '{campo}'."
                    )

            if str(nascimento.year) != ligada["ano"]:
                raise ValueError(
                    "O nascimento de uma cria diverge do ano no Plantel."
                )

            if (
                ligada.get("nascimento")
                and ligada["nascimento"] != cria["nascimento"]
            ):
                raise ValueError(
                    "A data de nascimento diverge entre Crias e Plantel."
                )

            for campo in ("pai_id", "mae_id"):
                if ligada.get(campo, "") != cria.get(campo, ""):
                    raise ValueError(
                        "A filiação diverge entre Crias e Plantel."
                    )

        if cria["anilha"].strip():
            chave = normal(cria["anilha"])

            if chave in anilhas and anilhas[chave] != ligada_id:
                raise ValueError(f"Anilha repetida: {cria['anilha']}.")

            anilhas[chave] = "cria:" + cria["id"]

    # Grafo dos progenitores, incluindo identificadores históricos.
    grafo = {}

    for ave in dados["plantel"]:
        grafo[ave["id"]] = (
            ave.get("pai_id", ""), ave.get("mae_id", "")
        )

    for cria in dados["crias"]:
        if cria.get("plantel_id"):
            grafo[cria["plantel_id"]] = (
                cria.get("pai_id", ""), cria.get("mae_id", "")
            )

    for grupo in ("plantel", "crias"):
        for item in dados[grupo]:
            pai = item.get("pai_id", "")
            mae = item.get("mae_id", "")

            if pai and pai == mae:
                raise ValueError("Pai e mãe não podem ser a mesma ave.")

            nascimento = (
                data_valida(item["nascimento"])
                if item.get("nascimento") else None
            )

            for campo, sexo in (("pai_id", "Macho"), ("mae_id", "Fêmea")):
                progenitor = aves.get(item.get(campo, ""))

                # IDs históricos de aves já removidas são preservados.
                if progenitor is None:
                    continue

                if progenitor["especie"] != item["especie"]:
                    raise ValueError(
                        "A espécie não coincide com a dos progenitores."
                    )

                if progenitor["sexo"] != sexo:
                    raise ValueError(
                        "O sexo de um progenitor é incompatível "
                        "com a filiação registada."
                    )

                if nascimento:
                    if int(progenitor["ano"]) > nascimento.year:
                        raise ValueError(
                            "Uma cria não pode nascer antes "
                            "do ano de nascimento de um progenitor."
                        )

                    if progenitor.get("nascimento"):
                        if data_valida(progenitor["nascimento"]) >= nascimento:
                            raise ValueError(
                                "Um progenitor deve nascer antes da cria."
                            )

    # Pesquisa iterativa para evitar ciclos genealógicos.
    terminados = set()

    for inicio in grafo:
        ativos = set()
        pilha = [(inicio, False)]

        while pilha:
            atual, sair = pilha.pop()

            if not atual:
                continue

            if sair:
                ativos.discard(atual)
                terminados.add(atual)
                continue

            if atual in ativos:
                raise ValueError("Existe um ciclo genealógico.")

            if atual in terminados:
                continue

            ativos.add(atual)
            pilha.append((atual, True))

            for progenitor in grafo.get(atual, ()):
                if progenitor:
                    pilha.append((progenitor, False))


def aplicar(novos, mensagem):
    try:
        novos["versao"] = 7
        validar_dados(novos)
    except (ValueError, TypeError, KeyError) as erro:
        st.error(f"A alteração não foi aplicada: {erro}")
        return False

    st.session_state.dados = novos
    st.session_state.revisao += 1
    st.session_state.aviso = mensagem
    st.rerun()


def especie_alteravel(dados, ave, especie):
    if especie == ave["especie"]:
        return True

    if ave.get("pai_id") or ave.get("mae_id"):
        return False

    return not any(
        item.get("pai_id") == ave["id"]
        or item.get("mae_id") == ave["id"]
        or item.get("plantel_id") == ave["id"]
        for grupo in ("plantel", "crias")
        for item in dados[grupo]
    )


def sincronizar(dados):
    mapa = {a["id"]: a for a in dados["plantel"]}

    for cria in dados["crias"]:
        ave = mapa.get(cria.get("plantel_id"))

        if ave:
            for campo in ("anilha", "sexo", "especie"):
                cria[campo] = ave[campo]


# ============================================================
# SESSÃO
# ============================================================

if "dados" not in st.session_state:
    st.session_state.dados = novos_dados()
    st.session_state.revisao = 0
    st.session_state.assinatura_download = assinatura(
        st.session_state.dados
    )

if st.session_state.get("aviso"):
    st.success(st.session_state.pop("aviso"))

dados = st.session_state.dados
revisao = st.session_state.revisao

st.title("🐦 Aves Elite Manager")

st.warning(
    "Os dados ficam apenas nesta sessão. Depois das alterações, "
    "utiliza «Descarregar JSON». Fechar ou perder a sessão pode "
    "eliminar alterações ainda não descarregadas."
)

with st.expander("Importar / descarregar dados", expanded=False):
    ficheiro = st.file_uploader(
        "Importar o teu ficheiro de dados",
        type=["json"],
        key="ficheiro_importacao",
    )

    confirmar_importacao = st.checkbox(
        "Confirmo que a importação substitui todos os dados desta sessão."
    )

    if st.button(
        "Importar JSON",
        disabled=ficheiro is None or not confirmar_importacao,
    ):
        try:
            importados = preparar_importacao(ficheiro.getvalue())
        except Exception as erro:
            st.error(
                f"Importação cancelada: {erro} "
                "Os dados atuais não foram alterados."
            )
        else:
            st.session_state.dados = importados
            st.session_state.revisao += 1
            st.session_state.assinatura_download = assinatura(importados)
            st.session_state.aviso = "Dados importados."
            st.rerun()

    def marcar_download():
        st.session_state.assinatura_download = assinatura(
            st.session_state.dados
        )

    st.download_button(
        "Descarregar JSON",
        data=serializar(dados),
        file_name="dados_criacao_elite.json",
        mime="application/json",
        on_click=marcar_download,
    )

    st.caption(
        "O botão prepara a cópia dos dados guardados na sessão. "
        "Confirma que o navegador guardou o ficheiro. "
        "Campos de formulários ainda não submetidos não são incluídos."
    )

    if assinatura(dados) != st.session_state.assinatura_download:
        st.info("Existem alterações posteriores ao último pedido de download.")


especies = sorted(dados["especies"], key=natural)

topo, adicionar = st.columns([3, 2])

with topo:
    especie_global = st.selectbox(
        "Consultar espécie",
        [TODAS] + especies,
        key="especie_global",
    )

with adicionar:
    with st.expander("Adicionar espécie"):
        with st.form("adicionar_especie", clear_on_submit=True):
            nome = st.text_input("Nome comum")
            cientifico = st.text_input("Nome científico")
            adicionar_especie = st.form_submit_button("Adicionar")

        if adicionar_especie:
            nome = nome.strip()
            existentes = {normal(n) for n in especies + [TODAS, GERAL]}

            if not nome or normal(nome) in existentes:
                st.error("Indica um nome novo e válido.")
            else:
                novos = copy.deepcopy(dados)
                novos["especies"][nome] = cientifico.strip()
                aplicar(novos, "Espécie adicionada.")


inicial = especie_global if especie_global in especies else PADRAO

if inicial not in especies:
    inicial = especies[0]


def visivel(item):
    return (
        especie_global == TODAS
        or item["especie"] == especie_global
    )


# ============================================================
# TABELAS, FILTROS E CSV
# ============================================================

def tabela(grupo, itens, colunas, ordem):
    pesquisa = st.text_input(
        "Pesquisar",
        key=f"pesquisa_{grupo}",
    )

    termo = normal(pesquisa)
    itens = [
        item for item in itens
        if termo in normal(
            " ".join(str(item.get(c, "")) for c in colunas)
        )
    ]

    a, b = st.columns([3, 1])

    with a:
        ordenar = st.selectbox(
            "Ordenar por",
            list(colunas),
            index=list(colunas).index(ordem),
            format_func=lambda c: colunas[c],
            key=f"ordem_{grupo}",
        )

    with b:
        descendente = st.checkbox(
            "Decrescente",
            value=ordem in ("data", "nascimento"),
            key=f"desc_{grupo}",
        )

    def chave(item):
        valor = item.get(ordenar, "")

        if ordenar in ("data", "nascimento"):
            try:
                return data_valida(valor, ordenar == "data")
            except ValueError:
                return datetime.min

        return natural(valor)

    itens = sorted(itens, key=chave, reverse=descendente)

    linhas = [
        {titulo: item.get(campo, "") for campo, titulo in colunas.items()}
        for item in itens
    ]

    st.dataframe(linhas, use_container_width=True, hide_index=True)

    saida = io.StringIO(newline="")
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(colunas.values())

    def celula(valor):
        texto = str(valor or "")
        if texto.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + texto
        return texto

    for item in itens:
        escritor.writerow([
            celula(item.get(c, "")) for c in colunas
        ])

    st.download_button(
        "Exportar CSV",
        data=saida.getvalue().encode("utf-8-sig"),
        file_name=f"{grupo}.csv",
        mime="text/csv",
        key=f"csv_{grupo}",
    )

    mapa = {item["id"]: item for item in itens}

    def rotulo(identificador):
        if not identificador:
            return "Novo registo / nenhum selecionado"

        item = mapa[identificador]

        if grupo == "diario":
            return (
                f"{item['data']} — {item['especie']} — "
                f"{item['texto'][:70]}"
            )

        return (
            f"{item['especie']} — "
            f"{item.get('anilha') or 'Sem anilha'} — "
            f"{item.get('casal') or 'Sem casal'}"
        )

    selecionado = st.selectbox(
        "Selecionar registo para editar ou apagar",
        [""] + list(mapa),
        format_func=rotulo,
        key=f"selecionado_{grupo}_{revisao}",
    )

    st.caption(f"{len(itens)} registo(s) apresentados.")
    return mapa.get(selecionado)


def escolher_especie(rotulo, atual, key, geral=False):
    opcoes = ([GERAL] if geral else []) + especies
    return st.selectbox(
        rotulo,
        opcoes,
        index=opcoes.index(atual) if atual in opcoes else 0,
        key=key,
    )


def apagar(grupo, item, key):
    if not item:
        return

    confirmar = st.checkbox(
        "Confirmo que pretendo apagar este registo.",
        key=f"confirmar_{key}_{revisao}",
    )

    if st.button(
        "Apagar",
        disabled=not confirmar,
        key=f"apagar_{key}_{revisao}",
    ):
        novos = copy.deepcopy(dados)
        novos[grupo] = [
            r for r in novos[grupo] if r["id"] != item["id"]
        ]

        if grupo == "plantel":
            for cria in novos["crias"]:
                if cria.get("plantel_id") == item["id"]:
                    cria["plantel_id"] = ""

        aplicar(novos, "Registo apagado.")


# ============================================================
# SEPARADORES ORIGINAIS
# ============================================================

guia, alimentacao, diario, plantel, crias = st.tabs([
    "Guia de Cuidados",
    "Alimentação",
    "Diário de Manejo",
    "Plantel",
    "Crias",
])

perfil = CFG["PERFIS"].get(especie_global, {})

with guia:
    if especie_global != TODAS:
        st.subheader(especie_global)
        st.caption(dados["especies"].get(especie_global, ""))
        st.text(
            perfil.get(
                "cuidados",
                "Ainda não existe um perfil específico para esta espécie.",
            ).strip()
        )

    st.text(CFG["BASE_CUIDADOS"].strip())

    with st.expander("Como interpretar os conteúdos"):
        st.text(CFG["NOTA"].strip())


with alimentacao:
    modo = st.radio(
        "Consultar",
        ["Alimentação", "Ciclo Anual", "Fontes e limites"],
        horizontal=True,
    )

    campo, base = {
        "Alimentação": ("alimentacao", "BASE_ALIMENTACAO"),
        "Ciclo Anual": ("ciclo", "BASE_CICLO"),
        "Fontes e limites": ("fontes", "NOTA"),
    }[modo]

    if especie_global == TODAS:
        st.info("Seleciona uma espécie no topo para consultar o perfil.")
    else:
        st.subheader(especie_global)
        st.text(
            perfil.get(
                campo,
                "Ainda não existe conteúdo específico nesta secção.",
            ).strip()
        )

    st.text(CFG[base].strip())


# ============================================================
# DIÁRIO DE MANEJO
# ============================================================

with diario:
    filtro_categoria = st.selectbox(
        "Filtrar categoria",
        ["Todas"] + CATEGORIAS,
    )

    itens = [
        r for r in dados["registos"]
        if (visivel(r) or r["especie"] == GERAL)
        and (
            filtro_categoria == "Todas"
            or r["categoria"] == filtro_categoria
        )
    ]

    selecionado = tabela(
        "diario",
        itens,
        {
            "data": "Data",
            "especie": "Espécie",
            "categoria": "Categoria",
            "texto": "Registo",
        },
        "data",
    )

    atual = selecionado or {}
    token = f"d_{atual.get('id', 'novo')}_{revisao}"

    st.subheader("Editar registo" if selecionado else "Novo registo")

    with st.form(token):
        c1, c2, c3 = st.columns(3)

        with c1:
            especie = escolher_especie(
                "Espécie",
                atual.get("especie", inicial),
                token + "_especie",
                geral=True,
            )

        with c2:
            categoria = st.selectbox(
                "Categoria",
                CATEGORIAS,
                index=CATEGORIAS.index(atual.get("categoria", "Geral")),
            )

        with c3:
            data = st.text_input(
                "Data — DD/MM/AAAA HH:MM",
                value=atual.get(
                    "data", datetime.now().strftime(DATA_HORA)
                ),
            )

        texto = st.text_area("Registo", value=atual.get("texto", ""))
        guardar = st.form_submit_button(
            "Guardar alteração" if selecionado else "Registar"
        )

    if guardar:
        novo = dict(atual)
        novo.update(
            id=atual.get("id") or uid(),
            especie=especie,
            categoria=categoria,
            data=data.strip(),
            texto=texto.strip(),
        )

        novos = copy.deepcopy(dados)
        novos["registos"] = [
            r for r in novos["registos"] if r["id"] != novo["id"]
        ] + [novo]

        aplicar(novos, "Registo guardado na sessão.")

    apagar("registos", selecionado, "diario")


# ============================================================
# PLANTEL — CASAL E EDIÇÃO INDIVIDUAL
# ============================================================

with plantel:
    selecionada = tabela(
        "plantel",
        [a for a in dados["plantel"] if visivel(a)],
        {
            "especie": "Espécie",
            "anilha": "Anilha",
            "sexo": "Sexo",
            "ano": "Ano",
            "casal": "Casal",
        },
        "casal",
    )

    modo = st.radio(
        "Operação",
        ["Constituir / editar casal", "Editar ave individual"],
        horizontal=True,
    )

    if modo == "Constituir / editar casal":
        membros = []

        if selecionada:
            membros = [
                a for a in dados["plantel"]
                if a["especie"] == selecionada["especie"]
                and normal(a["casal"]) == normal(selecionada["casal"])
            ] if selecionada["casal"] else [selecionada]

        if any(a["sexo"] not in ("Macho", "Fêmea") for a in membros):
            st.info(
                "Esta ave tem sexo indeterminado. "
                "Utiliza «Editar ave individual»."
            )
        else:
            por_sexo = {a["sexo"]: a for a in membros}
            token = (
                f"p_casal_{selecionada['id'] if selecionada else 'novo'}"
                f"_{revisao}"
            )

            with st.form(token):
                c1, c2 = st.columns(2)

                with c1:
                    especie = escolher_especie(
                        "Espécie",
                        selecionada["especie"] if selecionada else inicial,
                        token + "_especie",
                    )

                with c2:
                    casal = st.text_input(
                        "Casal",
                        value=selecionada["casal"] if selecionada else "",
                    )

                valores = {}

                for coluna, sexo, titulo in zip(
                    st.columns(2),
                    ["Macho", "Fêmea"],
                    ["Macho — Pai", "Fêmea — Mãe"],
                ):
                    with coluna:
                        st.markdown(f"**{titulo}**")
                        ave = por_sexo.get(sexo, {})

                        anilha = st.text_input(
                            "Anilha",
                            value=ave.get("anilha", ""),
                            key=token + sexo + "_anilha",
                        )

                        ano = st.text_input(
                            "Ano",
                            value=ave.get("ano", ""),
                            key=token + sexo + "_ano",
                        )

                        valores[sexo] = (anilha.strip(), ano.strip())

                st.caption(
                    "Podes guardar apenas um membro e completar depois. "
                    "Para remover uma ave existente, utiliza «Apagar»."
                )

                guardar = st.form_submit_button("Guardar casal")

            if guardar:
                try:
                    if not casal.strip():
                        raise ValueError("Indica a identificação do casal.")

                    novos = copy.deepcopy(dados)
                    novas = []

                    for sexo, (anilha, ano) in valores.items():
                        anterior = por_sexo.get(sexo)

                        if not anilha and not ano:
                            if anterior:
                                raise ValueError(
                                    "Não apagues os campos de uma ave "
                                    "existente. Utiliza «Apagar»."
                                )
                            continue

                        if not anilha or not ano_valido(ano):
                            raise ValueError(
                                f"Indica anilha e ano válidos para {sexo}."
                            )

                        if anterior and not especie_alteravel(
                            dados, anterior, especie
                        ):
                            raise ValueError(
                                "Não é possível alterar isoladamente "
                                "a espécie de uma ave com genealogia."
                            )

                        nova = dict(anterior or {})
                        nova.update(
                            id=nova.get("id") or uid(),
                            especie=especie,
                            casal=casal.strip(),
                            sexo=sexo,
                            anilha=anilha,
                            ano=ano,
                        )
                        novas.append(nova)

                    if not novas:
                        raise ValueError("Preenche pelo menos uma ave.")

                    ids = {a["id"] for a in membros}

                    novos["plantel"] = [
                        a for a in novos["plantel"] if a["id"] not in ids
                    ] + novas

                    sincronizar(novos)
                    aplicar(novos, "Casal guardado na sessão.")

                except ValueError as erro:
                    st.error(str(erro))

    else:
        if selecionada is None:
            st.info("Seleciona uma ave na lista para a editar.")
        else:
            token = f"p_ave_{selecionada['id']}_{revisao}"

            with st.form(token):
                especie = escolher_especie(
                    "Espécie",
                    selecionada["especie"],
                    token + "_especie",
                )

                c1, c2 = st.columns(2)

                with c1:
                    anilha = st.text_input(
                        "Anilha", value=selecionada["anilha"]
                    )
                    ano = st.text_input(
                        "Ano", value=selecionada["ano"]
                    )

                with c2:
                    sexo = st.selectbox(
                        "Sexo",
                        SEXOS,
                        index=SEXOS.index(selecionada["sexo"]),
                    )
                    casal = st.text_input(
                        "Casal", value=selecionada["casal"]
                    )

                guardar = st.form_submit_button("Guardar ave")

            if guardar:
                if not especie_alteravel(dados, selecionada, especie):
                    st.error(
                        "Esta ave tem ligações genealógicas. "
                        "A alteração isolada da espécie foi bloqueada."
                    )
                else:
                    novos = copy.deepcopy(dados)
                    ave = procurar(novos, "plantel", selecionada["id"])

                    ave.update(
                        especie=especie,
                        anilha=anilha.strip(),
                        ano=ano.strip(),
                        sexo=sexo,
                        casal=casal.strip(),
                    )

                    sincronizar(novos)
                    aplicar(novos, "Ave guardada na sessão.")

    if selecionada:
        st.caption(
            "Apagar uma ave preserva as anilhas e os identificadores "
            "históricos dos progenitores nas crias."
        )

    apagar("plantel", selecionada, "plantel")


# ============================================================
# CRIAS
# ============================================================

with crias:
    pares = sorted(
        {
            (c["especie"], c["casal"])
            for c in dados["crias"]
            if visivel(c) and c["casal"]
        },
        key=lambda p: (natural(p[0]), natural(p[1])),
    )

    filtro = st.selectbox(
        "Casal de origem",
        [None] + pares,
        format_func=lambda p: "Todos" if p is None else f"{p[0]} — {p[1]}",
        key="filtro_casal_crias",
    )

    ids_aves = {a["id"] for a in dados["plantel"]}
    itens = []

    for cria in dados["crias"]:
        if not visivel(cria):
            continue

        if filtro and (
            cria["especie"] != filtro[0]
            or normal(cria["casal"]) != normal(filtro[1])
        ):
            continue

        item = dict(cria)
        item["situacao"] = (
            "Sim" if cria.get("plantel_id") in ids_aves else "Não"
        )
        itens.append(item)

    selecionada = tabela(
        "crias",
        itens,
        {
            "especie": "Espécie",
            "anilha": "Anilha",
            "nascimento": "Nascimento",
            "sexo": "Sexo",
            "casal": "Casal de origem",
            "ninhada": "Ninhada",
            "pai_anilha": "Pai",
            "mae_anilha": "Mãe",
            "situacao": "No Plantel",
            "observacoes": "Observações",
        },
        "nascimento",
    )

    atual = selecionada or {}
    token = f"c_{atual.get('id', 'nova')}_{revisao}"

    st.subheader("Editar cria" if selecionada else "Registar cria")

    # Espécie e casal fora do formulário:
    # a lista de casais atualiza imediatamente ao mudar de espécie.
    especie = escolher_especie(
        "Espécie da cria",
        atual.get("especie", inicial),
        token + "_especie",
    )

    substituir = False

    if selecionada:
        st.info(
            f"Filiação histórica: "
            f"Pai: {atual.get('pai_anilha') or 'não indicado'} | "
            f"Mãe: {atual.get('mae_anilha') or 'não indicada'}."
        )

        substituir = st.checkbox(
            "Substituir a filiação histórica pelos membros atuais "
            "de um casal. Confirmo esta alteração.",
            key=token + "_substituir",
        )

    usar_atual = selecionada is not None and not substituir

    filiacao = None
    casal = atual.get("casal", "")

    if usar_atual:
        filiacao = {
            c: atual.get(c, "")
            for c in ("pai_id", "pai_anilha", "mae_id", "mae_anilha")
        }
        st.caption(f"Casal de origem preservado: {casal or 'não indicado'}")
    else:
        mapa_casais = {}

        for ave in dados["plantel"]:
            if ave["especie"] == especie and ave["casal"].strip():
                mapa_casais.setdefault(
                    normal(ave["casal"]), []
                ).append(ave)

        opcoes = {
            chave: membros
            for chave, membros in mapa_casais.items()
            if len(membros) == 2
            and {a["sexo"] for a in membros} == {"Macho", "Fêmea"}
        }

        escolha = st.selectbox(
            "Selecionar casal com macho e fêmea",
            [""] + sorted(opcoes, key=natural),
            format_func=lambda c: (
                "Selecionar…" if not c else opcoes[c][0]["casal"]
            ),
            key=token + "_casal_" + especie,
        )

        if escolha:
            membros = opcoes[escolha]
            pai = next(a for a in membros if a["sexo"] == "Macho")
            mae = next(a for a in membros if a["sexo"] == "Fêmea")
            casal = membros[0]["casal"]

            filiacao = {
                "pai_id": pai["id"],
                "pai_anilha": pai["anilha"],
                "mae_id": mae["id"],
                "mae_anilha": mae["anilha"],
            }

            st.caption(
                f"Pai: {pai['anilha']} | Mãe: {mae['anilha']}"
            )

        if not opcoes:
            st.info(
                "Não existem casais completos desta espécie. "
                "Constitui primeiro um casal no Plantel."
            )

    with st.form(token):
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            anilha = st.text_input(
                "Anilha", value=atual.get("anilha", "")
            )

        with c2:
            nascimento = st.text_input(
                "Nascimento — DD/MM/AAAA",
                value=atual.get(
                    "nascimento", datetime.now().strftime(DATA)
                ),
            )

        with c3:
            sexo = st.selectbox(
                "Sexo",
                SEXOS,
                index=SEXOS.index(
                    atual.get("sexo", "Indeterminado")
                ),
            )

        with c4:
            ninhada = st.text_input(
                "Ninhada", value=atual.get("ninhada", "")
            )

        observacoes = st.text_area(
            "Observações",
            value=atual.get("observacoes", ""),
        )

        st.caption(
            "A anilha pode ficar vazia até à identificação da cria. "
            "A saída do ninho não demonstra autonomia alimentar."
        )

        guardar = st.form_submit_button(
            "Guardar alteração" if selecionada else "Guardar cria"
        )

    if guardar:
        try:
            if filiacao is None or not casal:
                raise ValueError("Seleciona um casal e uma filiação válida.")

            if usar_atual and especie != atual["especie"]:
                raise ValueError(
                    "Para mudar a espécie, confirma primeiro "
                    "a substituição da filiação histórica."
                )

            nascimento_dt = data_valida(nascimento)
            ligada = procurar(
                dados, "plantel", atual.get("plantel_id")
            )

            if ligada and (
                not anilha.strip()
                or sexo != ligada["sexo"]
                or especie != ligada["especie"]
            ):
                raise ValueError(
                    "Uma cria no Plantel deve manter anilha, sexo "
                    "e espécie coerentes. Altera o sexo no Plantel."
                )

            nova = dict(atual)
            nova.pop("situacao", None)
            nova.update(
                id=atual.get("id") or uid(),
                especie=especie,
                casal=casal,
                anilha=anilha.strip(),
                nascimento=nascimento_dt.strftime(DATA),
                sexo=sexo,
                ninhada=ninhada.strip(),
                observacoes=observacoes.strip(),
                plantel_id=atual.get("plantel_id", ""),
            )
            nova.update(filiacao)

            novos = copy.deepcopy(dados)
            novos["crias"] = [
                c for c in novos["crias"] if c["id"] != nova["id"]
            ] + [nova]

            if ligada:
                ave = procurar(novos, "plantel", ligada["id"])

                for campo in (
                    "anilha", "nascimento", "ninhada", "observacoes",
                    "pai_id", "pai_anilha", "mae_id", "mae_anilha",
                ):
                    ave[campo] = nova[campo]

                ave["ano"] = str(nascimento_dt.year)
                ave["casal_origem"] = nova["casal"]

            aplicar(novos, "Cria guardada na sessão.")

        except ValueError as erro:
            st.error(str(erro))

    if selecionada:
        st.markdown("**Passar para o Plantel**")
        st.caption(
            "A transferência utiliza o registo já guardado, não os "
            "campos pendentes do formulário. A cria permanece em Crias."
        )

        ligada = selecionada.get("plantel_id") in ids_aves

        confirmar_transferencia = st.checkbox(
            "Confirmo a transferência do registo guardado, "
            "sem casal atribuído.",
            key=token + "_confirmar_transferencia",
            disabled=ligada,
        )

        if st.button(
            "Passar para o Plantel",
            key=token + "_transferir",
            disabled=ligada or not confirmar_transferencia,
        ):
            if not selecionada["anilha"].strip():
                st.error(
                    "Guarda primeiro uma anilha para esta cria."
                )
            else:
                novos = copy.deepcopy(dados)
                cria = procurar(
                    novos, "crias", selecionada["id"]
                )

                ave = dict(cria)
                ave.update(
                    id=uid(),
                    ano=str(data_valida(cria["nascimento"]).year),
                    casal="",
                    casal_origem=cria["casal"],
                    cria_origem_id=cria["id"],
                )
                ave.pop("plantel_id", None)
                ave.pop("situacao", None)

                novos["plantel"].append(ave)
                cria["plantel_id"] = ave["id"]

                aplicar(
                    novos,
                    "Cria adicionada ao Plantel, sem casal atribuído.",
                )

        if ligada:
            st.caption("Esta cria já está no Plantel.")

    st.caption(
        "Apagar uma cria não apaga a ave já transferida para o Plantel."
    )
    apagar("crias", selecionada, "crias")


# ============================================================
# RODAPÉ
# ============================================================

casais = {
    (a["especie"], normal(a["casal"]))
    for a in dados["plantel"]
    if a["casal"].strip()
}

st.caption(
    f"{len(dados['registos'])} registos | "
    f"{len(dados['plantel'])} aves | "
    f"{len(casais)} identificações de casal | "
    f"{len(dados['crias'])} crias | "
    f"{len(dados['especies'])} espécies"
)

st.caption(
    "Nos formulários, as alterações só entram nos dados após carregar "
    "em Registar/Guardar. Antes de mudar de registo ou importar dados, "
    "guarda os campos que pretendes conservar. Para sair de uma edição, "
    "seleciona «Novo registo / nenhum selecionado»."
)
