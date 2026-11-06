import csv
import hashlib
import json
import os
import re
import shutil
import tempfile
import traceback
import uuid
import tkinter as tk

from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox, filedialog


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
FICHEIRO = PASTA / "dados_criacao_elite.json"
BACKUP = PASTA / "dados_criacao_elite.json.bak"

PADRAO = "Pintassilgo parva"
TODAS = "Todas as espécies"
GERAL = "Geral — todas as espécies"

DATA = "%d/%m/%Y"
DATA_HORA = "%d/%m/%Y %H:%M"

SEXOS = ["Indeterminado", "Macho", "Fêmea"]
CATEGORIAS = [
    "Geral", "Alimentação", "Saúde", "Reprodução",
    "Muda", "Limpeza", "Plantel",
]

ESPECIES = {
    "Pintassilgo parva": "Carduelis carduelis parva",
    "Canário doméstico": "Serinus canaria domestica",
    "Lugre": "Spinus spinus",
    "Dom-fafe": "Pyrrhula pyrrhula",
    "Verdilhão": "Chloris chloris",
    "Rouxinol-do-Japão": "Leiothrix lutea",
    "Pintarroxo": "Linaria cannabina",
}


# ============================================================
# CONTEÚDOS GERAIS
# ============================================================

NOTA = """
COMO INTERPRETAR OS CONTEÚDOS

Estas orientações são uma síntese geral de maneio e não substituem
avaliação veterinária, uma formulação nutricional individual ou
consulta de literatura específica.

A ecologia alimentar descreve recursos utilizados na natureza.
Não constitui, por si só, uma receita completa para cativeiro.

Práticas de criação não equivalem automaticamente a necessidades
nutricionais demonstradas experimentalmente.

Não são apresentados como universais:
• dimensões mínimas de alojamento;
• intervalos de peso;
• percentagens de sementes, proteína ou gordura;
• limites de ferro;
• doses de suplementos;
• programas de horas de luz.

As referências mencionadas são pontos de consulta. Não se afirma
que os textos integrais tenham sido consultados ou que cada
recomendação tenha sido validada especificamente para cada espécie.

Não utilizar antibióticos, antiparasitários, vitaminas ou outros
produtos por rotina sem indicação fundamentada.
"""

BASE_CUIDADOS = """
ROTINA DIÁRIA

Observar cada ave antes de se aproximar:
• atividade, postura, equilíbrio e respiração;
• interação com as restantes aves;
• interesse e acesso ao alimento;
• acesso à água;
• aspeto das dejeções e limpeza da região cloacal.

Confirmar ingestão efetiva. Um comedouro com cascas pode parecer cheio.
Renovar a água, lavar recipientes e retirar resíduos deteriorados.

ALOJAMENTO

Priorizar comprimento útil de voo e trajetos desimpedidos.
Colocar poleiros e recipientes de modo a reduzir contaminação por fezes.
Disponibilizar sombra, ventilação e abrigo adequados ao clima.

Utilizar poleiros seguros e evitar superfícies abrasivas, fios soltos,
materiais tóxicos e elementos capazes de prender patas ou anilhas.

Distribuir recursos quando existe competição. O abrigo visual deve
permitir afastamento sem criar zonas onde uma ave fique encurralada.

Disponibilizar banho limpo sem obrigar a ave a utilizá-lo.
Evitar fumo, aerossóis e vapores de antiaderentes sobreaquecidos.

PLANTAS E RAMOS

Confirmar identificação e segurança da planta e da parte utilizada.
Usar materiais de origem conhecida. A lavagem não garante remoção
de todos os pesticidas. Retirar bolor e elementos perigosos.

VIGILÂNCIA E BIOSSEGURANÇA

Registar peso e condição corporal quando isso puder ser feito
com segurança e sem perturbação excessiva.
Comparar cada ave com o seu histórico individual.

Separar novas entradas em espaço independente, com utensílios próprios.
Definir quarentena e exames com um veterinário de aves.
Cuidar primeiro das aves saudáveis e depois das isoladas.
Limpar antes de desinfetar e respeitar as instruções do produto.

URGÊNCIA

Respiração de bico aberto em repouso, esforço respiratório, colapso,
hemorragia, incapacidade de pousar, ausência de ingestão ou esforço
persistente de postura justificam assistência veterinária rápida.
Não forçar água ou comida numa ave debilitada.

LEGALIDADE

Confirmar requisitos de origem, identificação, detenção, reprodução
e cedência aplicáveis à espécie e região.
Uma anilha não substitui toda a documentação.
Não capturar nem libertar aves selvagens.
"""

BASE_ALIMENTACAO = """
PLANEAMENTO ALIMENTAR

1. DEFINIR A BASE
Confirmar se o produto é completo ou complementar e se é adequado
ao grupo de aves e à fase de vida.
Uma mistura de sementes ou pasta não se torna completa apenas
por ser comercializada para aves.

2. AVALIAR O CONSUMO
Registar alimento oferecido e remanescente em condições comparáveis.
Cascas, derrame e seleção impedem que a diferença corresponda
exatamente à ingestão. Nos alimentos húmidos há também evaporação.

Observar quais os componentes escolhidos e quais ficam.
Uma mistura variada pode resultar numa dieta pouco variada
quando a ave seleciona apenas alguns ingredientes.

3. ALTERAÇÕES GRADUAIS
Apresentar o alimento novo juntamente com o conhecido.
Confirmar ingestão, atividade, dejeções e evolução da condição.
Não retirar abruptamente o alimento habitual para forçar conversão.

4. COMPLEMENTOS
Vegetais e frutos seguros devem ser lavados, apresentados em porções
adequadas e retirados antes de se deteriorarem.
Brócolos, cenoura e folhas comestíveis identificadas podem ser
complementos, não substitutos automáticos da base.

Alimentos aquosos podem aumentar a urina nas dejeções.
Isso não é necessariamente diarreia, mas alterações persistentes,
emagrecimento ou prostração precisam de avaliação.

5. SEMENTES E GERMINADOS
Rejeitar sementes com bolor, ranço, humidade ou infestação.
Respeitar conservação e validade.
Germinados não são indispensáveis e podem transportar microrganismos
mesmo sem alterações visíveis.

6. CÁLCIO, VITAMINAS E GRIT
Cálcio nutricional não é o mesmo que grit insolúvel.
Aves que descascam sementes não precisam automaticamente de grit.
Osso de choco disponível não garante ingestão adequada.

Avaliar cálcio, fósforo, vitamina D e restante dieta em conjunto.
Não sobrepor suplementos a alimentos completos sem verificar
a composição e a indicação.

7. HIGIENE DOS ALIMENTOS HÚMIDOS
Calor, humidade e composição alteram a velocidade de deterioração.
Não existe um tempo universal de permanência no comedouro.
Lavar recipientes em vez de adicionar alimento sobre resíduos.

8. EVITAR
Não oferecer abacate, chocolate, álcool ou cafeína.
Evitar alimentos muito salgados, bolorentos ou desconhecidos.
Não recolher plantas ou insetos em locais sujeitos a pesticidas.
"""

BASE_CICLO = """
GESTÃO DO CICLO ANUAL

MANUTENÇÃO
Manter alimentação estável, exercício e descanso.
Registar condição corporal, ingestão e comportamento.

PREPARAÇÃO
Avaliar maturidade, saúde, compatibilidade e recuperação dos adultos.
Preparar os alimentos necessários às crias antes das eclosões.
Não tentar compensar má condição com vitaminas ou estimulantes.

REPRODUÇÃO
Registar postura, eclosão, alimentação, crescimento, conflitos e perdas.
Reduzir perturbações sem deixar de acompanhar o bem-estar.
Não existe um número universal de posturas adequado a todas as aves.

CRIAS
A saída do ninho não significa independência alimentar.
Confirmar ingestão suficiente em cada jovem antes da separação.
Debicar alimento ou pedir comida não demonstra autonomia.

MUDA
A formação de penas exige nutrientes adequados, mas não existe uma
percentagem universal de proteína para todas estas espécies.
Não suplementar automaticamente uma dieta já completa.
Penas deformadas, prurido, falhas localizadas ou muda muito prolongada
justificam investigação.

REPOUSO
Permitir recuperação e evitar estímulos reprodutivos contínuos.
O calendário depende da latitude, hemisfério, clima, alojamento
e iluminação, incluindo luz doméstica noturna.
Evitar alterações bruscas e programas universais de horas de luz.
"""


# ============================================================
# PERFIS ESPECÍFICOS
# ============================================================

