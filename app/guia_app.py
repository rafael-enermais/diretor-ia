# -*- coding: utf-8 -*-
"""Diretor.IA - GUIA DO APP: a fonte unica do "como usar" (tela Ajuda e ferramenta `como_usar_o_app` do Assistente leem daqui; assim os dois nunca se contradizem).
Ao criar ou mudar uma tela, atualize este arquivo (o teste confere que toda tela do menu tem verbete). Puro: sem Streamlit e sem banco."""
from __future__ import annotations

import re
import unicodedata

PAGINAS = [
    {"pagina": "visao-geral", "titulo": "Visão geral", "menu": "Visão geral",
     "serve": "Mostra, em uma tela, quantos indicadores e entregáveis existem, quantos já têm valor e como estão (no alvo, atenção, fora da meta).",
     "como": ["Abra «Visão geral» no menu à esquerda.", "Leia os números do topo e a tabela por categoria; clique em «Atualizar agora» para reler o banco na hora (ele já se atualiza a cada 1 minuto)."],
     "dicas": ["«Sem lançamento» não quer dizer ruim: quer dizer que o número ainda não chegou do app de origem."]},
    {"pagina": "painel", "titulo": "Painel executivo", "menu": "Painel executivo",
     "serve": "O retrato do momento em gráficos: pontos de atenção, situação por categoria, evolução de cada indicador com tendência simples e comparação lado a lado.",
     "como": ["Abra «Painel executivo».", "Passe o mouse sobre o gráfico para ver os valores (a roda do mouse não mexe no gráfico).",
              "Na comparação, escolha até 5 indicadores para ver a evolução juntos."],
     "dicas": ["A tendência é só uma reta sobre os meses já gravados (precisa de 3 meses ou mais). Não é previsão oficial."]},
    {"pagina": "categorias", "titulo": "Categorias e detalhe do número", "menu": "Categorias",
     "serve": "Mostra cada indicador de uma categoria com valor, meta e status, e o DETALHE de como o número se formou (faixas de atraso, quantidades, composição) para você investigar um número fora do comum.",
     "como": ["Abra «Categorias» e escolha a categoria.", "Em «Detalhe de um indicador», escolha o indicador.",
              "Abra «Detalhe do número»: a composição (numerador ÷ denominador), as tabelas com % do total e os avisos 👀.",
              "Ligue «Mostrar histórico mês a mês» para ver a evolução e a tabela por mês."],
     "dicas": ["O aviso 👀 aparece quando o valor mudou 30% ou mais frente ao mês anterior, ou quando 20% ou mais do vencido está há mais de 90 dias. É um convite para olhar, não um veredito.",
               "Se houver pendências em aberto ligadas ao indicador, elas aparecem logo abaixo do detalhe."]},
    {"pagina": "entregaveis", "titulo": "Entregáveis", "menu": "Entregáveis",
     "serve": "Lista os 44 entregáveis com responsável, prazo, meta e resultado quando houver.",
     "como": ["Abra «Entregáveis».", "Use os filtros de responsável, prazo e apuração."],
     "dicas": ["Apuração «Checklist» = alguém confirma que fez; «Medido nos dados» = o app mede sozinho; «Misto» = os dois."]},
    {"pagina": "reports", "titulo": "Reports e pendências", "menu": "Reports e pendências",
     "serve": "Guarda o que os colaboradores relatam (dificuldades, pendências, problemas, evoluções), com urgência, situação, nota sua e histórico. É uma ajuda à gestão: nada é obrigatório e nada é apagado.",
     "como": ["Aba «Acompanhamento»: veja os números do topo, filtre (por padrão mostra só os em aberto) e edite direto na tabela: tipo, urgência, situação, vínculo, título, descrição e nota. Depois clique em «Salvar alterações».",
              "Para tirar um item da lista, mude a situação para «Arquivada» (não apaga; dá para voltar mudando a situação de novo).",
              "Aba «Evolução»: novos × resolvidos por semana, itens por tipo, em aberto por colaborador e por indicador vinculado.",
              "Aba «Histórico de um item»: quem mudou o quê e quando (de → para).",
              "Aba «Registrar novo»: digite um item na mão; só preencha o que quiser.",
              "Para levar a uma reunião: clique em «Preparar planilha (Excel)» e depois em «Baixar planilha». Ela traz a lista que está na tela (com os filtros), um resumo e o histórico."],
     "dicas": ["Os itens chegam sozinhos dos apps dos colaboradores; o texto deles é relato de terceiros e só é lido como informação.",
               "Urgência: Baixa, Média, Alta, Crítica. Situação: Nova, Em acompanhamento, Resolvida, Arquivada. Tipo: Dificuldade, Pendência, Problema, Evolução, Outro."]},
    {"pagina": "vinculos", "titulo": "Vínculo de um item com um indicador", "menu": "Reports e pendências",
     "serve": "Liga um relato a um indicador (I##) ou entregável (E##) para você ver as pendências de cada número. O app só SUGERE; o vínculo só vale depois que você confirma.",
     "como": ["Em «Reports e pendências > Acompanhamento», abra «Vínculos sugeridos para confirmar».", "Clique em «Confirmar» se a sugestão está certa, ou em «Não é esse» para o app parar de sugerir aquele indicador para aquele relato.",
              "Também dá para escolher o vínculo na coluna «Vínculo» da tabela, ou ao registrar um item novo."],
     "dicas": ["A sugestão usa o código citado no texto (ex.: I27) ou o nome do indicador. Nada é gravado sem o seu clique."]},
    {"pagina": "relatorios", "titulo": "Relatórios (PDF)", "menu": "Relatórios",
     "serve": "Gera um relatório em PDF no padrão visual do Grupo Enermais (o mesmo do GDF e do EGC): capa, resumo, pontos de atenção, indicadores por categoria com detalhe, entregáveis e pendências.",
     "como": ["Abra «Relatórios».", "Marque as seções que quer e, se quiser, escreva uma observação sua (ela sai no relatório).", "Clique em «Gerar relatório» e depois em «Baixar PDF»."],
     "dicas": ["O PDF é feito na hora com o que o painel mostra e não fica guardado no app. Os valores são os dos apps de origem."]},
    {"pagina": "prontidao", "titulo": "Prontidão e fontes", "menu": "Prontidão e fontes",
     "serve": "Mostra o que já está ligado a uma fonte e recebendo dado, e o que ainda falta chegar, por app de origem.",
     "como": ["Abra «Prontidão e fontes».", "O administrador pode rodar a «verificação técnica» para conferir banco, catálogo, acesso e permissões."],
     "dicas": []},
    {"pagina": "assistente", "titulo": "Assistente (IA)", "menu": "Assistente (IA)",
     "serve": "Responde em português sobre indicadores, entregáveis e pendências, e também tira dúvidas de como usar o painel. Só lê o que o painel mostra: não grava nada.",
     "como": ["Abra «Assistente (IA)» e escreva a pergunta (ou clique numa sugestão).", "Peça gráficos (ex.: «mostre a evolução do I27») e comparações.", "Pergunte «como faço para…» e ele explica o passo a passo."],
     "dicas": ["Ele avisa quando um valor da resposta não bate com as consultas: confira no painel antes de usar.", "Cada pergunta usa crédito da IA: o painel avisa a partir de 60 perguntas no dia."]},
    {"pagina": "ajuda", "titulo": "Ajuda", "menu": "Ajuda", "serve": "Esta página: como usar cada tela, o que significam os termos e respostas rápidas.",
     "como": ["Leia o verbete da tela, ou pergunte ao Assistente."], "dicas": []},
    {"pagina": "logs", "titulo": "Logs (admin)", "menu": "Logs (admin)", "so_admin": True,
     "serve": "Só para quem administra o painel: registro de eventos e erros, com o código «E-DIRETOR-AAMMDD-xxxx» que aparece nas mensagens de erro.",
     "como": ["Abra «Logs (admin)» e procure o código do erro para ver o motivo técnico."], "dicas": []},
]

