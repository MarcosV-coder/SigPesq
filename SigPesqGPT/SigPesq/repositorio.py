"""SQL explícito, parâmetros %s e regras atômicas de relacionamentos."""
from decimal import Decimal
from db import consultar, transacao
from telas.modelos import MODELOS

SELECTS = {
'projetos': """SELECT p.*,
 (SELECT GROUP_CONCAT(a.nome SEPARATOR ', ') FROM vinculo_projeto_participante v
 JOIN participante a ON a.cpf=v.cpf WHERE v.codigo_projeto=p.codigo_projeto
 AND v.funcao_desempenhada='coordenador') AS coordenacao,
 (SELECT MIN(v.cpf) FROM vinculo_projeto_participante v WHERE v.codigo_projeto=p.codigo_projeto
 AND v.funcao_desempenhada='coordenador') AS coordenador,
 (SELECT GROUP_CONCAT(CONCAT(a.nome,' ',a.cpf) SEPARATOR ' ') FROM vinculo_projeto_participante v
 JOIN participante a ON a.cpf=v.cpf WHERE v.codigo_projeto=p.codigo_projeto) AS busca_equipe
 FROM projeto p ORDER BY p.codigo_projeto DESC""",
'participantes': """SELECT a.*,
 (SELECT GROUP_CONCAT(CONCAT(p.titulo,' / ',COALESCE(v.funcao_desempenhada,''),
 ' / ',COALESCE(DATE_FORMAT(v.data_entrada,'%d/%m/%Y'),'—'),' a ',
 COALESCE(DATE_FORMAT(v.data_saida,'%d/%m/%Y'),'sem término')) SEPARATOR ' | ')
 FROM vinculo_projeto_participante v JOIN projeto p ON p.codigo_projeto=v.codigo_projeto
 WHERE v.cpf=a.cpf) AS projetos FROM participante a ORDER BY a.nome""",
'financiamentos': """SELECT f.*,
 (SELECT GROUP_CONCAT(p.titulo SEPARATOR ' | ') FROM vinculo_projeto_financiamento v
 JOIN projeto p ON p.codigo_projeto=v.codigo_projeto
 WHERE v.codigo_financiamento=f.codigo_financiamento) AS projetos
 FROM financiamento f ORDER BY f.codigo_financiamento DESC""",
'producoes': """SELECT c.*, p.titulo AS projeto_titulo,
 (SELECT GROUP_CONCAT(a.nome SEPARATOR ', ') FROM autoria_producao ap
 JOIN participante a ON a.cpf=ap.cpf WHERE ap.codigo_projeto=c.codigo_projeto AND ap.codigo_prod=c.codigo_prod) AS autores_nomes
 FROM producao_cientifica c JOIN projeto p ON p.codigo_projeto=c.codigo_projeto
 ORDER BY c.ano_publicacao DESC, c.codigo_projeto, c.codigo_prod""",
'vinculos': """SELECT v.*, p.titulo AS projeto_titulo, a.nome AS participante_nome, a.email
 FROM vinculo_projeto_participante v JOIN projeto p ON p.codigo_projeto=v.codigo_projeto
 JOIN participante a ON a.cpf=v.cpf ORDER BY p.titulo,a.nome""",
'alocacoes': """SELECT v.*, p.titulo AS projeto_titulo, f.agencia_financiadora
 FROM vinculo_projeto_financiamento v JOIN projeto p ON p.codigo_projeto=v.codigo_projeto
 JOIN financiamento f ON f.codigo_financiamento=v.codigo_financiamento ORDER BY p.titulo"""
}