PERFIS = {
    "Pintassilgo parva": {
        "cuidados": """
PINTASSILGO PARVA — ALOJAMENTO E OBSERVAÇÃO

IDENTIDADE
O parva é uma subespécie de Carduelis carduelis.
Dados da espécie completa não devem ser apresentados automaticamente
como valores específicos do parva, sobretudo no peso.

ORGANIZAÇÃO
Disponibilizar voo e abrigo visual.
Manter trajetos que não obriguem a passar constantemente junto do ninho.
Distribuir comedouros quando existe competição.

Observar cada indivíduo durante a alimentação, sobretudo após
formação de pares, mudanças de instalação ou alterações da dieta.

A tolerância fora da reprodução não garante compatibilidade.
Vigiar perseguições e impedimento de acesso aos recursos.

ENRIQUECIMENTO
Plantas e inflorescências seguras podem proporcionar procura de alimento.
Não devem substituir o acesso fácil à dieta principal.

CONTROLO
Verificar patas, anilhas, capacidade de descasque e condição individual.
Não justificar medicação preventiva com uma presumida fragilidade
hepática universal da espécie.
""",
        "alimentacao": """
PINTASSILGO PARVA — DIETA E CRIAÇÃO

ECOLOGIA
Carduelis carduelis utiliza sobretudo pequenas sementes, incluindo
sementes de cardos e outras herbáceas.
Isso não demonstra que uma mistura doméstica seja completa.

BASE E SELEÇÃO
Avaliar finalidade e composição do alimento principal.
Alpista, níger e outras sementes têm perfis diferentes;
nenhuma é obrigatória isoladamente.

Níger, cânhamo e girassol são ingredientes energéticos.
A sua utilização depende da dieta total, atividade e condição.

Registar o que é selecionado primeiro e o que permanece.
Não repor continuamente apenas os componentes preferidos.
Distinguir cascas, desperdício e alimento ingerido.

Se existir alimento formulado, confirmar ingestão:
partículas partidas ou espalhadas não são prova suficiente.

CRIAS
Confirmar antecipadamente aceitação dos alimentos de apoio.
A percentagem de proteína de uma pasta não corresponde à da dieta total.

Crescimento insuficiente não deve ser atribuído apenas à proteína:
avaliar ingestão, saúde, competição, perturbação e ambiente.
Ovo, germinados e insetos não são obrigatórios para todos os casais.
""",
        "ciclo": """
PINTASSILGO PARVA — REGISTOS DO CASAL

Registar:
• formação do casal e perseguições;
• aceitação dos alimentos de apoio;
• postura, eclosão e saída do ninho;
• evolução de cada cria e diferenças entre irmãos;
• recuperação da fêmea e condição dos adultos.

Usar material de ninho sem fios perigosos.
Não retirar ovos ou crias por um calendário automático.
Confirmar autonomia alimentar antes da separação.
""",
        "fontes": """
REFERÊNCIAS E LIMITES

Pontos de consulta:
• Birds of the World — European Goldfinch.
• Avibase — taxonomia de Carduelis carduelis parva.
• MSD Veterinary Manual — Nutrition in Birds.

Não é apresentada uma fórmula quantitativa validada especificamente
para a subespécie parva.
""",
    },

    "Canário doméstico": {
        "cuidados": """
CANÁRIO DOMÉSTICO — ALOJAMENTO E CONDIÇÃO

ADAPTAÇÃO AO INDIVÍDUO
Raças e indivíduos diferentes podem necessitar de adaptações nos
poleiros e no acesso a comedouros e bebedouros.
Isso não elimina a necessidade de exercício.

Inspecionar patas, unhas, anilhas e região cloacal.
Plumagem abundante não justifica assumir que toda a sujidade
é apenas um problema de higiene.

COMPATIBILIDADE
Machos podem tornar-se territoriais.
Vigiar perseguições, lesões e acesso aos recursos.
O canto do macho não demonstra que a fêmea esteja preparada
ou que os dois sejam compatíveis.

ACOMPANHAMENTO
Registar condição, capacidade de voo, seleção alimentar,
frequência de posturas e duração da muda.
Temperatura e banho devem considerar indivíduo, aclimatação e instalação.
""",
        "alimentacao": """
CANÁRIO DOMÉSTICO — BASE, PASTAS E POSTURA

Uma dieta exclusivamente de sementes pode ser desequilibrada,
nomeadamente em cálcio e determinadas vitaminas.

Alimentos formulados adequados são uma opção quando a conversão
é gradual e a ingestão está confirmada.
A percentagem de alpista, isoladamente, não demonstra adequação.

PASTAS E PREPARAÇÕES
Registar marca, finalidade e modo de utilização.
Confirmar se são completas ou complementares.

A água altera a concentração por unidade de peso:
não comparar diretamente alimentos húmidos e secos sem considerar isso.

Ovo completamente cozinhado pode integrar uma preparação,
mas não constitui sozinho uma fórmula equilibrada.
Manter higiene rigorosa nas preparações húmidas.

SUPLEMENTOS
Produtos com finalidades comerciais diferentes podem repetir
as mesmas vitaminas e minerais.
Não os combinar sem avaliar a ingestão total.

POSTURA E CRIAS
Avaliar cálcio, fósforo, vitamina D e energia no conjunto.
Problemas de postura exigem avaliação, não doses por tentativa.
Confirmar a alimentação das crias e a autonomia de cada jovem.
""",
        "ciclo": """
CANÁRIO DOMÉSTICO — LUZ E RECUPERAÇÃO

Contabilizar iluminação natural, artificial e luz doméstica noturna.
Um temporizador não controla toda a luz que chega à ave.

Evitar mudanças bruscas e estimulação reprodutiva contínua.
Registar recuperação entre posturas e sobreposição entre muda e criação.

Postura persistente, desgaste ou dificuldades repetidas justificam
revisão de maneio e avaliação veterinária.

Não extrapolar programas de pigmentação de canários de fator vermelho
para outras espécies.
""",
        "fontes": """
REFERÊNCIAS E LIMITES

Pontos de consulta:
• Harper, E. J. (2000), Nutrition and energetics of the canary.
• Royal Veterinary College — Canary Care.
• The Unusual Pet Vets — Canary Care.
• MSD Veterinary Manual — Nutrition in Birds.

Fontes diferentes podem propor planos distintos.
Não combinar percentagens de planos diferentes como se constituíssem
uma fórmula validada.
""",
    },

    "Lugre": {
        "cuidados": """
LUGRE — ESPAÇO, RECURSOS E OBSERVAÇÃO

Este perfil refere-se a Spinus spinus.
Não copiar automaticamente recomendações de Spinus pinus
ou Spinus cucullatus.

Disponibilizar estruturas seguras em diferentes posições,
sem ocupar todo o percurso de voo.

Observar os indivíduos menos dominantes em momentos diferentes.
Uma observação breve pode não revelar exclusão persistente.

Após mudanças, confirmar que cada ave localizou água e alimento.
Não assumir que seguirá imediatamente os restantes indivíduos.

Redução de ingestão em aves pequenas merece atenção rápida.
Não atribuir um consumo fixo apenas com base no tamanho.
""",
        "alimentacao": """
LUGRE — CONSUMO E APRESENTAÇÃO

ECOLOGIA
Utiliza sobretudo sementes, incluindo coníferas, amieiro, bétula
e herbáceas, com consumo de invertebrados na época reprodutiva.

APLICAÇÃO
Uma designação comercial como “mistura para lugres” não demonstra
equilíbrio nutricional.
Confirmar dimensão dos ingredientes, descasque e ingestão.

Sementes de árvores podem servir de enriquecimento, sem serem
ingredientes obrigatórios. Confirmar identificação e origem.

Preferência por níger não demonstra necessidade de oferta ilimitada.
O consumo natural de insetos não estabelece uma dose obrigatória
de alimento vivo em cativeiro.

MUDANÇAS
Um alimento conhecido pode ser menos utilizado quando muda de recipiente.
Alterar um elemento de cada vez facilita identificar dificuldades.

Não reduzir drasticamente a oferta para controlar peso
nem considerar germinados indispensáveis.
""",
        "ciclo": """
LUGRE — ACOMPANHAMENTO INDIVIDUAL

Registar o ciclo observado nas próprias aves.
Relacionar condição e comportamento com muda, formação de pares,
mudanças ambientais e acesso ao alimento.

Não interpretar emagrecimento como consequência normal da muda
sem avaliar ingestão e saúde.

Confirmar autonomia alimentar de cada jovem,
não apenas do conjunto da ninhada.
""",
        "fontes": """
REFERÊNCIAS E LIMITES

Pontos de consulta:
• BirdLife International — Eurasian Siskin, Spinus spinus.
• Literatura de comportamento alimentar de Spinus spinus.
• MSD Veterinary Manual — Nutrition in Birds.

Fontes ecológicas e comportamentais não estabelecem, por si só,
uma fórmula completa para reprodução em cativeiro.
""",
    },

    "Dom-fafe": {
        "cuidados": """
DOM-FAFE — TRANQUILIDADE COM VIGILÂNCIA

Disponibilizar espaço de voo, rotina previsível e abrigo visual.
Evitar capturas desnecessárias.

O abrigo não deve impedir observação da condição da ave.
Imobilidade não demonstra automaticamente tranquilidade:
observar atenção, postura, ingestão e respiração.

Em períodos quentes, verificar sombra ao longo do dia,
ventilação e água. A posição do sol altera as zonas protegidas.

Confirmar compatibilidade continuadamente.
A aparência calma não exclui intimidação ou acesso desigual.

Não existe fundamento apresentado aqui para afirmar que todos
os dom-fafes necessitam de medicação hepática preventiva
ou restrição generalizada de cálcio.
""",
        "alimentacao": """
DOM-FAFE — SEMENTES, GOMOS E FRUTOS

A espécie utiliza sementes, gomos e outros recursos vegetais,
com variação sazonal.
Isso não obriga a fornecer permanentemente todos esses recursos.

BASE
Avaliar o conjunto da dieta e a ingestão efetiva.
Quando não existe formulação demonstravelmente adequada,
procurar apoio especializado.

GOMOS E REBENTOS
Podem servir de enriquecimento quando seguros.
A segurança não se deduz apenas de a planta ser uma árvore de fruto.
Confirmar espécie vegetal, parte utilizada e origem.

FRUTOS E SEMENTES ENERGÉTICAS
Fruta não é uma base completa.
Cânhamo ou girassol não são, isoladamente, prova de toxicidade.

Perante seleção dos alimentos mais energéticos,
avaliar dieta e condição antes de restringir ingredientes.

Não usar preferências como prova de necessidade nutricional,
nem recusa de alimento como diagnóstico.
""",
        "ciclo": """
DOM-FAFE — NINHADAS E RECUPERAÇÃO

Registar regularidade da alimentação das crias,
diferenças entre irmãos e perdas repetidas.

Quando um casal falha, rever saúde, compatibilidade,
ambiente, ingestão e qualidade dos alimentos.
Não atribuir automaticamente a causa a uma carência
ou a uma determinada semente.

Avaliar recuperação dos adultos antes de nova reprodução.
Aceitar o ninho não demonstra, por si só, condição adequada.
""",
        "fontes": """
REFERÊNCIAS E LIMITES

Referência geral:
• MSD Veterinary Manual — Nutrition in Birds.

Não foi incorporado um protocolo quantitativo específico verificado.
Não se atribuem recomendações a “Todos los Camachuelos”
sem confirmar edição, conteúdo e páginas relevantes.
""",
    },

    "Verdilhão": {
        "cuidados": """
VERDILHÃO — COMPETIÇÃO E BIOSSEGURANÇA

Disponibilizar voo e recursos distribuídos.
Vigiar conflitos, especialmente na reprodução.

Evitar acesso de aves selvagens à água e alimento.
Limpar utensílios e, quando indicado, desinfetá-los
antes de os utilizar noutra instalação.

Verdilhões podem ser afetados por tricomonose,
que pode atingir o trato digestivo superior.
Não é simplesmente uma doença respiratória.

Dificuldade de deglutição, regurgitação, saliva anormal,
emagrecimento ou alimento deixado cair exigem avaliação.

Separar aves com sinais e procurar assistência.
Não manipular placas na boca nem administrar
antiprotozoários preventivamente por calendário.
""",
        "alimentacao": """
VERDILHÃO — ENERGIA, EXERCÍCIO E INGESTÃO

O bico robusto permite utilizar certas sementes,
mas não demonstra que girassol ou cânhamo devam dominar a dieta.

Relacionar consumo com atividade e capacidade de voo.
Uma ave sedentária pode selecionar uma dieta muito energética
mesmo quando existem outros componentes na mistura.

Girassol descascado continua a ser energético.
Alpista e vegetais não corrigem automaticamente
todas as limitações de uma dieta de sementes.

Não resolver excesso de condição reduzindo indiscriminadamente
a quantidade: isso pode limitar nutrientes importantes.

Dificuldade em descascar, engolir ou reter alimento
não deve ser tratada apenas mudando de sementes.

Preparar a alimentação das crias e confirmar aceitação,
sem impor aumentos universais de proteína ou energia.
""",
        "ciclo": """
VERDILHÃO — HISTÓRICO DO CASAL

Rever doença recente, tratamentos e recuperação antes da reprodução.
Acompanhar territorialidade e acesso da fêmea aos recursos.

Registar postura, eclosão, crescimento e perdas.
Não estabelecer diagnósticos apenas por semelhança
com episódios de outras ninhadas.

Após a criação, manter exercício e acompanhar condição e muda.
""",
        "fontes": """
REFERÊNCIAS E LIMITES

Pontos de consulta:
• MSD Veterinary Manual — Nutrition in Birds.
• Literatura veterinária sobre tricomonose aviária.

Não é apresentada uma fórmula nutricional específica validada,
nem um protocolo de diagnóstico ou tratamento.
""",
    },

    "Rouxinol-do-Japão": {
        "cuidados": """
ROUXINOL-DO-JAPÃO — AVIÁRIO E RECURSOS

Leiothrix lutea não deve receber o plano de um fringilídeo granívoro.

Disponibilizar voo e abrigo visual.
Distribuir os recursos para que um indivíduo não controle
todos os pontos de alimentação.

Em aviários mistos, observar diferentes fases do ano.
Convivência pacífica no repouso não garante segurança na reprodução.

Verificar resíduos de frutos e invertebrados, que podem atrair pragas.
Abrigo, clima, aclimatação e segurança determinam
a adequação de instalações interiores ou exteriores.

Confirmar as regras legais aplicáveis à espécie na região
antes de adquirir, reproduzir, transportar ou ceder.
""",
        "alimentacao": """
ROUXINOL-DO-JAPÃO — DIETA INSETÍVORA/FRUGÍVORA

BASE
Escolher alimento completo adequado e avaliar a sua indicação.
Uma pasta rotulada “insetívora” pode ser apenas complementar.

Registar separadamente formulado, frutos e invertebrados.
Variedade oferecida não demonstra equilíbrio se a ave
seleciona quase exclusivamente os componentes preferidos.

INVERTEBRADOS
Utilizar origem controlada e conservação adequada.
Tenébrios não constituem alimento completo.
Espécie, tamanho, alimentação prévia e preparação alteram
o valor nutricional dos insetos.

Alimentação prévia dos insetos e suplementação, quando indicadas,
devem integrar um plano, não uma combinação arbitrária de produtos.
Evitar insetos selvagens de segurança desconhecida.

FRUTOS
Maçã sem sementes, pera e frutos adequados podem complementar.
Fruta isolada não cobre todas as necessidades.
Lavar recipientes e retirar resíduos antes de deterioração.

FERRO
Não se estabelece aqui um limite específico validado
de ferro para Leiothrix lutea.
Não aplicar automaticamente números definidos para outras aves.

CRIAS
Assegurar fornecimento regular e conservação dos alimentos.
Não aumentar insetos de forma drástica e não monitorizada.
Observar o que os pais oferecem e a evolução dos jovens.
""",
        "ciclo": """
ROUXINOL-DO-JAPÃO — PLANEAMENTO DA CRIAÇÃO

Confirmar compatibilidade e possibilidade de separação em conflito.
Preparar alimentos e alternativas apropriadas antes das eclosões.

Acompanhar alimentação com a menor perturbação possível.
Na saída do ninho, vigiar ingestão e interações com outras aves.

Após a criação, permitir recuperação e acompanhar a muda,
sem estimulação reprodutiva contínua.
""",
        "fontes": """
REFERÊNCIAS E LIMITES

Referência geral:
• MSD Veterinary Manual — Nutrition in Birds.

Não foi incorporado um manual zoológico específico integralmente
verificado para Leiothrix lutea.
Dados de outras aves de bico mole não estabelecem automaticamente
limites nutricionais para esta espécie.
""",
    },

    "Pintarroxo": {
        "cuidados": """
PINTARROXO — ESTABILIDADE E COMPATIBILIDADE

Disponibilizar voo, abrigo visual e rotina previsível.
Evitar deslocar frequentemente poleiros e recipientes.

Após mudanças, confirmar localização dos recursos e ingestão.
Na reprodução, vigiar conflitos e perturbações junto do ninho.

Não concluir que a espécie é adequada à criação em colónia
com base no comportamento de um único casal.

Confirmar condição individual.
Não copiar automaticamente protocolos de pintassilgos.
""",
        "alimentacao": """
PINTARROXO — DA ECOLOGIA À DIETA

Utiliza principalmente sementes de herbáceas.
Isso não valida automaticamente uma mistura comercial
destinada a outra espécie.

Avaliar base, seleção de ingredientes e capacidade de utilização.
Nenhuma semente é considerada obrigatória neste guia.

Plantas com sementes podem enriquecer a procura,
desde que identificadas e sem contaminantes.

Evitar mudar simultaneamente mistura, pasta e suplementos,
pois isso dificulta identificar causas de problemas.

Se as dejeções mudarem após vegetais, avaliar também
atividade, ingestão e condição.
Não presumir doença nem considerar toda a alteração inofensiva.

Preparar os alimentos de crescimento antecipadamente.
Avaliar cálcio, fósforo e vitamina D no conjunto da dieta,
sem suplementar por tentativa.
""",
        "ciclo": """
PINTARROXO — JOVENS E MUDA

Registar alimentação e desenvolvimento de cada cria.
Confirmar ingestão suficiente antes de separar dos pais.

Acompanhar plumagem e condição ao longo da muda.
Intensidade de coloração não demonstra isoladamente
qualidade da dieta ou estado de saúde.

Não aplicar programas de pigmentação de canários por analogia.
""",
        "fontes": """
REFERÊNCIAS E LIMITES

Referência geral:
• MSD Veterinary Manual — Nutrition in Birds.

As notas específicas são síntese geral de ecologia e maneio.
São necessárias fontes adicionais específicas antes de apresentar
uma receita quantitativa para Linaria cannabina.
""",
    },
}