GLOSSARIO = [
    ("No alvo", "🟢 Dentro da meta."), ("Atenção", "🟡 Perto do limite da meta."), ("Fora da meta", "🔴 Fora da meta."),
    ("Só informativo (Sem meta)", "🔵 Tem valor gravado, mas o app de origem não tem meta numérica para julgar (ex.: contas a receber). Conta como «com valor»."),
    ("Sem lançamento", "⚪ O número ainda não chegou. Não significa que esteja ruim."),
    ("Detalhe do número", "O que o app de origem gravou junto do valor: faixas, quantidades, composição. Serve para ver por que o número é o que é."),
    ("Composição", "Numerador ÷ denominador gravados pelo app de origem (ex.: vencido ÷ total em aberto). O painel só faz a divisão para mostrar o percentual."),
    ("Aviso 👀", "Convite para olhar um número: variou 30% ou mais frente ao mês anterior, ou 20% ou mais do vencido está há mais de 90 dias."),
    ("Urgência", "Baixa, Média, Alta ou Crítica: o quanto o item pede atenção."), ("Situação", "Nova, Em acompanhamento, Resolvida ou Arquivada."),
    ("Arquivada", "Tira o item da lista sem apagar. O histórico fica guardado."), ("Vínculo", "Ligação opcional de um item com um indicador (I##) ou entregável (E##); só vale depois de confirmada."),
    ("Origem", "Quem enviou o item: «manual» (digitado aqui) ou o nome do app do colaborador."), ("Tendência", "Reta simples sobre os meses já gravados (3 ou mais). Não é previsão oficial."),
]

