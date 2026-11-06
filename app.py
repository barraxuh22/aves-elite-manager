import ast
import copy
import csv
import hashlib
import io
import json
import uuid
from datetime import date, datetime
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Aves Elite Manager",
    page_icon="🐦",
    layout="wide",
)

DATA = "%d/%m/%Y"
DATA_HORA = "%d/%m/%Y %H:%M"
GERAL = "Geral — todas as espécies"
TODAS = "Todas as espécies"


# ============================================================
# LER APENAS AS CONSTANTES DO CÓDIGO ORIGINAL
# Não importa tkinter nem executa o ficheiro.
# ============================================================

@st.cache_data
def carregar_conteudos(texto):
    nomes = {
        "ESPECIES",
        "PERFIS",
        "NOTA",
        "BASE_CUIDADOS",
        "BASE_ALIMENTACAO",
        "BASE_CICLO",
        "SEXOS",
        "CATEGORIAS",
    }
    resultado = {}
    arvore = ast.parse(texto)

    for no in arvore.body:
        if not isinstance(no, ast.Assign):
            continue
        for alvo in no.targets:
            if isinstance(alvo, ast.Name) and alvo.id in nomes:
                resultado[alvo.id] = ast.literal_eval(no.value)

    faltam = nomes - resultado.keys()
    if faltam:
        raise ValueError(
            "Faltam constantes no código original: "
            + ", ".join(sorted(faltam))
        )
    return resultado


try:
    caminho = Path(__file__).resolve().parent / "aves_elite_manager.py"
    CONFIG = carregar_conteudos(caminho.read_text(encoding="utf-8-sig"))
except Exception as erro:
    st.error(
        "Não foi possível ler os conteúdos. Coloca o ficheiro "
        "'aves_elite_manager.py' na mesma pasta de 'app.py'."
    )
    st.code(str(erro))
    st.stop()

SEXOS = CONFIG["SEXOS"]
CATEGORIAS = CONFIG["CATEGORIAS"]


# ============================================================
# DADOS E VALIDAÇÃO
# ============================================================

def uid():
    return uuid.uuid4().hex


def normal(valor):
    return str(valor).strip().casefold()


def dados_vazios():
    return {
        "versao": 7,
        "especies": dict(CONFIG["ESPECIES"]),
        "plantel": [],
        "crias": [],
        "registos": [],
    }


def ler_data(texto, hora=False):
    return datetime.strptime(
        str(texto).strip(), DATA_HORA if hora else DATA
    )