# ============================================================
# APOIO E PERSISTÊNCIA
# ============================================================

def uid():
    return uuid.uuid4().hex


def normal(valor):
    return str(valor).strip().casefold()


def chave_natural(valor):
    return tuple(
        (1, int(p)) if p.isdigit() else (0, p.casefold())
        for p in re.split(r"(\d+)", str(valor))
    )


def validar_data(valor, com_hora=False):
    data = datetime.strptime(str(valor).strip(), DATA_HORA if com_hora else DATA)
    if data.year < 1900:
        raise ValueError("Ano anterior a 1900.")
    return data


def interpretar_data(valor):
    for hora in (True, False):
        try:
            return validar_data(valor, hora)
        except (ValueError, TypeError):
            pass
    return datetime.min


def validar_ano(valor):
    return (
        bool(re.fullmatch(r"\d{4}", valor))
        and 1900 <= int(valor) <= datetime.now().year
    )


def assinatura_ficheiro():
    if not FICHEIRO.exists():
        return None
    return hashlib.sha256(FICHEIRO.read_bytes()).hexdigest()


def carregar():
    if FICHEIRO.exists():
        with FICHEIRO.open("r", encoding="utf-8") as f:
            dados = json.load(f)
    else:
        dados = {}

    if isinstance(dados, list):
        dados = {"registos": dados}
    if not isinstance(dados, dict):
        raise ValueError("A estrutura principal do JSON não é válida.")

    especies = dados.setdefault("especies", dict(ESPECIES))
    if not isinstance(especies, dict):
        raise ValueError("A lista de espécies não é válida.")

    for nome, cientifico in ESPECIES.items():
        especies.setdefault(nome, cientifico)

    if any(
        not isinstance(n, str) or not n.strip() or not isinstance(c, str)
        for n, c in especies.items()
    ):
        raise ValueError("Existe uma espécie inválida.")

    campos = {
        "registos": ["data", "categoria", "texto"],
        "plantel": ["anilha", "sexo", "ano", "casal"],
        "crias": [
            "anilha", "nascimento", "sexo", "casal", "ninhada",
            "observacoes", "pai_id", "pai_anilha", "mae_id",
            "mae_anilha", "plantel_id",
        ],
    }
    ids = set()

    for grupo, nomes in campos.items():
        lista = dados.setdefault(grupo, [])
        if not isinstance(lista, list):
            raise ValueError(f"O grupo '{grupo}' não é uma lista.")

        for item in lista:
            if not isinstance(item, dict):
                raise ValueError(f"Registo inválido em '{grupo}'.")

            item["id"] = str(item.get("id") or uid())
            if item["id"] in ids:
                raise ValueError("Existem identificadores repetidos.")
            ids.add(item["id"])

            for campo in nomes:
                valor = item.get(campo)
                item[campo] = "" if valor is None else str(valor)

            item["especie"] = str(item.get("especie") or PADRAO)
            if item["especie"] == GERAL:
                if grupo != "registos":
                    raise ValueError("Uma ave não pode ter espécie geral.")
            else:
                especies.setdefault(item["especie"], "")

            if grupo == "registos":
                item["categoria"] = item["categoria"] or "Geral"
            else:
                item["sexo"] = item["sexo"] or "Indeterminado"

    return dados