PERGUNTAS = [
    ("O painel recalcula os indicadores?", "Não. Cada app calcula o seu e grava; o painel só lê e mostra. O número aqui é o mesmo do app de origem."),
    ("Por que um indicador está «Sem lançamento»?", "Porque o app de origem ainda não gravou o valor do mês. Veja em «Prontidão e fontes» o que falta chegar."),
    ("Posso apagar um item de pendência?", "Não: nada é apagado. Mude a situação para «Arquivada» e ele sai da lista; o histórico continua guardado."),
    ("Como mudo a urgência ou a situação de um item?", "Em «Reports e pendências > Acompanhamento», clique na célula, escolha o novo valor e clique em «Salvar alterações»."),
    ("Como levo as pendências para uma reunião?", "Em «Reports e pendências», clique em «Preparar planilha (Excel)» e depois em «Baixar planilha»."),
    ("Como gero o relatório em PDF?", "Abra «Relatórios», marque as seções, clique em «Gerar relatório» e depois em «Baixar PDF»."),
    ("O vínculo sugerido foi gravado sozinho?", "Não. O app só sugere; o vínculo só vale depois que você clica em «Confirmar»."),
    ("No I27 (contas a pagar) a meta é zero vencido. Onde vejo o percentual vencido?", "Em «Categorias > Detalhe do número», na «Composição do número» (vencido ÷ total em aberto) e nas faixas de atraso com % do total."),
    ("Quem vê o quê?", "Entra só quem está na lista de acesso. O administrador vê também Logs e o bloco técnico da Ajuda; o Diretor vê as mesmas telas, sem esses blocos."),
    ("Algo deu errado e apareceu um código.", "Anote o código «E-DIRETOR-AAMMDD-xxxx» e informe a quem administra o painel; ele procura o motivo em Logs."),
]


def _norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(s or "").lower()) if unicodedata.category(c) != "Mn")


def _tokens(s: str) -> set:
    """Palavras de 3+ letras (sem acento), cortadas nos 6 primeiros caracteres: 'exporto' e 'exportar' contam como a mesma palavra."""
    parada = {"para", "como", "que", "uma", "com", "dos", "das", "nos", "nas", "por", "mas", "isso", "esta", "este", "significa"}
    return {w[:6] for w in re.findall(r"[a-z0-9]{3,}", _norm(s)) if w not in parada}


def paginas(admin: bool = False) -> list:
    return [p for p in PAGINAS if admin or not p.get("so_admin")]


def pagina(nome: str, admin: bool = False):
    n = _norm(nome).strip()
    for p in paginas(admin):
        if n in (_norm(p["pagina"]), _norm(p["titulo"]), _norm(p["menu"])):
            return p
    return None


def buscar(texto: str, admin: bool = False, limite: int = 4) -> dict:
    """Procura por palavras nos verbetes de tela, glossario e perguntas. Devolve os melhores (so' o que tem pelo menos 1 palavra em comum)."""
    q = _tokens(texto)
    if not q:
        return {"paginas": [], "glossario": [], "perguntas": []}

    def nota(titulo, corpo):            # palavra no titulo vale 3 vezes mais que no corpo
        return 3 * len(q & _tokens(titulo)) + len(q & _tokens(corpo))
    pg = sorted(((nota(p["titulo"] + " " + p["menu"], " ".join([p["serve"]] + p["como"] + p["dicas"])), p) for p in paginas(admin)), key=lambda x: -x[0])
    gl = sorted(((nota(t, d), (t, d)) for t, d in GLOSSARIO), key=lambda x: -x[0])
    fq = sorted(((nota(a, b), (a, b)) for a, b in PERGUNTAS), key=lambda x: -x[0])
    return {"paginas": [p for n, p in pg if n][:limite], "glossario": [x for n, x in gl if n][:limite], "perguntas": [x for n, x in fq if n][:limite]}