def normalizar_dados(originais):
    if isinstance(originais, list):
        originais = {"registos": originais}
    if not isinstance(originais, dict):
        raise ValueError("A estrutura principal deve ser um objeto JSON.")

    dados = copy.deepcopy(originais)
    especies = dados.setdefault("especies", {})
    if not isinstance(especies, dict):
        raise ValueError("'especies' deve ser um objeto.")

    for nome, cientifico in CONFIG["ESPECIES"].items():
        especies.setdefault(nome, cientifico)

    if any(
        not isinstance(n, str)
        or not n.strip()
        or n in (GERAL, TODAS)
        or not isinstance(c, str)
        for n, c in especies.items()
    ):
        raise ValueError("A lista de espécies contém valores inválidos.")

    campos = {
        "plantel": ["anilha", "sexo", "ano", "casal"],
        "crias": [
            "anilha", "sexo", "nascimento", "casal", "ninhada",
            "observacoes", "pai_id", "pai_anilha",
            "mae_id", "mae_anilha", "plantel_id",
        ],
        "registos": ["data", "categoria", "texto"],
    }
    ids = set()

    for grupo, nomes in campos.items():
        itens = dados.setdefault(grupo, [])
        if not isinstance(itens, list):
            raise ValueError(f"'{grupo}' deve ser uma lista.")

        for item in itens:
            if not isinstance(item, dict):
                raise ValueError(f"Existe um registo inválido em '{grupo}'.")

            item["id"] = str(item.get("id") or uid())
            if item["id"] in ids:
                raise ValueError("Existem identificadores repetidos.")
            ids.add(item["id"])

            for campo in nomes:
                valor = item.get(campo, "")
                item[campo] = "" if valor is None else str(valor)

            item["especie"] = str(
                item.get("especie") or "Pintassilgo parva"
            )
            if item["especie"] == GERAL:
                if grupo != "registos":
                    raise ValueError("Uma ave não pode ter espécie geral.")
            else:
                especies.setdefault(item["especie"], "")

            if grupo == "registos":
                item["categoria"] = item["categoria"] or "Geral"
                try:
                    ler_data(item["data"], True)
                except ValueError:
                    ler_data(item["data"])
            else:
                item["sexo"] = item["sexo"] or "Indeterminado"
                if item["sexo"] not in SEXOS:
                    raise ValueError("Existe uma ave com sexo inválido.")
                if grupo == "plantel":
                    ano = item["ano"]
                    if not (
                        ano.isdigit()
                        and len(ano) == 4
                        and 1900 <= int(ano) <= date.today().year
                    ):
                        raise ValueError("Existe uma ave com ano inválido.")
                else:
                    nascimento = ler_data(item["nascimento"])
                    if not 1900 <= nascimento.year <= date.today().year:
                        raise ValueError("Existe uma data inválida.")
                    if nascimento.date() > date.today():
                        raise ValueError("Existe uma cria com data futura.")

    aves = {a["id"]: a for a in dados["plantel"]}
    ligacoes = set()
    donos_anilhas = {}

    for grupo in ("plantel", "crias"):
        for item in dados[grupo]:
            dono = item["id"]
            if grupo == "crias" and item.get("plantel_id"):
                ligado = item["plantel_id"]
                if ligado not in aves:
                    raise ValueError(
                        "Uma cria aponta para uma ave inexistente no Plantel."
                    )
                if ligado in ligacoes:
                    raise ValueError(
                        "Duas crias estão ligadas à mesma ave."
                    )
                ligacoes.add(ligado)
                ave = aves[ligado]
                for campo in ("anilha", "sexo", "especie"):
                    if item[campo] != ave[campo]:
                        raise ValueError(
                            "Uma cria não coincide com a ave ligada no Plantel."
                        )
                if str(ler_data(item["nascimento"]).year) != ave["ano"]:
                    raise ValueError(
                        "O nascimento da cria não coincide com o ano no Plantel."
                    )
                dono = ligado

            anilha = normal(item.get("anilha", ""))
            if grupo == "plantel" and not anilha:
                raise ValueError("Existe uma ave do Plantel sem anilha.")
            if anilha:
                if (
                    anilha in donos_anilhas
                    and donos_anilhas[anilha] != dono
                ):
                    raise ValueError("Existem anilhas repetidas.")
                donos_anilhas[anilha] = dono

    # Validar filiação conhecida, preservando referências históricas
    # de progenitores que já não estão no Plantel.
    grafo = {
        a["id"]: (a.get("pai_id", ""), a.get("mae_id", ""))
        for a in dados["plantel"]
    }

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
            for progenitor in (pai, mae):
                if (
                    progenitor in aves
                    and aves[progenitor]["especie"] != item["especie"]
                ):
                    raise ValueError(
                        "A espécie não coincide com a dos progenitores."
                    )

    for origem in grafo:
        pendentes = list(grafo[origem])
        vistos = set()
        while pendentes:
            atual = pendentes.pop()
            if not atual:
                continue
            if atual == origem:
                raise ValueError("Existe um ciclo genealógico.")
            if atual in vistos:
                continue
            vistos.add(atual)
            pendentes.extend(grafo.get(atual, ()))

    dados["versao"] = 7
    return dados


if "dados" not in st.session_state:
    st.session_state.dados = dados_vazios()
    st.session_state.alterado = False
    st.session_state.revisao = 0


def guardar(novos):
    try:
        validados = normalizar_dados(novos)
    except (ValueError, TypeError) as erro:
        st.error(str(erro))
        return

    st.session_state.dados = validados
    st.session_state.alterado = True
    st.session_state.revisao += 1
    st.session_state.aviso = "Alteração aplicada. Descarrega o JSON atualizado."
    st.rerun()


def substituir(grupo, item):
    novos = copy.deepcopy(st.session_state.dados)
    novos[grupo] = [
        x for x in novos[grupo] if x["id"] != item["id"]
    ] + [item]
    guardar(novos)


def indice(opcoes, valor):
    return opcoes.index(valor) if valor in opcoes else 0


def etiqueta(item):
    return (
        f"{item.get('anilha') or 'Sem anilha'}"
        f" — {item.get('especie', '')}"
        f" — {item.get('casal', '')}"
        f" [{item['id'][:8]}]"
    )