def gravar(dados, assinatura_esperada):
    temporario = None
    bloqueio = PASTA / "dados_criacao_elite.lock"
    descritor = None

    try:
        try:
            descritor = os.open(
                str(bloqueio), os.O_CREAT | os.O_EXCL | os.O_WRONLY
            )
        except FileExistsError:
            raise RuntimeError(
                "Existe outra gravação em curso ou um bloqueio pendente.\n"
                "Feche outras instâncias e tente novamente.\n"
                "Se o problema persistir após encerrar todas as instâncias,\n"
                "verifique o ficheiro dados_criacao_elite.lock."
            )

        if assinatura_ficheiro() != assinatura_esperada:
            raise RuntimeError(
                "O ficheiro de dados foi alterado fora desta janela.\n"
                "A gravação foi cancelada para não sobrescrever alterações.\n"
                "Reabra a aplicação para carregar a versão atual."
            )

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=PASTA,
            prefix="aves_", suffix=".tmp", delete=False,
        ) as f:
            temporario = Path(f.name)
            json.dump(dados, f, ensure_ascii=False, indent=4)
            f.flush()
            os.fsync(f.fileno())

        nova_assinatura = hashlib.sha256(temporario.read_bytes()).hexdigest()

        if FICHEIRO.exists():
            pasta_backup = PASTA / "backups_aves"
            pasta_backup.mkdir(exist_ok=True)
            nome = datetime.now().strftime("dados_%Y%m%d_%H%M%S_%f.json")
            shutil.copy2(FICHEIRO, pasta_backup / nome)
            shutil.copy2(FICHEIRO, BACKUP)

        os.replace(temporario, FICHEIRO)
        return nova_assinatura

    finally:
        if temporario and temporario.exists():
            temporario.unlink()
        if descritor is not None:
            os.close(descritor)
            try:
                bloqueio.unlink()
            except FileNotFoundError:
                pass


# ============================================================
# APLICAÇÃO
# ============================================================