def carregar(modulo):
    with transacao() as cur:
        def fetch(sql):
            cur.execute(sql)
            return cur.fetchall()
        registros = fetch(SELECTS[modulo])
        opcoes = {
            'projeto': [(r['codigo_projeto'], f"{r['codigo_projeto']} · {r['titulo']}") for r in fetch('SELECT codigo_projeto,titulo FROM projeto ORDER BY titulo')],
            'participante': [(r['cpf'], f"{r['nome']} · {r['cpf']}") for r in fetch('SELECT cpf,nome FROM participante ORDER BY nome')],
            'docente': [(r['cpf'], r['nome']+' · '+r['cpf']) for r in fetch("SELECT cpf,nome FROM participante WHERE tipo_participante='docente' ORDER BY nome")],
            'financiamento': [(r['codigo_financiamento'], f"{r['codigo_financiamento']} · {r['agencia_financiadora'].upper()} · {r['valor_total']}") for r in fetch('SELECT codigo_financiamento,agencia_financiadora,valor_total FROM financiamento ORDER BY codigo_financiamento')],
        }
        autores = fetch("""SELECT v.codigo_projeto,v.cpf,a.nome FROM vinculo_projeto_participante v
                           JOIN participante a ON a.cpf=v.cpf ORDER BY a.nome""")
        autoria = fetch('SELECT codigo_projeto,codigo_prod,cpf FROM autoria_producao')
        for r in registros:
            if modulo == 'producoes':
                r['autores'] = [a['cpf'] for a in autoria if (a['codigo_projeto'],a['codigo_prod']) == (r['codigo_projeto'],r['codigo_prod'])]
        return registros, opcoes, autores


def _projeto_lock(cur, codigo):
    cur.execute('SELECT codigo_projeto FROM projeto WHERE codigo_projeto=%s FOR UPDATE', (codigo,))
    if not cur.fetchone():
        raise ValueError('Projeto não encontrado. Atualize a lista.')


def _docente(cur, cpf):
    cur.execute('SELECT tipo_participante FROM participante WHERE cpf=%s FOR UPDATE', (cpf,))
    r = cur.fetchone()
    if not r or r['tipo_participante'] != 'docente':
        raise ValueError('O coordenador deve ser um docente cadastrado.')