def selecionar(itens, chave):
    mapa = {x["id"]: x for x in itens}
    escolhido = st.selectbox(
        "Registo",
        [""] + list(mapa),
        format_func=lambda x: "Novo registo" if not x else etiqueta(mapa[x]),
        key=chave,
    )
    return copy.deepcopy(mapa.get(escolhido, {}))


def csv_bytes(itens, campos):
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(campos)
    for item in itens:
        linha = []
        for campo in campos:
            texto = str(item.get(campo, ""))
            if texto.lstrip().startswith(("=", "+", "-", "@")):
                texto = "'" + texto
            linha.append(texto)
        escritor.writerow(linha)
    return saida.getvalue().encode("utf-8-sig")


def mostrar_tabela(itens, campos, nome):
    if not itens:
        st.info("Não existem registos para estes filtros.")
        return
    st.dataframe(
        [{campo: x.get(campo, "") for campo in campos} for x in itens],
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Exportar esta tabela em CSV",
        csv_bytes(itens, campos),
        file_name=f"{nome}.csv",
        mime="text/csv",
        key=f"csv_{nome}",
    )


# ============================================================
# IMPORTAÇÃO E EXPORTAÇÃO
# ============================================================

st.title("🐦 Aves Elite Manager")
st.caption("Plantel, casais, crias, diário e guias por espécie.")

if "aviso" in st.session_state:
    st.success(st.session_state.pop("aviso"))

with st.sidebar:
    st.header("Os teus dados")
    st.warning(
        "Sem gravação permanente na nuvem. Importa o teu JSON "
        "e descarrega uma cópia atualizada antes de sair."
    )

    ficheiro = st.file_uploader("Importar JSON", type=["json"])
    confirmar_importacao = st.checkbox(
        "Confirmo que a importação substitui os dados desta sessão."
    )
    if st.button(
        "Carregar ficheiro",
        disabled=ficheiro is None or not confirmar_importacao,
    ):
        try:
            if ficheiro.size > 10 * 1024 * 1024:
                raise ValueError("O ficheiro deve ter no máximo 10 MB.")
            novos = normalizar_dados(
                json.loads(ficheiro.getvalue().decode("utf-8-sig"))
            )
        except Exception as erro:
            st.error(f"Não foi possível importar: {erro}")
        else:
            st.session_state.dados = novos
            st.session_state.alterado = False
            st.session_state.revisao += 1
            st.session_state.aviso = "Dados importados."
            st.rerun()

    dados_json = json.dumps(
        st.session_state.dados, ensure_ascii=False, indent=4
    )
    st.download_button(
        "💾 Descarregar JSON atualizado",
        dados_json,
        file_name=(
            "dados_criacao_elite_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".json"
        ),
        mime="application/json",
        use_container_width=True,
    )
    if st.session_state.alterado:
        st.caption(
            "Houve alterações nesta sessão. Guarda uma cópia atualizada; "
            "este aviso não confirma se já a descarregaste."
        )

dados = st.session_state.dados
especies = sorted(dados["especies"], key=str.casefold)
rev = st.session_state.revisao

with st.sidebar:
    filtro = st.selectbox("Consultar espécie", [TODAS] + especies)
    pesquisa = st.text_input("Pesquisar registos").strip().casefold()

    with st.expander("Adicionar espécie"):
        with st.form("nova_especie"):
            nome = st.text_input("Nome comum")
            cientifico = st.text_input("Nome científico")
            adicionar = st.form_submit_button("Adicionar")
        if adicionar:
            nome = nome.strip()
            existentes = {normal(x) for x in especies + [GERAL, TODAS]}
            if not nome or normal(nome) in existentes:
                st.error("Indica um nome novo e válido.")
            else:
                novos = copy.deepcopy(dados)
                novos["especies"][nome] = cientifico.strip()
                guardar(novos)


def visiveis(grupo):
    resultado = []
    for item in dados[grupo]:
        if (
            filtro != TODAS
            and item["especie"] != filtro
            and not (grupo == "registos" and item["especie"] == GERAL)
        ):
            continue
        if pesquisa and pesquisa not in normal(
            " ".join(str(v) for v in item.values())
        ):
            continue
        resultado.append(item)
    return resultado


def campo_especie(valor=None):
    inicial = valor or (filtro if filtro != TODAS else especies[0])
    return st.selectbox(
        "Espécie", especies, index=indice(especies, inicial)
    )