class Aplicacao:
    def __init__(self, root, dados, assinatura):
        self.root = root
        self.dados = dados
        self.assinatura = assinatura

        self.edicao_diario = None
        self.edicao_cria = None
        self.ids_casal = {"Macho": None, "Fêmea": None}
        self.filiacao = None
        self.tabelas = {}
        self.ordens = {}
        self.combos_especies = []
        self.mapa_filtros = {}
        self.modo_alimentacao = "Alimentação"
        self.bases = {}

        root.title("Aves Elite Manager")
        root.geometry("1280x880")
        root.minsize(1080, 760)
        root.protocol("WM_DELETE_WINDOW", self.fechar)

        estilo = ttk.Style(root)
        estilo.configure(".", font=("Segoe UI", 10))
        estilo.configure("Treeview", rowheight=27)

        topo = self.linha(root)
        ttk.Label(topo, text="Consultar espécie:").pack(side="left")
        self.especie_global = tk.StringVar(value=TODAS)
        self.combo_global = ttk.Combobox(
            topo, textvariable=self.especie_global,
            state="readonly", width=28,
        )
        self.combo_global.pack(side="left", padx=6)
        self.combo_global.bind("<<ComboboxSelected>>", self.mudar_especie)
        self.botao(topo, "Adicionar espécie", self.adicionar_especie)
        ttk.Label(
            topo, text="O filtro não modifica os registos guardados."
        ).pack(side="right", padx=8)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        self.abas = {}

        for nome in (
            "Guia de Cuidados", "Alimentação",
            "Diário de Manejo", "Plantel", "Crias",
        ):
            frame = ttk.Frame(self.notebook, padding=8)
            self.notebook.add(frame, text=nome)
            self.abas[nome] = frame

        self.texto_guia = self.caixa_leitura(self.abas["Guia de Cuidados"])
        barra = self.linha(self.abas["Alimentação"])
        for modo in ("Alimentação", "Ciclo Anual", "Fontes e limites"):
            self.botao(barra, modo, lambda m=modo: self.alterar_modo(m))
        self.texto_alimentacao = self.caixa_leitura(self.abas["Alimentação"])

        self.construir_diario()
        self.construir_plantel()
        self.construir_crias()

        self.estado = tk.StringVar()
        ttk.Label(
            root, textvariable=self.estado, wraplength=1240
        ).pack(fill="x", padx=12, pady=8)

        self.atualizar()
        self.marcar_base("diario")
        self.marcar_base("plantel")
        self.marcar_base("crias")

    # --------------------------------------------------------
    # INTERFACE E FORMULÁRIOS
    # --------------------------------------------------------

    def linha(self, pai):
        frame = ttk.Frame(pai, padding=(5, 3))
        frame.pack(fill="x", pady=2)
        return frame

    def botao(self, pai, texto, comando, lado="left"):
        ttk.Button(pai, text=texto, command=comando).pack(
            side=lado, padx=3
        )

    def campo(self, pai, titulo, variavel, largura=20):
        ttk.Label(pai, text=titulo).pack(side="left", padx=(5, 2))
        entrada = ttk.Entry(pai, textvariable=variavel, width=largura)
        entrada.pack(side="left", padx=3)
        return entrada

    def combo_especie(self, pai, variavel, geral=False):
        combo = ttk.Combobox(
            pai, textvariable=variavel, state="readonly", width=25
        )
        combo.pack(side="left", padx=5)
        self.combos_especies.append((combo, geral))
        return combo

    def caixa_leitura(self, pai):
        frame = ttk.Frame(pai)
        frame.pack(fill="both", expand=True)
        texto = tk.Text(
            frame, wrap="word", font=("Segoe UI", 12),
            padx=18, pady=12,
        )
        scroll = ttk.Scrollbar(frame, command=texto.yview)
        texto.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        texto.pack(fill="both", expand=True)
        return texto

    def escrever(self, caixa, texto):
        caixa.configure(state="normal")
        caixa.delete("1.0", "end")
        caixa.insert("1.0", texto.strip())
        caixa.configure(state="disabled")

    def aviso(self, texto):
        messagebox.showwarning("Atenção", texto, parent=self.root)

    def confirmar(self, texto):
        return messagebox.askyesno("Confirmar", texto, parent=self.root)

    def nomes_especies(self):
        return sorted(self.dados["especies"], key=chave_natural)

    def especie_inicial(self):
        atual = self.especie_global.get()
        return atual if atual in self.dados["especies"] else PADRAO

    def visivel(self, item):
        return (
            self.especie_global.get() == TODAS
            or item["especie"] == self.especie_global.get()
        )

    def estado_formulario(self, nome):
        if nome == "diario":
            return (
                self.edicao_diario, self.d_especie.get(),
                self.d_categoria.get(), self.d_data.get(),
                self.d_texto.get("1.0", "end-1c"),
            )
        if nome == "plantel":
            return (
                self.p_especie.get(), self.p_casal.get(),
                tuple(self.ids_casal.items()),
                tuple(
                    self.p_campos[s][c].get()
                    for s in ("Macho", "Fêmea")
                    for c in ("anilha", "ano")
                ),
            )
        return (
            self.edicao_cria, self.c_especie.get(),
            tuple((k, v.get()) for k, v in self.c_vars.items()),
            self.c_obs.get("1.0", "end-1c"),
            tuple(sorted((self.filiacao or {}).items())),
        )

    def marcar_base(self, nome):
        self.bases[nome] = self.estado_formulario(nome)

    def alterado(self, nome):
        return (
            nome in self.bases
            and self.estado_formulario(nome) != self.bases[nome]
        )

    def autorizar_descarte(self, *nomes):
        alterados = [n for n in nomes if self.alterado(n)]
        return not alterados or self.confirmar(
            "Existem alterações não guardadas nos formulários.\n"
            "Continuar e descartá-las?"
        )

    def fechar(self):
        if self.autorizar_descarte("diario", "plantel", "crias"):
            self.root.destroy()

    def guardar(self, **alteracoes):
        novos = dict(self.dados)
        novos.update(alteracoes)
        novos["versao"] = 7
        try:
            assinatura = gravar(novos, self.assinatura)
        except Exception as erro:
            messagebox.showerror(
                "Erro ao guardar",
                f"A alteração não foi aplicada:\n\n{erro}",
                parent=self.root,
            )
            return False
        self.dados = novos
        self.assinatura = assinatura
        self.atualizar()
        return True

    # --------------------------------------------------------
    # TABELAS E CSV
    # --------------------------------------------------------

    def criar_tabela(self, pai, nome, colunas, ordem):
        frame = ttk.Frame(pai)
        frame.pack(fill="both", expand=True, pady=4)
        tree = ttk.Treeview(
            frame, columns=[c[0] for c in colunas],
            show="headings", selectmode="extended",
        )
        for campo, titulo, largura in colunas:
            tree.column(campo, width=largura, minwidth=75)
            tree.heading(
                campo, text=titulo,
                command=lambda c=campo: self.ordenar(nome, c),
            )
        vertical = ttk.Scrollbar(frame, command=tree.yview)
        horizontal = ttk.Scrollbar(
            frame, orient="horizontal", command=tree.xview
        )
        tree.configure(
            yscrollcommand=vertical.set, xscrollcommand=horizontal.set
        )
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.tabelas[nome] = (tree, colunas)
        self.ordens[nome] = ordem
        return tree

    def ordenar(self, nome, campo):
        anterior, inversa = self.ordens[nome]
        self.ordens[nome] = (
            campo, not inversa if anterior == campo else False
        )
        self.atualizar()

    def ordenar_itens(self, nome, itens):
        campo, inversa = self.ordens[nome]
        def chave(item):
            valor = item.get(campo, "")
            if campo in ("data", "nascimento"):
                return interpretar_data(valor)
            return chave_natural(valor)
        return sorted(itens, key=chave, reverse=inversa)

    def preencher(self, nome, itens):
        tree, colunas = self.tabelas[nome]
        selecionados = set(tree.selection())
        filhos = tree.get_children()
        if filhos:
            tree.delete(*filhos)
        for item in self.ordenar_itens(nome, itens):
            tree.insert(
                "", "end", iid=item["id"],
                values=[
                    str(item.get(c, "")).replace("\n", " ")
                    for c, _, _ in colunas
                ],
            )
        for identificador in selecionados:
            if tree.exists(identificador):
                tree.selection_add(identificador)
        campo_ordenado, inversa = self.ordens[nome]
        for campo, titulo, _ in colunas:
            seta = (" ▼" if inversa else " ▲") if campo == campo_ordenado else ""
            tree.heading(campo, text=titulo + seta)

    def selecionado(self, nome, grupo, evento=None):
        tree = self.tabelas[nome][0]
        if evento is not None:
            if tree.identify_region(evento.x, evento.y) not in ("cell", "tree"):
                return None
            identificador = tree.identify_row(evento.y)
        else:
            selecao = tree.selection()
            if len(selecao) > 1:
                self.aviso("Selecione apenas um registo para esta operação.")
                return None
            identificador = selecao[0] if selecao else None
        return next(
            (i for i in self.dados[grupo] if i["id"] == identificador), None
        )

    def exportar(self, nome, itens):
        caminho = filedialog.asksaveasfilename(
            parent=self.root, title="Exportar dados filtrados",
            defaultextension=".csv", filetypes=[("CSV", "*.csv")],
        )
        if not caminho:
            return
        colunas = self.tabelas[nome][1]
        def celula(valor):
            texto = str(valor)
            return "'" + texto if texto.lstrip().startswith(
                ("=", "+", "-", "@")
            ) else texto
        try:
            with open(caminho, "w", encoding="utf-8-sig", newline="") as f:
                escritor = csv.writer(f, delimiter=";")
                escritor.writerow([t for _, t, _ in colunas])
                for item in self.ordenar_itens(nome, itens):
                    escritor.writerow([
                        celula(item.get(c, "")) for c, _, _ in colunas
                    ])
        except OSError as erro:
            self.aviso(str(erro))
            return
        messagebox.showinfo("Exportação", "CSV exportado.", parent=self.root)

    # --------------------------------------------------------
    # ESPÉCIES E TEXTOS
    # --------------------------------------------------------

    def adicionar_especie(self):
        janela = tk.Toplevel(self.root)
        janela.title("Adicionar espécie")
        janela.transient(self.root)
        corpo = ttk.Frame(janela, padding=15)
        corpo.pack()
        nome = tk.StringVar()
        cientifico = tk.StringVar()
        self.campo(self.linha(corpo), "Nome comum:", nome, 32)
        self.campo(self.linha(corpo), "Nome científico:", cientifico, 32)

        def adicionar():
            valor = nome.get().strip()
            existentes = {
                normal(n) for n in self.nomes_especies() + [TODAS, GERAL]
            }
            if not valor or normal(valor) in existentes:
                self.aviso("Indique um nome novo e válido.")
                return
            especies = dict(self.dados["especies"])
            especies[valor] = cientifico.get().strip()
            if self.guardar(especies=especies):
                janela.destroy()

        self.botao(self.linha(corpo), "Adicionar", adicionar)
        janela.grab_set()

    def mudar_especie(self, evento=None):
        # Não altera formulários em edição ou com dados pendentes.
        if not self.edicao_diario and not self.alterado("diario"):
            self.d_especie.set(self.especie_inicial())
            self.marcar_base("diario")
        if not any(self.ids_casal.values()) and not self.alterado("plantel"):
            self.p_especie.set(self.especie_inicial())
            self.marcar_base("plantel")
        if not self.edicao_cria and not self.alterado("crias"):
            self.c_especie.set(self.especie_inicial())
            self.c_vars["casal"].set("")
            self.filiacao = None
            self.mostrar_filiacao()
            self.marcar_base("crias")
        self.atualizar()

    def alterar_modo(self, modo):
        self.modo_alimentacao = modo
        self.atualizar_textos()

    def atualizar_textos(self):
        especie = self.especie_global.get()
        bases = {
            "Alimentação": BASE_ALIMENTACAO,
            "Ciclo Anual": BASE_CICLO,
            "Fontes e limites": NOTA,
        }
        if especie == TODAS:
            self.escrever(
                self.texto_guia, "CUIDADOS GERAIS\n" + BASE_CUIDADOS + NOTA
            )
            self.escrever(
                self.texto_alimentacao,
                "Selecione uma espécie no topo para consultar o perfil.\n\n"
                + bases[self.modo_alimentacao],
            )
            return
        perfil = PERFIS.get(especie, {
            "cuidados": "Ainda não existe um perfil específico.\n",
            "alimentacao": "Confirmar a dieta com um especialista.\n",
            "ciclo": "Ainda não existe um ciclo específico.\n",
            "fontes": "Não foram adicionadas referências específicas.\n",
        })
        titulo = (
            f"{especie}\n"
            f"{self.dados['especies'].get(especie, '')}\n\n"
        )
        self.escrever(
            self.texto_guia, titulo + perfil["cuidados"] + BASE_CUIDADOS
        )
        campo = {
            "Alimentação": "alimentacao",
            "Ciclo Anual": "ciclo",
            "Fontes e limites": "fontes",
        }[self.modo_alimentacao]
        self.escrever(
            self.texto_alimentacao,
            titulo + perfil[campo] + bases[self.modo_alimentacao],
        )

    # --------------------------------------------------------
    # DIÁRIO
    # --------------------------------------------------------

    def construir_diario(self):
        pai = self.abas["Diário de Manejo"]
        linha = self.linha(pai)
        self.d_especie = tk.StringVar(value=PADRAO)
        self.combo_especie(linha, self.d_especie, True)
        self.d_categoria = tk.StringVar(value="Geral")
        ttk.Combobox(
            linha, textvariable=self.d_categoria, values=CATEGORIAS,
            state="readonly", width=15,
        ).pack(side="left", padx=4)
        self.d_data = tk.StringVar(value=datetime.now().strftime(DATA_HORA))
        self.campo(linha, "Data:", self.d_data, 18)
        self.botao(
            linha, "Hoje",
            lambda: self.d_data.set(datetime.now().strftime(DATA_HORA)),
        )
        ttk.Label(linha, text="DD/MM/AAAA HH:MM").pack(side="left", padx=4)

        self.d_texto = tk.Text(
            pai, height=4, wrap="word", font=("Segoe UI", 11)
        )
        self.d_texto.pack(fill="x", pady=5)
        self.d_texto.bind("<Control-Return>", self.atalho_diario)

        linha = self.linha(pai)
        self.d_botao = ttk.Button(
            linha, text="Registar", command=self.guardar_diario
        )
        self.d_botao.pack(side="left")
        self.botao(linha, "Cancelar / Limpar", self.limpar_diario)
        self.botao(linha, "Editar", self.editar_diario)
        self.botao(linha, "Apagar", self.apagar_diario)
        self.botao(
            linha, "Exportar CSV",
            lambda: self.exportar("diario", self.filtrar_diario()), "right",
        )
        linha = self.linha(pai)
        self.d_pesquisa = tk.StringVar()
        self.campo(linha, "Pesquisar:", self.d_pesquisa, 40)
        self.d_filtro = tk.StringVar(value="Todas")
        combo = ttk.Combobox(
            linha, textvariable=self.d_filtro,
            values=["Todas"] + CATEGORIAS, state="readonly", width=18,
        )
        combo.pack(side="left", padx=4)
        combo.bind("<<ComboboxSelected>>", lambda e: self.atualizar())
        tree = self.criar_tabela(
            pai, "diario", [
                ("data", "Data", 150), ("especie", "Espécie", 180),
                ("categoria", "Categoria", 130), ("texto", "Registo", 650),
            ], ("data", True),
        )
        tree.bind("<Double-1>", self.editar_diario)
        self.d_pesquisa.trace_add("write", lambda *a: self.atualizar())

    def atalho_diario(self, evento):
        self.guardar_diario()
        return "break"

    def filtrar_diario(self):
        termo = normal(self.d_pesquisa.get())
        return [
            r for r in self.dados["registos"]
            if (self.visivel(r) or r["especie"] == GERAL)
            and (self.d_filtro.get() == "Todas"
                 or r["categoria"] == self.d_filtro.get())
            and termo in normal(" ".join(
                r[c] for c in ("data", "especie", "categoria", "texto")
            ))
        ]

    def guardar_diario(self):
        texto = self.d_texto.get("1.0", "end").strip()
        if not texto:
            self.aviso("Escreva o registo.")
            return
        try:
            data = validar_data(self.d_data.get(), True)
        except ValueError:
            self.aviso("Use DD/MM/AAAA HH:MM.")
            return
        if self.d_especie.get() not in self.nomes_especies() + [GERAL]:
            self.aviso("Selecione uma espécie válida.")
            return
        if self.d_categoria.get() not in CATEGORIAS:
            self.aviso("Selecione uma categoria válida.")
            return
        anterior = next(
            (r for r in self.dados["registos"]
             if r["id"] == self.edicao_diario), {},
        )
        novo = dict(anterior)
        novo.update(
            id=self.edicao_diario or uid(),
            especie=self.d_especie.get(), categoria=self.d_categoria.get(),
            data=data.strftime(DATA_HORA), texto=texto,
        )
        registos = [
            r for r in self.dados["registos"]
            if r["id"] != self.edicao_diario
        ] + [novo]
        if self.guardar(registos=registos):
            self.limpar_diario(forcar=True)

    def editar_diario(self, evento=None):
        item = self.selecionado("diario", "registos", evento)
        if not item or not self.autorizar_descarte("diario"):
            return
        self.edicao_diario = item["id"]
        self.d_especie.set(item["especie"])
        self.d_categoria.set(item["categoria"])
        self.d_data.set(item["data"])
        self.d_texto.delete("1.0", "end")
        self.d_texto.insert("1.0", item["texto"])
        self.d_botao.configure(text="Guardar alteração")
        self.marcar_base("diario")

    def limpar_diario(self, forcar=False):
        if not forcar and not self.autorizar_descarte("diario"):
            return
        self.edicao_diario = None
        self.d_especie.set(self.especie_inicial())
        self.d_categoria.set("Geral")
        self.d_data.set(datetime.now().strftime(DATA_HORA))
        self.d_texto.delete("1.0", "end")
        self.d_botao.configure(text="Registar")
        self.marcar_base("diario")

    def apagar_diario(self):
        ids = set(self.tabelas["diario"][0].selection())
        if not ids:
            return
        limpar = self.edicao_diario in ids
        if limpar and not self.autorizar_descarte("diario"):
            return
        if not self.confirmar(f"Apagar {len(ids)} registo(s)?"):
            return
        if self.guardar(registos=[
            r for r in self.dados["registos"] if r["id"] not in ids
        ]) and limpar:
            self.limpar_diario(forcar=True)

    # --------------------------------------------------------
    # PLANTEL
    # --------------------------------------------------------

    def construir_plantel(self):
        pai = self.abas["Plantel"]
        form = ttk.LabelFrame(
            pai, text="Constituir / editar casal", padding=8
        )
        form.pack(fill="x", pady=4)
        linha = self.linha(form)
        self.p_especie = tk.StringVar(value=PADRAO)
        self.combo_especie(linha, self.p_especie)
        self.p_casal = tk.StringVar()
        self.campo(linha, "Casal:", self.p_casal, 25)

        fichas = self.linha(form)
        self.p_campos = {}
        for sexo, titulo in (
            ("Macho", "Macho — Pai"), ("Fêmea", "Fêmea — Mãe")
        ):
            ficha = ttk.LabelFrame(fichas, text=titulo, padding=6)
            ficha.pack(side="left", fill="both", expand=True, padx=4)
            self.p_campos[sexo] = {
                "anilha": tk.StringVar(), "ano": tk.StringVar()
            }
            self.campo(
                self.linha(ficha), "Anilha:",
                self.p_campos[sexo]["anilha"], 30,
            )
            self.campo(
                self.linha(ficha), "Ano:",
                self.p_campos[sexo]["ano"], 12,
            )
        ttk.Label(
            form, text="Pode guardar apenas um membro e completar depois."
        ).pack(anchor="w", padx=8, pady=3)

        linha = self.linha(pai)
        for titulo, comando in (
            ("Guardar casal", self.guardar_casal),
            ("Cancelar / Limpar", self.limpar_casal),
            ("Editar casal", self.editar_casal),
            ("Editar ave individual", self.editar_ave),
            ("Apagar", self.apagar_aves),
        ):
            self.botao(linha, titulo, comando)

        linha = self.linha(pai)
        self.p_pesquisa = tk.StringVar()
        self.campo(linha, "Pesquisar:", self.p_pesquisa, 42)
        self.botao(
            linha, "Exportar CSV",
            lambda: self.exportar("plantel", self.filtrar_plantel()), "right",
        )
        tree = self.criar_tabela(
            pai, "plantel", [
                ("especie", "Espécie", 210), ("anilha", "Anilha", 250),
                ("sexo", "Sexo", 140), ("ano", "Ano", 100),
                ("casal", "Casal", 230),
            ], ("casal", False),
        )
        tree.bind("<Double-1>", self.editar_casal)
        self.p_pesquisa.trace_add("write", lambda *a: self.atualizar())

    def filtrar_plantel(self):
        termo = normal(self.p_pesquisa.get())
        return [
            a for a in self.dados["plantel"]
            if self.visivel(a) and termo in normal(" ".join(
                a[c] for c in ("especie", "anilha", "sexo", "ano", "casal")
            ))
        ]

    def limpar_casal(self, forcar=False):
        if not forcar and not self.autorizar_descarte("plantel"):
            return
        self.ids_casal = {"Macho": None, "Fêmea": None}
        self.p_especie.set(self.especie_inicial())
        self.p_casal.set("")
        for campos in self.p_campos.values():
            for var in campos.values():
                var.set("")
        self.marcar_base("plantel")

    def editar_casal(self, evento=None):
        ave = self.selecionado("plantel", "plantel", evento)
        if not ave or not self.autorizar_descarte("plantel"):
            return
        membros = [
            a for a in self.dados["plantel"]
            if a["especie"] == ave["especie"]
            and normal(a["casal"]) == normal(ave["casal"])
        ] if ave["casal"].strip() else [ave]

        if (
            any(a["sexo"] not in ("Macho", "Fêmea") for a in membros)
            or any(
                sum(a["sexo"] == s for a in membros) > 1
                for s in ("Macho", "Fêmea")
            )
        ):
            self.editar_ave(ave)
            return

        self.limpar_casal(forcar=True)
        self.p_especie.set(ave["especie"])
        self.p_casal.set(ave["casal"])
        for item in membros:
            sexo = item["sexo"]
            self.ids_casal[sexo] = item["id"]
            for campo in ("anilha", "ano"):
                self.p_campos[sexo][campo].set(item[campo])
        self.marcar_base("plantel")

    def anilha_ocupada(self, anilha, ave_id=None, cria_id=None):
        if not anilha.strip():
            return False
        for ave in self.dados["plantel"]:
            if normal(ave["anilha"]) == normal(anilha) and ave["id"] != ave_id:
                return True
        for cria in self.dados["crias"]:
            if normal(cria["anilha"]) != normal(anilha) or cria["id"] == cria_id:
                continue
            if ave_id and cria.get("plantel_id") == ave_id:
                continue
            return True
        return False

    def ano_coerente(self, ave, ano):
        textos = []
        if ave.get("nascimento"):
            textos.append(ave["nascimento"])
        textos.extend(
            c["nascimento"] for c in self.dados["crias"]
            if c.get("plantel_id") == ave.get("id")
        )
        for texto in textos:
            try:
                nascimento = validar_data(texto)
            except ValueError:
                self.aviso("Existe uma data de nascimento inválida associada.")
                return False
            if str(nascimento.year) != ano:
                self.aviso(
                    "O ano não coincide com a data de nascimento.\n"
                    "Altere a data no separador Crias, quando aplicável."
                )
                return False
        return True

    def especie_compativel(self, ave, especie):
        if especie == ave.get("especie"):
            return True

        tem_historico = (
            ave.get("pai_id") or ave.get("mae_id")
            or any(
                c.get("plantel_id") == ave.get("id")
                or c.get("pai_id") == ave.get("id")
                or c.get("mae_id") == ave.get("id")
                for c in self.dados["crias"]
            )
            or any(
                a.get("pai_id") == ave.get("id")
                or a.get("mae_id") == ave.get("id")
                for a in self.dados["plantel"]
            )
        )
        if tem_historico:
            self.aviso(
                "Esta ave tem ligações genealógicas.\n"
                "A alteração isolada da espécie foi bloqueada para evitar\n"
                "inconsistências na filiação histórica."
            )
            return False
        return True

    def sincronizar_crias(self, aves):
        mapa = {a["id"]: a for a in aves}
        resultado = []
        for cria in self.dados["crias"]:
            nova = dict(cria)
            ligada = mapa.get(cria.get("plantel_id"))
            if ligada:
                for campo in ("anilha", "sexo", "especie"):
                    nova[campo] = ligada[campo]
            resultado.append(nova)
        return resultado

    def guardar_casal(self):
        especie = self.p_especie.get()
        casal = self.p_casal.get().strip()
        if especie not in self.dados["especies"] or not casal:
            self.aviso("Indique espécie e identificação do casal.")
            return

        ids = {i for i in self.ids_casal.values() if i}
        novas = []
        anilhas = set()
        for sexo, campos in self.p_campos.items():
            anilha = campos["anilha"].get().strip()
            ano = campos["ano"].get().strip()
            identificador = self.ids_casal[sexo]

            if not anilha and not ano:
                if identificador:
                    self.aviso("Para remover uma ave, use Apagar.")
                    return
                continue
            if not anilha or not validar_ano(ano):
                self.aviso(f"Indique anilha e ano válidos para {sexo}.")
                return
            if normal(anilha) in anilhas or self.anilha_ocupada(
                anilha, ave_id=identificador
            ):
                self.aviso(f"A anilha '{anilha}' já está em utilização.")
                return

            anterior = next(
                (a for a in self.dados["plantel"] if a["id"] == identificador),
                {},
            )
            if identificador and (
                not self.ano_coerente(anterior, ano)
                or not self.especie_compativel(anterior, especie)
            ):
                return
            nova = dict(anterior)
            nova.update(
                id=identificador or uid(), especie=especie,
                casal=casal, anilha=anilha, ano=ano, sexo=sexo,
            )
            novas.append(nova)
            anilhas.add(normal(anilha))

        if not novas:
            self.aviso("Preencha pelo menos uma ave.")
            return

        outras = [a for a in self.dados["plantel"] if a["id"] not in ids]
        ocupantes = [
            a for a in outras if a["especie"] == especie
            and normal(a["casal"]) == normal(casal)
        ]
        if any(
            a["sexo"] == n["sexo"] or a["sexo"] not in ("Macho", "Fêmea")
            for a in ocupantes for n in novas
        ):
            self.aviso("O casal já tem um membro incompatível.")
            return
        if not self.autorizar_descarte("crias"):
            return

        aves = outras + novas
        if self.guardar(plantel=aves, crias=self.sincronizar_crias(aves)):
            self.limpar_casal(forcar=True)
            self.limpar_cria(forcar=True)

    def editar_ave(self, ave=None):
        if ave is None:
            ave = self.selecionado("plantel", "plantel")
        if not ave:
            self.aviso("Selecione uma ave.")
            return

        janela = tk.Toplevel(self.root)
        janela.title("Editar ave individual")
        janela.transient(self.root)
        corpo = ttk.Frame(janela, padding=15)
        corpo.pack()
        variaveis = {}
        campos = [
            ("especie", "Espécie"), ("anilha", "Anilha"),
            ("sexo", "Sexo"), ("ano", "Ano"), ("casal", "Casal"),
        ]
        for indice, (campo, titulo) in enumerate(campos):
            ttk.Label(corpo, text=titulo + ":").grid(
                row=indice, column=0, sticky="w", pady=6
            )
            var = tk.StringVar(value=ave[campo])
            variaveis[campo] = var
            if campo in ("especie", "sexo"):
                widget = ttk.Combobox(
                    corpo, textvariable=var, state="readonly", width=30,
                    values=self.nomes_especies() if campo == "especie" else SEXOS,
                )
            else:
                widget = ttk.Entry(corpo, textvariable=var, width=32)
            widget.grid(row=indice, column=1, padx=8, pady=6)

        def guardar():
            valores = {c: v.get().strip() for c, v in variaveis.items()}
            if (
                valores["especie"] not in self.dados["especies"]
                or valores["sexo"] not in SEXOS
                or not valores["anilha"]
                or not validar_ano(valores["ano"])
            ):
                self.aviso("Preencha os campos com valores válidos.")
                return
            if self.anilha_ocupada(valores["anilha"], ave_id=ave["id"]):
                self.aviso("A anilha já está em utilização.")
                return
            if (
                not self.ano_coerente(ave, valores["ano"])
                or not self.especie_compativel(ave, valores["especie"])
            ):
                return
            outras = [a for a in self.dados["plantel"] if a["id"] != ave["id"]]
            ocupantes = [
                a for a in outras if valores["casal"]
                and a["especie"] == valores["especie"]
                and normal(a["casal"]) == normal(valores["casal"])
            ]
            if ocupantes and (
                len(ocupantes) > 1 or valores["sexo"] == "Indeterminado"
                or any(
                    a["sexo"] == valores["sexo"]
                    or a["sexo"] not in ("Macho", "Fêmea")
                    for a in ocupantes
                )
            ):
                self.aviso("Casal ocupado. Escolha outro ou deixe vazio.")
                return
            if not self.autorizar_descarte("plantel", "crias"):
                return
            nova = dict(ave)
            nova.update(valores)
            aves = outras + [nova]
            if self.guardar(plantel=aves, crias=self.sincronizar_crias(aves)):
                self.limpar_casal(forcar=True)
                self.limpar_cria(forcar=True)
                janela.destroy()

        ttk.Button(corpo, text="Guardar", command=guardar).grid(
            row=len(campos), column=1, sticky="e", pady=10
        )
        janela.grab_set()

    def apagar_aves(self):
        ids = set(self.tabelas["plantel"][0].selection())
        if not ids or not self.autorizar_descarte("plantel", "crias"):
            return
        if not self.confirmar(
            f"Apagar {len(ids)} ave(s)?\n"
            "A filiação histórica das crias será preservada."
        ):
            return
        crias = []
        for cria in self.dados["crias"]:
            nova = dict(cria)
            if nova.get("plantel_id") in ids:
                nova["plantel_id"] = ""
            crias.append(nova)
        if self.guardar(
            plantel=[a for a in self.dados["plantel"] if a["id"] not in ids],
            crias=crias,
        ):
            self.limpar_casal(forcar=True)
            self.limpar_cria(forcar=True)

    # --------------------------------------------------------
    # CRIAS
    # --------------------------------------------------------

    def construir_crias(self):
        pai = self.abas["Crias"]
        form = ttk.LabelFrame(pai, text="Registar / editar cria", padding=7)
        form.pack(fill="x", pady=4)
        self.c_especie = tk.StringVar(value=PADRAO)
        self.c_vars = {
            c: tk.StringVar()
            for c in ("casal", "anilha", "nascimento", "sexo", "ninhada")
        }
        self.c_vars["nascimento"].set(datetime.now().strftime(DATA))
        self.c_vars["sexo"].set("Indeterminado")
        linha = self.linha(form)
        combo = self.combo_especie(linha, self.c_especie)
        combo.bind("<<ComboboxSelected>>", self.mudar_especie_cria)
        ttk.Label(linha, text="Casal de origem:").pack(side="left", padx=5)
        self.combo_casal = ttk.Combobox(
            linha, textvariable=self.c_vars["casal"],
            state="readonly", width=30,
        )
        self.combo_casal.pack(side="left", padx=5)
        self.combo_casal.bind("<<ComboboxSelected>>", self.escolher_pais)

        linha = self.linha(form)
        self.campo(linha, "Anilha:", self.c_vars["anilha"], 22)
        self.campo(linha, "Nascimento:", self.c_vars["nascimento"], 12)
        ttk.Label(linha, text="DD/MM/AAAA").pack(side="left", padx=3)
        ttk.Combobox(
            linha, textvariable=self.c_vars["sexo"],
            values=SEXOS, state="readonly", width=16,
        ).pack(side="left", padx=5)
        self.campo(linha, "Ninhada:", self.c_vars["ninhada"], 10)

        self.c_pais = tk.StringVar()
        ttk.Label(form, textvariable=self.c_pais, wraplength=1120).pack(
            anchor="w", padx=7, pady=4
        )
        ttk.Label(form, text="Observações:").pack(anchor="w", padx=7)
        self.c_obs = tk.Text(form, height=3, wrap="word")
        self.c_obs.pack(fill="x", padx=7, pady=4)
        ttk.Label(
            form, text="A anilha pode ficar vazia até à identificação da cria."
        ).pack(anchor="w", padx=7)

        linha = self.linha(pai)
        self.c_botao = ttk.Button(
            linha, text="Guardar cria", command=self.guardar_cria
        )
        self.c_botao.pack(side="left")
        for titulo, comando in (
            ("Cancelar / Limpar", self.limpar_cria),
            ("Editar", self.editar_cria),
            ("Apagar", self.apagar_crias),
            ("Passar para o Plantel", self.transferir_cria),
        ):
            self.botao(linha, titulo, comando)

        linha = self.linha(pai)
        self.c_pesquisa = tk.StringVar()
        self.campo(linha, "Pesquisar:", self.c_pesquisa, 28)
        self.c_filtro = tk.StringVar(value="Todos")
        self.combo_filtro = ttk.Combobox(
            linha, textvariable=self.c_filtro,
            state="readonly", width=38,
        )
        self.combo_filtro.pack(side="left", padx=5)
        self.combo_filtro.bind("<<ComboboxSelected>>", lambda e: self.atualizar())
        self.botao(
            linha, "Exportar CSV",
            lambda: self.exportar("crias", self.filtrar_crias()), "right",
        )

        tree = self.criar_tabela(
            pai, "crias", [
                ("especie", "Espécie", 180), ("anilha", "Anilha", 170),
                ("nascimento", "Nascimento", 115), ("sexo", "Sexo", 130),
                ("casal", "Casal de origem", 150), ("ninhada", "Ninhada", 90),
                ("pai_anilha", "Pai", 170), ("mae_anilha", "Mãe", 170),
                ("situacao", "No Plantel", 100),
                ("observacoes", "Observações", 300),
            ], ("nascimento", True),
        )
        tree.bind("<Double-1>", self.editar_cria)
        self.c_pesquisa.trace_add("write", lambda *a: self.atualizar())
        self.mostrar_filiacao()

    def atualizar_casais(self):
        nomes = {}
        for ave in self.dados["plantel"]:
            if ave["especie"] == self.c_especie.get() and ave["casal"].strip():
                nomes.setdefault(normal(ave["casal"]), ave["casal"])
        atual = self.c_vars["casal"].get()
        valores = sorted(nomes.values(), key=chave_natural)
        # Preserva a seleção pendente e os casais históricos.
        if atual and atual not in valores:
            valores.append(atual)
        self.combo_casal.configure(values=sorted(valores, key=chave_natural))

    def obter_filiacao(self):
        casal = self.c_vars["casal"].get()
        if not casal:
            return None
        membros = [
            a for a in self.dados["plantel"]
            if a["especie"] == self.c_especie.get()
            and normal(a["casal"]) == normal(casal)
        ]
        machos = [a for a in membros if a["sexo"] == "Macho"]
        femeas = [a for a in membros if a["sexo"] == "Fêmea"]
        if len(membros) != 2 or len(machos) != 1 or len(femeas) != 1:
            return None
        return {
            "pai_id": machos[0]["id"], "pai_anilha": machos[0]["anilha"],
            "mae_id": femeas[0]["id"], "mae_anilha": femeas[0]["anilha"],
        }

    def mostrar_filiacao(self):
        if self.filiacao is None:
            self.c_pais.set("Escolha um casal com um macho e uma fêmea.")
        else:
            self.c_pais.set(
                f"Pai: {self.filiacao.get('pai_anilha') or 'não indicado'}"
                f" | Mãe: {self.filiacao.get('mae_anilha') or 'não indicada'}"
                " — filiação histórica deste registo."
            )

    def mudar_especie_cria(self, evento=None):
        anterior = next(
            (c for c in self.dados["crias"] if c["id"] == self.edicao_cria),
            None,
        )
        if anterior and not self.confirmar(
            "Alterar a espécie exige selecionar novamente os pais.\nContinuar?"
        ):
            self.c_especie.set(anterior["especie"])
            return
        self.c_vars["casal"].set("")
        self.filiacao = None
        self.atualizar_casais()
        self.mostrar_filiacao()

    def escolher_pais(self, evento=None):
        anterior = next(
            (c for c in self.dados["crias"] if c["id"] == self.edicao_cria),
            None,
        )
        if anterior and not self.confirmar(
            "Substituir a filiação histórica pelos membros atuais do casal?"
        ):
            self.c_especie.set(anterior["especie"])
            self.c_vars["casal"].set(anterior["casal"])
            self.filiacao = {
                c: anterior.get(c, "")
                for c in ("pai_id", "pai_anilha", "mae_id", "mae_anilha")
            }
            self.atualizar_casais()
        else:
            self.filiacao = self.obter_filiacao()
        self.mostrar_filiacao()

    def limpar_cria(self, forcar=False):
        if not forcar and not self.autorizar_descarte("crias"):
            return
        self.edicao_cria = None
        self.filiacao = None
        self.c_especie.set(self.especie_inicial())
        for var in self.c_vars.values():
            var.set("")
        self.c_vars["nascimento"].set(datetime.now().strftime(DATA))
        self.c_vars["sexo"].set("Indeterminado")
        self.c_obs.delete("1.0", "end")
        self.c_botao.configure(text="Guardar cria")
        self.atualizar_casais()
        self.mostrar_filiacao()
        self.marcar_base("crias")

    def editar_cria(self, evento=None):
        cria = self.selecionado("crias", "crias", evento)
        if not cria or not self.autorizar_descarte("crias"):
            return
        self.edicao_cria = cria["id"]
        self.c_especie.set(cria["especie"])
        for campo, var in self.c_vars.items():
            var.set(cria.get(campo, ""))
        self.filiacao = {
            c: cria.get(c, "")
            for c in ("pai_id", "pai_anilha", "mae_id", "mae_anilha")
        }
        self.c_obs.delete("1.0", "end")
        self.c_obs.insert("1.0", cria["observacoes"])
        self.c_botao.configure(text="Guardar alteração")
        self.atualizar_casais()
        self.mostrar_filiacao()
        self.marcar_base("crias")

    def cria_ciclo(self, ave_id, filiacao):
        if not ave_id:
            return False

        pais = {}
        for ave in self.dados["plantel"]:
            pais[ave["id"]] = (
                ave.get("pai_id", ""), ave.get("mae_id", "")
            )
        for cria in self.dados["crias"]:
            if cria.get("plantel_id"):
                pais[cria["plantel_id"]] = (
                    cria.get("pai_id", ""), cria.get("mae_id", "")
                )

        pendentes = [
            filiacao.get("pai_id", ""), filiacao.get("mae_id", "")
        ]
        vistos = set()
        while pendentes:
            atual = pendentes.pop()
            if not atual:
                continue
            if atual == ave_id:
                return True
            if atual in vistos:
                continue
            vistos.add(atual)
            pendentes.extend(pais.get(atual, ()))
        return False

    def guardar_cria(self):
        valores = {c: v.get().strip() for c, v in self.c_vars.items()}
        valores["especie"] = self.c_especie.get()
        if (
            valores["especie"] not in self.dados["especies"]
            or not valores["casal"] or self.filiacao is None
        ):
            self.aviso("Selecione espécie, casal e filiação válida.")
            return
        if valores["sexo"] not in SEXOS:
            self.aviso("Selecione um sexo válido.")
            return
        try:
            nascimento = validar_data(valores["nascimento"])
            if nascimento.date() > datetime.now().date():
                raise ValueError()
            valores["nascimento"] = nascimento.strftime(DATA)
        except ValueError:
            self.aviso("Use uma data de nascimento válida e não futura.")
            return

        anterior = next(
            (c for c in self.dados["crias"] if c["id"] == self.edicao_cria), {}
        )
        plantel_id = anterior.get("plantel_id", "")
        if self.anilha_ocupada(
            valores["anilha"], ave_id=plantel_id,
            cria_id=self.edicao_cria,
        ):
            self.aviso("A anilha já está em utilização.")
            return

        ligada = next(
            (a for a in self.dados["plantel"] if a["id"] == plantel_id), None
        )
        if ligada and (
            not valores["anilha"]
            or valores["sexo"] != ligada["sexo"]
            or valores["especie"] != ligada["especie"]
        ):
            self.aviso(
                "Esta cria já está no Plantel e tem de manter anilha.\n"
                "Altere o sexo em 'Editar ave individual'.\n"
                "Alterações de espécie com genealogia exigem revisão conjunta."
            )
            return
        if self.cria_ciclo(plantel_id, self.filiacao):
            self.aviso("A filiação criaria um ciclo genealógico.")
            return

        pai = self.filiacao.get("pai_id", "")
        mae = self.filiacao.get("mae_id", "")
        if pai and pai == mae:
            self.aviso("Pai e mãe não podem ser a mesma ave.")
            return
        for progenitor_id in (pai, mae):
            progenitor = next(
                (a for a in self.dados["plantel"]
                 if a["id"] == progenitor_id), None
            )
            if progenitor and progenitor["especie"] != valores["especie"]:
                self.aviso("A espécie não coincide com a dos progenitores.")
                return

        if ligada and not self.autorizar_descarte("plantel"):
            return

        nova = dict(anterior)
        nova.update(valores)
        nova.update(self.filiacao)
        nova.update(
            id=self.edicao_cria or uid(), plantel_id=plantel_id,
            observacoes=self.c_obs.get("1.0", "end").strip(),
        )
        aves = []
        for ave in self.dados["plantel"]:
            copia = dict(ave)
            if ligada and ave["id"] == plantel_id:
                copia.update(
                    anilha=nova["anilha"], nascimento=nova["nascimento"],
                    ano=str(nascimento.year), casal_origem=nova["casal"],
                    ninhada=nova["ninhada"], observacoes=nova["observacoes"],
                )
                copia.update(self.filiacao)
            aves.append(copia)
        crias = [
            c for c in self.dados["crias"] if c["id"] != self.edicao_cria
        ] + [nova]
        if self.guardar(plantel=aves, crias=crias):
            self.limpar_cria(forcar=True)
            if ligada:
                self.limpar_casal(forcar=True)

    def atualizar_filtros(self):
        identidade_anterior = self.mapa_filtros.get(self.c_filtro.get())
        pares = {}
        for cria in self.dados["crias"]:
            if self.visivel(cria) and cria["casal"]:
                identidade = (cria["especie"], normal(cria["casal"]))
                pares.setdefault(identidade, cria["casal"])
        self.mapa_filtros = {}
        selecionado = "Todos"
        for indice, identidade in enumerate(
            sorted(
                pares,
                key=lambda p: (chave_natural(p[0]), chave_natural(p[1])),
            ), 1
        ):
            rotulo = f"{indice}. {identidade[0]} — {pares[identidade]}"
            self.mapa_filtros[rotulo] = identidade
            if identidade == identidade_anterior:
                selecionado = rotulo
        self.combo_filtro.configure(values=["Todos"] + list(self.mapa_filtros))
        self.c_filtro.set(selecionado)

    def filtrar_crias(self):
        termo = normal(self.c_pesquisa.get())
        filtro = self.mapa_filtros.get(self.c_filtro.get())
        ids_aves = {a["id"] for a in self.dados["plantel"]}
        resultado = []
        for cria in self.dados["crias"]:
            if not self.visivel(cria):
                continue
            if filtro and (cria["especie"], normal(cria["casal"])) != filtro:
                continue
            item = dict(cria)
            item["situacao"] = (
                "Sim" if cria.get("plantel_id") in ids_aves else "Não"
            )
            texto = " ".join(
                str(item.get(c, "")) for c in (
                    "especie", "anilha", "nascimento", "sexo", "casal",
                    "ninhada", "pai_anilha", "mae_anilha", "observacoes",
                )
            )
            if termo in normal(texto):
                resultado.append(item)
        return resultado

    def apagar_crias(self):
        ids = set(self.tabelas["crias"][0].selection())
        if not ids:
            return
        limpar = self.edicao_cria in ids
        if limpar and not self.autorizar_descarte("crias"):
            return
        if not self.confirmar(
            f"Apagar {len(ids)} cria(s)?\n"
            "Aves já transferidas permanecem no Plantel."
        ):
            return
        if self.guardar(crias=[
            c for c in self.dados["crias"] if c["id"] not in ids
        ]) and limpar:
            self.limpar_cria(forcar=True)

    def transferir_cria(self):
        cria = self.selecionado("crias", "crias")
        if not cria:
            self.aviso("Selecione uma cria.")
            return
        if self.edicao_cria == cria["id"] or self.alterado("crias"):
            self.aviso("Guarde ou cancele o formulário antes de transferir.")
            return
        if any(a["id"] == cria.get("plantel_id") for a in self.dados["plantel"]):
            self.aviso("Esta cria já está no Plantel.")
            return
        if not cria["anilha"].strip():
            self.aviso("Preencha a anilha antes de transferir.")
            return
        if self.anilha_ocupada(cria["anilha"], cria_id=cria["id"]):
            self.aviso("A anilha já está em utilização.")
            return
        if cria["sexo"] not in SEXOS:
            self.aviso("Corrija o sexo da cria.")
            return
        try:
            nascimento = validar_data(cria["nascimento"])
            if nascimento.date() > datetime.now().date():
                raise ValueError()
        except ValueError:
            self.aviso("Corrija a data de nascimento.")
            return
        if not self.confirmar(
            f"Adicionar {cria['anilha']} ao Plantel, sem casal atribuído?"
        ):
            return

        ave = dict(cria)
        ave.update(
            id=uid(), ano=str(nascimento.year), casal="",
            casal_origem=cria["casal"], cria_origem_id=cria["id"],
        )
        ave.pop("plantel_id", None)
        crias = []
        for item in self.dados["crias"]:
            copia = dict(item)
            if copia["id"] == cria["id"]:
                copia["plantel_id"] = ave["id"]
            crias.append(copia)
        if self.guardar(plantel=self.dados["plantel"] + [ave], crias=crias):
            self.limpar_cria(forcar=True)
            messagebox.showinfo(
                "Plantel", "Cria adicionada, sem casal atribuído.",
                parent=self.root,
            )

    # --------------------------------------------------------
    # ATUALIZAÇÃO
    # --------------------------------------------------------

    def atualizar(self):
        especies = self.nomes_especies()
        self.combo_global.configure(values=[TODAS] + especies)
        for combo, geral in self.combos_especies:
            if combo.winfo_exists():
                combo.configure(values=([GERAL] if geral else []) + especies)
        self.atualizar_textos()
        self.atualizar_casais()
        self.atualizar_filtros()
        self.preencher("diario", self.filtrar_diario())
        self.preencher("plantel", self.filtrar_plantel())
        self.preencher("crias", self.filtrar_crias())

        casais = {
            (a["especie"], normal(a["casal"]))
            for a in self.dados["plantel"] if a["casal"].strip()
        }
        self.estado.set(
            f"{len(self.dados['registos'])} registos | "
            f"{len(self.dados['plantel'])} aves | "
            f"{len(casais)} identificações de casal | "
            f"{len(self.dados['crias'])} crias | "
            f"{len(especies)} espécies\nDados: {FICHEIRO}"
        )


