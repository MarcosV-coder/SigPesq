"""Aba Relatórios do SIGPesq: consultas, prévia e exportação em PDF."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from tkinter import filedialog, messagebox
from unicodedata import combining, normalize
from xml.sax.saxutils import escape

import customtkinter as ctk

from db import transacao
from modelos import AGENCIAS, FOMENTOS, FUNCOES, MEIOS, PRODUCOES, SITUACOES, TIPOS
from repositorio import identidade, linhas
from validacao import formatar
from visual import AZUL, BORDA, BRANCO, CLARO, MUTED, TITULO, botao, fonte, label


@dataclass(frozen=True)
class Tabela:
    colunas: tuple[str, ...]
    pesos: tuple[int, ...]
    linhas: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class Relatorio:
    titulo: str
    filtros: tuple[tuple[str, str], ...]
    gerado_em: datetime
    detalhes: Tabela
    resumo: Tabela | None = None
    totais_contratos: tuple[tuple[int, Decimal, Decimal], ...] = ()


TIPOS_RELATORIO = {
    'projetos': 'Projetos por coordenador',
    'equipe': 'Equipe por projeto',
    'producoes': 'Produções científicas',
    'financiamentos': 'Financiamentos por agência',
    'multiprojetos': 'Participantes em vários projetos',
}

FILTROS_RELATORIO = {
    'projetos': ('docente', 'situacao'),
    'equipe': ('projeto', 'funcao'),
    'producoes': ('projeto', 'ano', 'tipo_producao'),
    'financiamentos': ('agencia', 'fomento'),
    'multiprojetos': ('tipo_participante', 'minimo'),
}

ROTULOS_FILTROS = {
    'docente': 'Docente',
    'situacao': 'Situação',
    'projeto': 'Projeto',
    'funcao': 'Função',
    'ano': 'Ano',
    'tipo_producao': 'Tipo de produção',
    'agencia': 'Agência',
    'fomento': 'Tipo de fomento',
    'tipo_participante': 'Tipo de participante',
    'minimo': 'Mínimo de projetos',
}

OPCOES_FIXAS = {
    'situacao': SITUACOES,
    'funcao': FUNCOES,
    'tipo_producao': PRODUCOES,
    'agencia': AGENCIAS,
    'fomento': FOMENTOS,
    'tipo_participante': TIPOS,
}


def opcoes_relatorios(sessao):
    with transacao() as cur:
        identidade(cur, sessao)
        projetos = linhas(cur, 'SELECT codigo_projeto, titulo FROM projeto WHERE excluido_em IS NULL ORDER BY titulo, codigo_projeto')
        docentes = linhas(cur, "SELECT cpf, nome FROM participante WHERE tipo_participante = '2' AND excluido_em IS NULL ORDER BY nome, cpf")
        anos = linhas(cur, 'SELECT DISTINCT ano_publicacao FROM producao_cientifica WHERE excluido_em IS NULL ORDER BY ano_publicacao DESC')

    # Distingue homônimos no seletor e mantém seu identificador apenas no mapa interno.
    totais = Counter(d['nome'] for d in docentes)
    ocorrencias = Counter()
    opcoes_docentes = []
    for docente in docentes:
        nome = docente['nome']
        ocorrencias[nome] += 1
        rotulo = f'{nome} ({ocorrencias[nome]})' if totais[nome] > 1 else nome
        opcoes_docentes.append((docente['cpf'], rotulo))

    return {
        **OPCOES_FIXAS,
        'projeto': [(p['codigo_projeto'], f"{p['codigo_projeto']} · {p['titulo']}") for p in projetos],
        'docente': opcoes_docentes,
        'ano': [(a['ano_publicacao'], str(a['ano_publicacao'])) for a in anos],
    }


def _buscar(cur, base, clausulas, filtros, ordem, *, visibilidade):
    selecionadas = [
        (clausula, str(filtros[chave]) if chave in OPCOES_FIXAS else filtros[chave])
        for chave, clausula in clausulas
        if filtros.get(chave) is not None
    ]
    condicoes = [visibilidade, *(clausula for clausula, _ in selecionadas)]
    where = ' WHERE ' + ' AND '.join(condicoes)
    return linhas(cur, base + where + ' ORDER BY ' + ordem, tuple(valor for _, valor in selecionadas))


def _categoria(opcoes, codigo):
    return dict(opcoes).get(codigo, f'Código {codigo}' if codigo is not None else '—')


def _tabela(colunas, pesos, registros):
    return Tabela(tuple(colunas), tuple(pesos), tuple(tuple(formatar(v) for v in linha) for linha in registros))


def _projetos(cur, filtros):
    registros = _buscar(cur, '''
        SELECT p.codigo_projeto, p.titulo, p.situacao, p.data_inicio, p.data_termino,
               c.nome AS coordenador
        FROM projeto p
        LEFT JOIN (
            SELECT v.codigo_projeto, d.cpf, d.nome
            FROM vinculo_projeto_participante v
            JOIN participante d ON d.cpf = v.cpf
            WHERE v.funcao_desempenhada = '3' AND d.tipo_participante = '2'
              AND v.excluido_em IS NULL AND d.excluido_em IS NULL
        ) c ON c.codigo_projeto = p.codigo_projeto
        ''', (('docente', 'c.cpf = %s'), ('situacao', 'p.situacao = %s')),
        filtros, 'p.titulo, p.codigo_projeto, c.nome, c.cpf',
        visibilidade='p.excluido_em IS NULL')
    projetos = {}
    for registro in registros:
        _, coordenadores = projetos.setdefault(registro['codigo_projeto'], (registro, []))
        if registro['coordenador'] is not None:
            coordenadores.append(registro['coordenador'])

    return _tabela(
        ('Código', 'Projeto', 'Coordenação', 'Situação', 'Início', 'Término'), (8, 28, 23, 15, 13, 13),
        ((r['codigo_projeto'], r['titulo'], '; '.join(nomes) or 'Não atribuído',
          _categoria(SITUACOES, r['situacao']), r['data_inicio'], r['data_termino'])
         for r, nomes in projetos.values()),
    )


def _equipe(cur, filtros):
    registros = _buscar(cur, '''
        SELECT p.codigo_projeto, p.titulo AS projeto, a.nome, a.tipo_participante, v.funcao_desempenhada,
               v.data_entrada, v.data_saida
        FROM vinculo_projeto_participante v
        JOIN participante a ON a.cpf = v.cpf
        JOIN projeto p ON p.codigo_projeto = v.codigo_projeto
        ''', (('projeto', 'v.codigo_projeto = %s'), ('funcao', 'v.funcao_desempenhada = %s')),
        filtros, 'p.titulo, p.codigo_projeto, a.nome, a.cpf',
        visibilidade='v.excluido_em IS NULL AND a.excluido_em IS NULL AND p.excluido_em IS NULL')
    return _tabela(
        ('Projeto', 'Participante', 'Tipo', 'Função', 'Entrada', 'Saída'), (24, 22, 17, 15, 11, 11),
        ((f"{r['codigo_projeto']} · {r['projeto']}", r['nome'], _categoria(TIPOS, r['tipo_participante']),
          _categoria(FUNCOES, r['funcao_desempenhada']), r['data_entrada'], r['data_saida'])
         for r in registros),
    )


def _producoes(cur, filtros):
    registros = _buscar(cur, '''
        SELECT c.codigo_projeto, c.codigo_prod, c.titulo, c.tipo_prod, c.meio_divulgacao,
               c.ano_publicacao, p.titulo AS projeto, a.nome AS autor
        FROM producao_cientifica c
        JOIN projeto p ON p.codigo_projeto = c.codigo_projeto
        LEFT JOIN autoria_producao ap
          ON ap.codigo_projeto = c.codigo_projeto AND ap.codigo_prod = c.codigo_prod
        LEFT JOIN participante a ON a.cpf = ap.cpf
        ''', (('projeto', 'c.codigo_projeto = %s'), ('ano', 'c.ano_publicacao = %s'),
              ('tipo_producao', 'c.tipo_prod = %s')),
        filtros, 'c.ano_publicacao DESC, c.titulo, c.codigo_projeto, c.codigo_prod, a.nome, a.cpf',
        visibilidade='c.excluido_em IS NULL AND p.excluido_em IS NULL')
    producoes = {}
    for registro in registros:
        chave = (registro['codigo_projeto'], registro['codigo_prod'])
        _, autores = producoes.setdefault(chave, (registro, []))
        if registro['autor'] is not None:
            autores.append(registro['autor'])

    return _tabela(
        ('Projeto', 'Título', 'Autores', 'Ano', 'Tipo', 'Divulgação'), (20, 24, 24, 7, 13, 12),
        ((f"{r['codigo_projeto']} · {r['projeto']}", r['titulo'], '; '.join(autores) or 'Sem autoria registrada',
          r['ano_publicacao'], _categoria(PRODUCOES, r['tipo_prod']), _categoria(MEIOS, r['meio_divulgacao']))
         for r, autores in producoes.values()),
    )


def _financiamentos(cur, filtros):
    registros = _buscar(cur, '''
        SELECT f.codigo_financiamento, f.agencia_financiadora, f.tipo_fomento, f.valor_total,
               v.valor_destinado, p.codigo_projeto, p.titulo AS projeto
        FROM financiamento f
        LEFT JOIN vinculo_projeto_financiamento v
          ON v.codigo_financiamento = f.codigo_financiamento AND v.excluido_em IS NULL
        LEFT JOIN projeto p ON p.codigo_projeto = v.codigo_projeto AND p.excluido_em IS NULL
        ''', (('agencia', 'f.agencia_financiadora = %s'), ('fomento', 'f.tipo_fomento = %s')),
        filtros, 'f.agencia_financiadora, f.codigo_financiamento, p.titulo, p.codigo_projeto',
        visibilidade='f.excluido_em IS NULL')
    contratos = {}
    for registro in registros:
        _, destinacoes = contratos.setdefault(registro['codigo_financiamento'], (registro, []))
        if registro['codigo_projeto'] is not None:
            destinacoes.append((registro['codigo_projeto'], registro['projeto'], registro['valor_destinado']))

    totais = []
    detalhes = []
    # O JOIN repete o valor contratado por projeto. Somamos após agrupar pelo código do contrato.
    for contrato, destinacoes in contratos.values():
        total = contrato['valor_total']
        destinado = sum((valor for _, _, valor in destinacoes), Decimal('0'))
        agencia = contrato['agencia_financiadora']
        totais.append((agencia, total, destinado))
        projetos = '\n'.join(f'{codigo} · {nome} ({formatar(valor)})' for codigo, nome, valor in destinacoes)
        detalhes.append((
            contrato['codigo_financiamento'], _categoria(AGENCIAS, agencia),
            _categoria(FOMENTOS, contrato['tipo_fomento']), projetos or 'Sem destinação',
            total, destinado, total - destinado,
        ))

    return _tabela(
        ('Código', 'Agência', 'Fomento', 'Projetos e valores destinados', 'Contratado', 'Destinado', 'Saldo'),
        (7, 10, 11, 33, 13, 13, 13), detalhes,
    ), tuple(totais)


def _resumo_financeiro(totais):
    agencias = {}
    for agencia, total, destinado in totais:
        total_anterior, destinado_anterior = agencias.get(agencia, (Decimal('0'), Decimal('0')))
        agencias[agencia] = (total_anterior + total, destinado_anterior + destinado)
    return _tabela(
        ('Agência', 'Contratado', 'Destinado', 'Saldo'), (25, 25, 25, 25),
        ((_categoria(AGENCIAS, agencia), total, destinado, total - destinado)
         for agencia, (total, destinado) in agencias.items()),
    )


def _multiprojetos(cur, filtros):
    tipo_participante = filtros.get('tipo_participante')
    if tipo_participante is not None:
        tipo_participante = str(tipo_participante)
    registros = linhas(cur, '''
        SELECT a.cpf AS participante_id, a.nome, a.tipo_participante,
               selecionados.quantidade, p.codigo_projeto, p.titulo AS projeto
        FROM (
            SELECT cpf, COUNT(DISTINCT codigo_projeto) AS quantidade
            FROM vinculo_projeto_participante
            WHERE excluido_em IS NULL
            GROUP BY cpf
            HAVING COUNT(DISTINCT codigo_projeto) >= %s
        ) selecionados
        JOIN participante a ON a.cpf = selecionados.cpf
        JOIN vinculo_projeto_participante v ON v.cpf = a.cpf
        JOIN projeto p ON p.codigo_projeto = v.codigo_projeto
        WHERE a.excluido_em IS NULL AND v.excluido_em IS NULL AND p.excluido_em IS NULL
          AND (%s IS NULL OR a.tipo_participante = %s)
        ORDER BY selecionados.quantidade DESC, a.nome, a.cpf, p.titulo, p.codigo_projeto
    ''', (filtros['minimo'], tipo_participante, tipo_participante))
    participantes = {}
    for registro in registros:
        _, projetos = participantes.setdefault(registro['participante_id'], (registro, []))
        projetos.append(f"{registro['codigo_projeto']} · {registro['projeto']}")
    return _tabela(
        ('Participante', 'Tipo', 'Projetos distintos', 'Projetos'), (26, 20, 15, 39),
        ((r['nome'], _categoria(TIPOS, r['tipo_participante']), r['quantidade'], '\n'.join(projetos))
         for r, projetos in participantes.values()),
    )


CONSULTAS = {
    'projetos': _projetos,
    'equipe': _equipe,
    'producoes': _producoes,
    'financiamentos': _financiamentos,
    'multiprojetos': _multiprojetos,
}


def gerar_relatorio(sessao, tipo, filtros, rotulos):
    with transacao() as cur:
        identidade(cur, sessao)
        resultado = CONSULTAS[tipo](cur, filtros)
    detalhes, totais = resultado if tipo == 'financiamentos' else (resultado, ())
    resumo = _resumo_financeiro(totais) if tipo == 'financiamentos' else None
    return Relatorio(TIPOS_RELATORIO[tipo], tuple(rotulos), datetime.now(), detalhes, resumo, totais)


def _normalizar_busca(texto):
    decomposicao = normalize('NFD', texto.casefold())
    return ''.join(c for c in decomposicao if not combining(c))


def aplicar_busca(relatorio, texto):
    termo = _normalizar_busca(texto.strip())
    if not termo:
        return relatorio
    indices = [i for i, linha in enumerate(relatorio.detalhes.linhas)
               if termo in _normalizar_busca(' '.join(linha))]
    detalhes = replace(relatorio.detalhes, linhas=tuple(relatorio.detalhes.linhas[i] for i in indices))
    totais = tuple(relatorio.totais_contratos[i] for i in indices) if relatorio.resumo is not None else ()
    resumo = _resumo_financeiro(totais) if relatorio.resumo is not None else None
    return replace(relatorio, detalhes=detalhes, resumo=resumo, totais_contratos=totais,
                   filtros=relatorio.filtros + (('Busca textual', 'Aplicada'),))


def salvar_pdf(relatorio, caminho):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, TableStyle

    buffer = BytesIO()
    azul = colors.HexColor(AZUL)
    estilos = getSampleStyleSheet()
    estilo_texto = ParagraphStyle('Celula', fontSize=9, leading=12)
    estilo_cabecalho = ParagraphStyle('Cabecalho', parent=estilo_texto, fontName='Helvetica-Bold', textColor=colors.white)
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4), title=f'SIGPesq — {relatorio.titulo}',
        leftMargin=32, rightMargin=32, topMargin=32, bottomMargin=36,
    )

    def paragrafo(valor, estilo):
        texto = ''.join(c for c in valor if c in '\t\n' or ord(c) >= 32)
        return Paragraph(escape(texto).replace('\n', '<br/>'), estilo)

    def tabela_pdf(dados):
        linhas_pdf = [[paragrafo(c, estilo_cabecalho) for c in dados.colunas]]
        linhas_pdf += [[paragrafo(c, estilo_texto) for c in linha] for linha in dados.linhas]
        larguras = [(doc.width - 12) * peso / sum(dados.pesos) for peso in dados.pesos]
        tabela = LongTable(linhas_pdf, colWidths=larguras, repeatRows=1, splitInRow=1)
        tabela.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), azul),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f6fb')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LINEBELOW', (0, 1), (-1, -1), 0.3, colors.HexColor(BORDA)),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ]))
        return tabela

    def rodape(canvas, documento):
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(azul)
        canvas.drawString(documento.leftMargin, 19, 'SIGPesq')
        canvas.drawRightString(documento.pagesize[0] - documento.rightMargin, 19, f'Página {documento.page}')
        canvas.restoreState()

    filtros = '  |  '.join(f'{nome}: {valor}' for nome, valor in relatorio.filtros)
    data = relatorio.gerado_em.strftime('%d/%m/%Y às %H:%M')
    elementos = [
        paragrafo(f'SIGPesq — {relatorio.titulo}', estilos['Heading1']),
        paragrafo(f'Gerado em {data}  |  {len(relatorio.detalhes.linhas)} registro(s)', estilos['Normal']),
        paragrafo(f'Filtros: {filtros}', estilos['Normal']),
        Spacer(1, 12),
    ]
    if relatorio.resumo and relatorio.resumo.linhas:
        elementos.extend([Paragraph('Resumo por agência', estilos['Heading2']), tabela_pdf(relatorio.resumo),
                          Spacer(1, 12), Paragraph('Financiamentos', estilos['Heading2'])])
    if relatorio.detalhes.linhas:
        elementos.append(tabela_pdf(relatorio.detalhes))
    else:
        elementos.append(Paragraph('Nenhum registro para os filtros selecionados.', estilos['Normal']))
    doc.build(elementos, onFirstPage=rodape, onLaterPages=rodape)
    Path(caminho).write_bytes(buffer.getvalue())


class AbaRelatorios:
    POR_PAGINA = 20
    ESTILO_ENTRADA = dict(height=40, fg_color=CLARO, border_width=0, font=fonte(13), text_color=TITULO)
    ESTILO_FILTRO = dict(height=40, fg_color=CLARO, text_color=TITULO, button_color='#dfe8fc',
                         button_hover_color='#d3dff5', font=fonte(12), dropdown_font=fonte(12))

    def __init__(self, app):
        self.app = app
        self.opcoes = {}
        self.campos = {}
        self.relatorio = None
        self.pagina = 0
        self.nomes = {nome: tipo for tipo, nome in TIPOS_RELATORIO.items()}

        label(app.body, 'Relatórios', size=28, bold=True, color=TITULO).pack(anchor='w', pady=(8, 14))
        painel = ctk.CTkFrame(app.body, fg_color=BRANCO, corner_radius=12, border_width=1, border_color=BORDA)
        painel.pack(fill='x', pady=(0, 12))
        controles = ctk.CTkFrame(painel, fg_color='transparent')
        controles.pack(fill='x', padx=16, pady=(12, 6))
        label(controles, 'Tipo de relatório', bold=True).pack(side='left', padx=(0, 8))
        self.tipo = ctk.CTkOptionMenu(controles, values=list(self.nomes), width=265, command=self.montar_filtros, **self.ESTILO_FILTRO)
        self.tipo.pack(side='left')
        self.exportar = botao(controles, 'Baixar PDF', self.baixar, kind='secondary', height=40, state='disabled')
        self.exportar.pack(side='right', padx=(8, 0))
        self.gerar = botao(controles, 'Gerar prévia', self.gerar_previa, height=40, state='disabled')
        self.gerar.pack(side='right')
        barra_filtros = ctk.CTkFrame(painel, fg_color='transparent')
        barra_filtros.pack(fill='x', padx=16, pady=(0, 12))
        grupo_busca = ctk.CTkFrame(barra_filtros, fg_color='transparent')
        grupo_busca.pack(side='left', fill='both', expand=True, padx=(0, 12))
        label(grupo_busca, 'Busca', size=12).pack(anchor='w', pady=(0, 4))
        self.busca = ctk.CTkEntry(grupo_busca, placeholder_text='Buscar por nome, título, código ou projeto...',
                                 **self.ESTILO_ENTRADA)
        self.busca.pack(fill='x')
        self.filtros = ctk.CTkFrame(barra_filtros, fg_color='transparent')
        self.filtros.pack(side='right')

        resultado = ctk.CTkFrame(app.body, fg_color=BRANCO, corner_radius=12, border_width=1, border_color=BORDA)
        resultado.pack(fill='both', expand=True, pady=(0, 10))
        barra = ctk.CTkFrame(resultado, fg_color='transparent')
        barra.pack(fill='x', padx=14, pady=(8, 3))
        self.mensagem = label(barra, 'Carregando filtros…', size=12, color=MUTED)
        self.mensagem.pack(side='left')
        self.proxima = botao(barra, 'Próxima', lambda: self.paginar(1), kind='secondary', height=30, state='disabled')
        self.proxima.pack(side='right')
        self.anterior = botao(barra, 'Anterior', lambda: self.paginar(-1), kind='secondary', height=30, state='disabled')
        self.anterior.pack(side='right', padx=(0, 6))
        self.previa = ctk.CTkScrollableFrame(resultado, fg_color=BRANCO)
        self.previa.pack(fill='both', expand=True, padx=10, pady=(0, 8))
        self.busca.bind('<KeyRelease>', self.atualizar_busca)
        for evento in ('<<Paste>>', '<<Cut>>'):
            self.busca.bind(evento, lambda _: self.busca.after_idle(self.atualizar_busca))
        sessao = app.sessao
        app.tarefa(lambda: opcoes_relatorios(sessao), self.carregar_opcoes)

    def carregar_opcoes(self, opcoes):
        self.opcoes = opcoes
        self.montar_filtros(self.tipo.get())
        self.gerar.configure(state='normal')

    def montar_filtros(self, nome):
        for widget in self.filtros.winfo_children():
            widget.destroy()
        for coluna in range(len(self.campos)):
            self.filtros.columnconfigure(coluna, weight=0, uniform='')
        self.campos.clear()
        self.invalidar_previa()
        if not self.opcoes:
            return
        for coluna, campo in enumerate(FILTROS_RELATORIO[self.nomes[nome]]):
            grupo = ctk.CTkFrame(self.filtros, fg_color='transparent')
            self.filtros.columnconfigure(coluna, weight=1, uniform='filtro')
            grupo.grid(row=0, column=coluna, padx=(0, 8), sticky='ew')
            label(grupo, ROTULOS_FILTROS[campo], size=12).pack(anchor='w', pady=(0, 4))
            if campo == 'minimo':
                seletor = ctk.CTkEntry(grupo, width=155, **self.ESTILO_ENTRADA)
                seletor.insert(0, '2')
                seletor.bind('<KeyRelease>', lambda _evento: self.invalidar_previa())
                mapa = None
            else:
                mapa = {'Todos': None}
                mapa.update({rotulo: codigo for codigo, rotulo in self.opcoes[campo]})
                seletor = ctk.CTkOptionMenu(grupo, values=list(mapa), width=175, dynamic_resizing=False,
                                            command=lambda _valor: self.invalidar_previa(), **self.ESTILO_FILTRO)
                seletor.set('Todos')
            seletor.pack(fill='x')
            self.campos[campo] = (seletor, mapa)

    def invalidar_previa(self):
        self.relatorio = None
        self.exportar.configure(state='disabled')
        self.anterior.configure(state='disabled')
        self.proxima.configure(state='disabled')
        self.mensagem.configure(text='Selecione os filtros e gere a prévia.')
        for widget in self.previa.winfo_children():
            widget.destroy()

    def ler_filtros(self):
        filtros = {}
        rotulos = []
        for campo, (seletor, mapa) in self.campos.items():
            valor = seletor.get().strip()
            if mapa is None:
                if not valor.isascii() or not valor.isdecimal() or len(valor) > 10 or int(valor) < 2:
                    raise ValueError('Informe um mínimo de projetos igual ou superior a 2.')
                filtros[campo] = int(valor)
            else:
                filtros[campo] = mapa[valor]
            rotulos.append((ROTULOS_FILTROS[campo], valor))
        return filtros, rotulos

    def gerar_previa(self):
        if self.app.pendente or not self.opcoes:
            return
        try:
            filtros, rotulos = self.ler_filtros()
        except ValueError as erro:
            messagebox.showwarning('Confira os filtros', str(erro), parent=self.app)
            return
        self.invalidar_previa()
        tipo = self.nomes[self.tipo.get()]
        sessao = self.app.sessao

        def exibir(relatorio):
            # O usuário pode editar os filtros enquanto a consulta roda.
            try:
                atuais, _ = self.ler_filtros()
            except ValueError:
                return
            if self.nomes[self.tipo.get()] != tipo or atuais != filtros:
                return
            self.relatorio = relatorio
            self.pagina = 0
            self.desenhar_previa()

        self.app.tarefa(lambda: gerar_relatorio(sessao, tipo, filtros, rotulos), exibir)

    def atualizar_busca(self, *_):
        if self.relatorio is not None:
            self.pagina = 0
            self.desenhar_previa()

    def paginar(self, delta):
        if self.relatorio is not None:
            self.pagina += delta
            self.desenhar_previa()

    def desenhar_previa(self):
        for widget in self.previa.winfo_children():
            widget.destroy()
        relatorio = aplicar_busca(self.relatorio, self.busca.get())
        total = len(relatorio.detalhes.linhas)
        inicio = self.pagina * self.POR_PAGINA
        fim = min(inicio + self.POR_PAGINA, total)
        self.anterior.configure(state='normal' if inicio else 'disabled')
        self.proxima.configure(state='normal' if fim < total else 'disabled')
        self.exportar.configure(state='normal')
        if not total:
            self.mensagem.configure(text='Nenhum registro para a busca e os filtros atuais.')
            return
        self.mensagem.configure(text=f'Exibindo {inicio + 1}–{fim} de {total} registro(s)')
        if relatorio.resumo and relatorio.resumo.linhas:
            label(self.previa, 'Resumo por agência', bold=True).pack(anchor='w', pady=(4, 3))
            self.desenhar_tabela(relatorio.resumo, relatorio.resumo.linhas)
            label(self.previa, 'Financiamentos', bold=True).pack(anchor='w', pady=(8, 3))
        self.desenhar_tabela(relatorio.detalhes, relatorio.detalhes.linhas[inicio:fim])

    def desenhar_tabela(self, tabela, registros):
        grade = ctk.CTkFrame(self.previa, fg_color='transparent')
        grade.pack(fill='x', pady=(0, 6))
        for coluna, peso in enumerate(tabela.pesos):
            grade.columnconfigure(coluna, weight=peso, uniform='coluna')
        for indice, linha in enumerate((tabela.colunas, *registros)):
            for coluna, valor in enumerate(linha):
                cell = label(grade, valor, size=11, bold=indice == 0, anchor='w', justify='left',
                             fg_color=CLARO if indice % 2 == 0 else BRANCO, padx=7, pady=6, wraplength=65)
                cell.grid(row=indice, column=coluna, sticky='nsew', padx=1, pady=1)
                cell.bind('<Configure>', lambda event, w=cell: w.configure(wraplength=max(28, event.width - 17)))

    def baixar(self):
        if self.relatorio is None or self.app.pendente:
            return
        caminho = filedialog.asksaveasfilename(
            parent=self.app, title='Salvar relatório', defaultextension='.pdf',
            initialfile=f"SIGPesq_{self.nomes[self.tipo.get()]}.pdf", filetypes=[('Documento PDF', '*.pdf')],
        )
        if caminho:
            relatorio = aplicar_busca(self.relatorio, self.busca.get())
            self.app.tarefa(
                lambda: salvar_pdf(relatorio, caminho),
                lambda _resultado: messagebox.showinfo('Relatório salvo', f'PDF salvo em:\n{caminho}', parent=self.app),
            )