def apagar(grupo, item):
    if not item:
        return
    with st.expander("Apagar este registo"):
        confirmado = st.checkbox(
            "Confirmo a eliminação",
            key=f"confirmar_{grupo}_{item['id']}_{rev}",
        )
        if st.button(
            "Apagar definitivamente",
            disabled=not confirmado,
            key=f"apagar_{grupo}_{item['id']}_{rev}",
        ):
            novos = copy.deepcopy(dados)
            novos[grupo] = [
                x for x in novos[grupo] if x["id"] != item["id"]
            ]
            if grupo == "plantel":
                for cria in novos["crias"]:
                    if cria.get("plantel_id") == item["id"]:
                        cria["plantel_id"] = ""
            guardar(novos)


abas = st.tabs([
    "Guia de Cuidados", "Alimentação e Ciclo",
    "Plantel", "Casais", "Crias", "Diário",
])

# ============================================================
# GUIAS
# ============================================================

with abas[0]:
    if filtro != TODAS:
        st.subheader(filtro)
        st.caption(dados["especies"].get(filtro, ""))
        perfil = CONFIG["PERFIS"].get(filtro, {})
        st.text(perfil.get("cuidados", "Sem perfil específico."))
    st.text(CONFIG["BASE_CUIDADOS"])
    with st.expander("Como interpretar os conteúdos"):
        st.text(CONFIG["NOTA"])

with abas[1]:
    modo = st.radio(
        "Conteúdo",
        ["Alimentação", "Ciclo anual", "Fontes e limites"],
        horizontal=True,
    )
    campo, base = {
        "Alimentação": ("alimentacao", "BASE_ALIMENTACAO"),
        "Ciclo anual": ("ciclo", "BASE_CICLO"),
        "Fontes e limites": ("fontes", "NOTA"),
    }[modo]
    if filtro != TODAS:
        st.subheader(filtro)
        st.text(
            CONFIG["PERFIS"].get(filtro, {}).get(
                campo, "Sem conteúdo específico."
            )
        )
    st.text(CONFIG[base])

# ============================================================
# PLANTEL
# ============================================================

with abas[2]:
    st.subheader("Plantel")
    itens = visiveis("plantel")
    mostrar_tabela(
        itens, ["especie", "anilha", "sexo", "ano", "casal"], "plantel"
    )
    item = selecionar(itens, f"editar_plantel_{rev}")
    with st.form(f"plantel_{item.get('id', 'novo')}_{rev}"):
        especie = campo_especie(item.get("especie"))
        anilha = st.text_input("Anilha", item.get("anilha", ""))
        sexo = st.selectbox(
            "Sexo", SEXOS, index=indice(SEXOS, item.get("sexo"))
        )
        ano = st.number_input(
            "Ano de nascimento",
            min_value=1900,
            max_value=date.today().year,
            value=int(item.get("ano") or date.today().year),
            step=1,
        )
        casal = st.text_input("Casal — opcional", item.get("casal", ""))
        enviado = st.form_submit_button("Guardar ave")

    if enviado:
        nova = dict(item)
        nova.update(
            id=item.get("id") or uid(),
            especie=especie, anilha=anilha.strip(),
            sexo=sexo, ano=str(ano), casal=casal.strip(),
        )
        outros = [
            a for a in dados["plantel"] if a["id"] != nova["id"]
        ]
        ocupantes = [
            a for a in outros
            if casal.strip()
            and a["especie"] == especie
            and normal(a["casal"]) == normal(casal)
        ]
        ligada = any(
            c.get("plantel_id") == nova["id"] for c in dados["crias"]
        )
        historico = (
            item.get("pai_id") or item.get("mae_id") or ligada
            or any(
                x.get("pai_id") == nova["id"]
                or x.get("mae_id") == nova["id"]
                for grupo in ("plantel", "crias")
                for x in dados[grupo]
            )
        )

        if (
            item
            and especie != item["especie"]
            and historico
        ):
            st.error("Não alteres isoladamente a espécie de uma ave com genealogia.")
        elif ocupantes and (
            len(ocupantes) > 1
            or sexo == "Indeterminado"
            or any(a["sexo"] in (sexo, "Indeterminado") for a in ocupantes)
        ):
            st.error("O casal já tem membros incompatíveis.")
        else:
            novos = copy.deepcopy(dados)
            novos["plantel"] = outros + [nova]
            for cria in novos["crias"]:
                if cria.get("plantel_id") == nova["id"]:
                    for campo in ("anilha", "sexo", "especie"):
                        cria[campo] = nova[campo]
            guardar(novos)
    apagar("plantel", item)