def salvar(modulo, dados, chave=None):
    m = MODELOS[modulo]
    # Campos de relacionamento não pertencem à tabela principal.
    extras = {'coordenador','projeto','funcao','inicio','fim','autores'}
    cols = [c.nome for c in m['campos'] if c.nome not in extras]
    valores = {c: dados[c] for c in cols}
    with transacao() as cur:
        if chave is not None:
            where = ' AND '.join(f'{k}=%s' for k in m['pk'])
            cur.execute(f"SELECT * FROM {m['tabela']} WHERE {where} FOR UPDATE", chave)
            if cur.fetchone() is None:
                raise ValueError('Registro excluído por outra sessão. Atualize a lista.')
            if tuple(dados[k] for k in m['pk']) != tuple(chave):
                raise ValueError('A chave não pode ser alterada durante a edição.')
        if modulo == 'participantes' and dados['tipo_participante'] != 'docente':
            cur.execute("SELECT 1 FROM vinculo_projeto_participante WHERE cpf=%s AND funcao_desempenhada='coordenador' LIMIT 1", (dados['cpf'],))
            if cur.fetchone():
                raise ValueError('Este participante coordena projetos; mantenha o tipo Docente ou altere os vínculos primeiro.')
        if modulo == 'vinculos':
            _projeto_lock(cur, dados['codigo_projeto'])
            if dados['funcao_desempenhada'] == 'coordenador':
                _docente(cur, dados['cpf'])
                cur.execute("""SELECT cpf FROM vinculo_projeto_participante
                    WHERE codigo_projeto=%s AND funcao_desempenhada='coordenador' AND cpf<>%s""",
                    (dados['codigo_projeto'],dados['cpf']))
                if cur.fetchone():
                    raise ValueError('O projeto já possui coordenador. Altere-o na tela Projetos.')
        if modulo == 'alocacoes':
            # Serializa destinações por contrato, evitando excesso concorrente.
            cur.execute('SELECT valor_total FROM financiamento WHERE codigo_financiamento=%s FOR UPDATE', (dados['codigo_financiamento'],))
            contrato = cur.fetchone()
            if not contrato:
                raise ValueError('Financiamento não encontrado.')
            cur.execute("""SELECT COALESCE(SUM(valor_destinado),0) AS total
                FROM vinculo_projeto_financiamento WHERE codigo_financiamento=%s AND codigo_projeto<>%s""",
                (dados['codigo_financiamento'],dados['codigo_projeto']))
            if cur.fetchone()['total'] + dados['valor_destinado'] > contrato['valor_total']:
                raise ValueError('A soma destinada aos projetos ultrapassa o valor total do financiamento.')
        if modulo == 'financiamentos' and chave:
            cur.execute('SELECT COALESCE(SUM(valor_destinado),0) AS total FROM vinculo_projeto_financiamento WHERE codigo_financiamento=%s',chave)
            if dados['valor_total'] < cur.fetchone()['total']:
                raise ValueError('O valor total não pode ser inferior aos recursos já destinados.')
        if modulo == 'producoes':
            _projeto_lock(cur,dados['codigo_projeto'])
            for cpf in dados['autores']:
                cur.execute('SELECT 1 FROM vinculo_projeto_participante WHERE codigo_projeto=%s AND cpf=%s', (dados['codigo_projeto'],cpf))
                if not cur.fetchone():
                    raise ValueError('Todos os autores devem estar vinculados ao projeto.')
        if chave is None:
            cur.execute(f"INSERT INTO {m['tabela']} ({','.join(cols)}) VALUES ({','.join(['%s']*len(cols))})", tuple(valores.values()))
        else:
            cols_edit = [c for c in cols if c not in m['pk']]
            cur.execute(f"UPDATE {m['tabela']} SET {','.join(c+'=%s' for c in cols_edit)} WHERE "+' AND '.join(k+'=%s' for k in m['pk']),
                        tuple(valores[c] for c in cols_edit)+tuple(chave))
        if modulo == 'projetos':
            _projeto_lock(cur,dados['codigo_projeto'])
            _docente(cur,dados['coordenador'])
            # Um coordenador atual por projeto; antigos coordenadores viram colaboradores.
            cur.execute("""UPDATE vinculo_projeto_participante SET funcao_desempenhada='colaborador'
                WHERE codigo_projeto=%s AND funcao_desempenhada='coordenador' AND cpf<>%s""",
                (dados['codigo_projeto'],dados['coordenador']))
            cur.execute("""INSERT INTO vinculo_projeto_participante
                (codigo_projeto,cpf,funcao_desempenhada,data_entrada,data_saida)
                VALUES (%s,%s,'coordenador',%s,%s)
                ON DUPLICATE KEY UPDATE funcao_desempenhada='coordenador'""",
                (dados['codigo_projeto'],dados['coordenador'],dados['data_inicio'],dados['data_termino']))
        if modulo == 'participantes' and chave is None and dados.get('projeto'):
            _projeto_lock(cur,dados['projeto'])
            if dados['funcao'] == 'coordenador':
                _docente(cur,dados['cpf'])
                cur.execute("SELECT 1 FROM vinculo_projeto_participante WHERE codigo_projeto=%s AND funcao_desempenhada='coordenador'", (dados['projeto'],))
                if cur.fetchone():
                    raise ValueError('Projeto já possui coordenador. Use a tela Projetos para substituí-lo.')
            cur.execute("""INSERT INTO vinculo_projeto_participante
                (codigo_projeto,cpf,funcao_desempenhada,data_entrada,data_saida) VALUES (%s,%s,%s,%s,%s)""",
                (dados['projeto'],dados['cpf'],dados['funcao'],dados['inicio'],dados['fim']))
        if modulo == 'producoes':
            key = (dados['codigo_projeto'],dados['codigo_prod'])
            cur.execute('DELETE FROM autoria_producao WHERE codigo_projeto=%s AND codigo_prod=%s',key)
            for cpf in set(dados['autores']):
                cur.execute('INSERT INTO autoria_producao (codigo_projeto,codigo_prod,cpf) VALUES (%s,%s,%s)',key+(cpf,))


def excluir(modulo, chave):
    m = MODELOS[modulo]
    with transacao() as cur:
        cur.execute(f"DELETE FROM {m['tabela']} WHERE "+' AND '.join(k+'=%s' for k in m['pk']),chave)
        if cur.rowcount == 0:
            raise ValueError('Registro não encontrado. Atualize a lista.')


def indicadores():
    return consultar("""SELECT
        (SELECT COUNT(*) FROM projeto WHERE situacao='em_andamento') AS projetos,
        (SELECT COUNT(*) FROM participante) AS participantes,
        (SELECT COALESCE(SUM(valor_total),0) FROM financiamento) AS financiamentos,
        (SELECT COUNT(*) FROM producao_cientifica) AS producoes,
        (SELECT COUNT(*) FROM vinculo_projeto_participante) AS vinculos""")[0]