# ============================================================
# ERROS E ARRANQUE
# ============================================================

def janela_erro(root, titulo, detalhes):
    janela = tk.Toplevel(root)
    janela.title(titulo)
    janela.geometry("850x500")
    ttk.Label(
        janela,
        text="Pode selecionar e copiar estes detalhes para diagnóstico.",
        padding=10,
    ).pack(fill="x")
    frame = ttk.Frame(janela)
    frame.pack(fill="both", expand=True, padx=10, pady=8)
    texto = tk.Text(frame, wrap="word", font=("Consolas", 10))
    scroll = ttk.Scrollbar(frame, command=texto.yview)
    texto.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    texto.pack(fill="both", expand=True)
    texto.insert("1.0", detalhes)
    texto.configure(state="disabled")
    ttk.Button(janela, text="Fechar", command=janela.destroy).pack(pady=10)
    janela.lift()
    return janela


def main():
    root = tk.Tk()
    root.withdraw()

    def erro_callback(tipo, valor, tb):
        janela_erro(
            root, "Erro na aplicação",
            "".join(traceback.format_exception(tipo, valor, tb)),
        )

    root.report_callback_exception = erro_callback

    try:
        # Confirma que o ficheiro não mudou durante a leitura.
        assinatura_antes = assinatura_ficheiro()
        dados = carregar()
        assinatura_depois = assinatura_ficheiro()
        if assinatura_antes != assinatura_depois:
            raise RuntimeError(
                "O ficheiro mudou durante a leitura. Tente abrir novamente."
            )
    except Exception as erro:
        messagebox.showerror(
            "Erro ao carregar",
            "Não foi possível carregar os dados.\n\n"
            f"{erro}\n\n"
            "O ficheiro original não foi alterado.\n"
            "A aplicação será encerrada para evitar perda de dados.\n\n"
            f"Ficheiro: {FICHEIRO}",
            parent=root,
        )
        root.destroy()
        return

    try:
        app = Aplicacao(root, dados, assinatura_depois)
    except Exception:
        janela = janela_erro(
            root, "Erro no arranque", traceback.format_exc()
        )
        root.wait_window(janela)
        root.destroy()
        return

    root.deiconify()
    root.mainloop()


if __name__ == "__main__":
    main()