# ============================================================
# CASAIS
# ============================================================

with abas[3]:
    st.subheader("Casais")
    st.caption(
        "Para constituir um casal, atribui a mesma identificação "
        "a um macho e a uma fêmea da mesma espécie no Plantel."
    )
    grupos = {}
    for ave in dados["plantel"]:
        if ave["casal"].strip():
            chave = (ave["especie"], normal(ave["casal"]))
            grupos.setdefault(chave, []).append(ave)

    linhas = []
    for (especie, _), membros in grupos.items():
        if filtro != TODAS and especie != filtro:
            continue
        machos = [a["anilha"] for a in membros if a["sexo"] == "Macho"]
        femeas = [a["anilha"] for a in membros if a["sexo"] == "Fêmea"]
        linhas.append({
            "especie": especie,
            "casal": membros[0]["casal"],
            "macho": ", ".join(machos),
            "femea": ", ".join(femeas),
            "estado": (
                "Completo"
                if len(membros) == 2 and len(machos) == len(femeas) == 1
                else "Incompleto ou incompatível"
            ),
        })
    mostrar_tabela(
        linhas, ["especie", "casal", "macho", "femea", "estado"], "casais"
    )

# ============================================================
# CRIAS
# ============================================================

with abas[4]:
    st.subheader("Crias")
    itens = visiveis("crias")
    mostrar_tabela(
        itens,
        [
            "especie", "anilha", "nascimento", "sexo",
            "casal", "ninhada", "pai_anilha", "mae_anilha",
            "observacoes",
        ],
        "crias",
    )
    item = selecionar(itens, f"editar_cria_{rev}")

    # Escolha fora do formulário para atualizar os casais disponíveis.
    especie = st.selectbox(
        "Espécie da cria",
        especies,
        index=indice(especies, item.get("especie") or (
            filtro if filtro != TODAS else especies[0]
        )),
        key=f"especie_cria_{item.get('id', 'nova')}_{rev}",
    )

    casais = {}
    for (esp, chave), membros in grupos.items():
        machos = [a for a in membros if a["sexo"] == "Macho"]
        femeas = [a for a in membros if a["sexo"] == "Fêmea"]
        if (
            esp == especie and len(membros) == 2
            and len(machos) == len(femeas) == 1
        ):
            casais[chave] = (membros[0]["casal"], machos[0], femeas[0])

    with st.form(f"cria_{item.get('id', 'nova')}_{rev}_{especie}"):
        opcoes = [""] + list(casais)
        escolha = st.selectbox(
            "Casal atual — para nova filiação",
            opcoes,
            format_func=lambda x: "Selecionar…" if not x else casais[x][0],
        )
        preservar = False
        if item and especie == item["especie"]:
            preservar = st.checkbox(
                "Manter a filiação histórica deste registo", value=True
            )
            st.caption(
                f"Pai: {item.get('pai_anilha', '')} | "
                f"Mãe: {item.get('mae_anilha', '')}"
            )
        anilha = st.text_input(
            "Anilha — pode ficar vazia", item.get("anilha", "")
        )
        nascimento = st.date_input(
            "Nascimento",
            value=(
                ler_data(item["nascimento"]).date()
                if item else date.today()
            ),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            format="DD/MM/YYYY",
        )
        sexo = st.selectbox(
            "Sexo", SEXOS, index=indice(SEXOS, item.get("sexo"))
        )
        ninhada = st.text_input("Ninhada", item.get("ninhada", ""))
        observacoes = st.text_area(
            "Observações", item.get("observacoes", "")
        )
        enviado = st.form_submit_button("Guardar cria")

    if enviado:
        nova = dict(item)
        if preservar:
            filiacao = {
                c: item.get(c, "")
                for c in (
                    "casal", "pai_id", "pai_anilha", "mae_id", "mae_anilha"
                )
            }
        elif escolha:
            nome_casal, pai, mae = casais[escolha]
            filiacao = {
                "casal": nome_casal,
                "pai_id": pai["id"], "pai_anilha": pai["anilha"],
                "mae_id": mae["id"], "mae_anilha": mae["anilha"],
            }
        else:
            filiacao = None

        if filiacao is None:
            st.error("Seleciona um casal completo ou mantém a filiação histórica.")
        elif item.get("plantel_id") and (
            sexo != item["sexo"] or especie != item["especie"]
        ):
            st.error("Altera o sexo no Plantel. A espécie ligada não pode mudar aqui.")
        else:
            nova.update(
                id=item.get("id") or uid(),
                especie=especie, anilha=anilha.strip(),
                nascimento=nascimento.strftime(DATA),
                sexo=sexo, ninhada=ninhada.strip(),
                observacoes=observacoes.strip(),
                plantel_id=item.get("plantel_id", ""),
            )
            nova.update(filiacao)
            novos = copy.deepcopy(dados)
            novos["crias"] = [
                c for c in novos["crias"] if c["id"] != nova["id"]
            ] + [nova]
            for ave in novos["plantel"]:
                if ave["id"] == nova.get("plantel_id"):
                    ave.update(
                        anilha=nova["anilha"],
                        nascimento=nova["nascimento"],
                        ano=str(nascimento.year),
                        casal_origem=nova["casal"],
                        ninhada=nova["ninhada"],
                        observacoes=nova["observacoes"],
                    )
                    for campo in (
                        "pai_id", "pai_anilha", "mae_id", "mae_anilha"
                    ):
                        ave[campo] = nova.get(campo, "")
            guardar(novos)

    if item and not item.get("plantel_id"):
        if st.button("Passar esta cria para o Plantel", key=f"transferir_{rev}"):
            if not item["anilha"].strip():
                st.error("Preenche primeiro a anilha da cria.")
            else:
                novos = copy.deepcopy(dados)
                ave = dict(item)
                ave.update(
                    id=uid(),
                    ano=str(ler_data(item["nascimento"]).year),
                    casal="",
                    casal_origem=item["casal"],
                    cria_origem_id=item["id"],
                )
                ave.pop("plantel_id", None)
                novos["plantel"].append(ave)
                for cria in novos["crias"]:
                    if cria["id"] == item["id"]:
                        cria["plantel_id"] = ave["id"]
                guardar(novos)
    elif item:
        st.info("Esta cria já está ligada ao Plantel.")

    st.caption("Apagar uma cria não elimina a ave já transferida para o Plantel.")
    apagar("crias", item)

# ============================================================
# DIÁRIO
# ============================================================

with abas[5]:
    st.subheader("Diário de manejo")
    itens = visiveis("registos")
    mostrar_tabela(
        itens, ["data", "especie", "categoria", "texto"], "diario"
    )

    mapa = {x["id"]: x for x in itens}
    escolhido = st.selectbox(
        "Registo do diário",
        [""] + list(mapa),
        format_func=lambda x: (
            "Novo registo" if not x
            else f"{mapa[x]['data']} — {mapa[x]['texto'][:65]}"
        ),
        key=f"editar_diario_{rev}",
    )
    item = copy.deepcopy(mapa.get(escolhido, {}))
    opcoes_especie = [GERAL] + especies
    categorias = list(CATEGORIAS)
    if item.get("categoria") and item["categoria"] not in categorias:
        categorias.append(item["categoria"])

    with st.form(f"diario_{escolhido or 'novo'}_{rev}"):
        especie = st.selectbox(
            "Espécie",
            opcoes_especie,
            index=indice(
                opcoes_especie,
                item.get("especie") or (
                    filtro if filtro != TODAS else GERAL
                ),
            ),
        )
        categoria = st.selectbox(
            "Categoria",
            categorias,
            index=indice(categorias, item.get("categoria", "Geral")),
        )
        data_texto = st.text_input(
            "Data e hora — DD/MM/AAAA HH:MM",
            item.get("data") or datetime.now().strftime(DATA_HORA),
        )
        texto = st.text_area("Registo", item.get("texto", ""))
        enviado = st.form_submit_button("Guardar registo")

    if enviado:
        try:
            momento = ler_data(data_texto, True)
            if momento.year < 1900:
                raise ValueError()
        except ValueError:
            st.error("Usa uma data válida no formato DD/MM/AAAA HH:MM.")
        else:
            if not texto.strip():
                st.error("Escreve o registo.")
            else:
                novo = dict(item)
                novo.update(
                    id=item.get("id") or uid(),
                    especie=especie,
                    categoria=categoria,
                    data=momento.strftime(DATA_HORA),
                    texto=texto.strip(),
                )
                substituir("registos", novo)

    apagar("registos", item)

st.caption(
    "Os guias são orientações gerais e não substituem acompanhamento "
    "veterinário. Não carregues dados pessoais ou backups no repositório público."
)
