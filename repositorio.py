"""Validação e autorização centralizadas; SQL parametrizado e transações."""
from datetime import date
from db import transacao
from modelos import MODELOS
from validacao import validar
from seguranca import ADMIN_LOGIN, autenticar, gerar_hash


CODIGOS_CATEGORIA = {
    campo.nome: {str(codigo): codigo for codigo, _ in campo.opcoes}
    for modelo in MODELOS.values()
    for campo in modelo['campos']
    if campo.tipo == 'opcao'
}


def linhas(cur, sql, params=()):
    cur.execute(sql, params)
    registros = cur.fetchall()
    for registro in registros:
        for campo in registro.keys() & CODIGOS_CATEGORIA.keys():
            valor = registro[campo]
            registro[campo] = CODIGOS_CATEGORIA[campo].get(valor, valor)
    return registros


def identidade(cur,s):
    if not s: raise ValueError('Faça login para continuar.')
    if s.admin: return None
    rows=linhas(cur,'SELECT * FROM participante WHERE cpf=%s AND excluido_em IS NULL',(s.cpf,))
    if len(rows)!=1: raise ValueError('Conta indisponível. Entre novamente.')
    return rows[0]

def ativo(v): return v['data_saida'] is None or v['data_saida']>=date.today()
def gestao(cur, s, projeto=None, *, modulo='projetos'):
    participante = identidade(cur, s)
    if s.admin:
        return True
    if participante['tipo_participante'] != 2:
        return False
    if projeto is None:
        return True
    if modulo not in ('projetos', 'vinculos', 'producoes', 'alocacoes'):
        return False
    vinculos = linhas(
        cur, 'SELECT * FROM vinculo_projeto_participante WHERE cpf=%s AND codigo_projeto=%s AND excluido_em IS NULL',
        (s.cpf, projeto),
    )
    hoje = date.today()
    return any(
        ativo(vinculo)
        and (vinculo['data_entrada'] is None or vinculo['data_entrada'] <= hoje)
        and vinculo['funcao_desempenhada'] == 3
        for vinculo in vinculos
    )

def exigir(cur, s, projeto=None, *, modulo='projetos'):
    if gestao(cur, s, projeto, modulo=modulo):
        return
    if projeto is None:
        raise ValueError('Somente docentes ou o administrador podem cadastrar projetos.')
    if modulo == 'projetos':
        raise ValueError('Somente o administrador ou um docente com vínculo ativo de coordenador pode editar o projeto.')
    raise ValueError('Somente o administrador ou um docente com vínculo ativo de coordenador pode gerenciar estes registros.')

def carregar(modulo,s):
    m=MODELOS[modulo]
    with transacao() as cur:
        identidade(cur,s)
        # Senha nunca é enviada à interface.
        cols=[c.nome for c in m['campos'] if c.nome!='senha']
        rows=linhas(cur,f"SELECT {','.join(cols)} FROM {m['tabela']} WHERE excluido_em IS NULL")
        projetos=linhas(cur,'SELECT codigo_projeto,titulo FROM projeto WHERE excluido_em IS NULL')
        participantes = linhas(cur, """
            SELECT cpf, nome, tipo_participante FROM participante
            WHERE excluido_em IS NULL ORDER BY nome, cpf
        """)
        opcoes={'projeto':[(r['codigo_projeto'],f"{r['codigo_projeto']} · {r['titulo']}") for r in projetos],
                'participante':[(r['cpf'],r['nome']) for r in participantes],
                'financiamento':[(r['codigo_financiamento'],str(r['codigo_financiamento'])) for r in linhas(cur,'SELECT codigo_financiamento FROM financiamento WHERE excluido_em IS NULL')]}
        # Dados derivados para a consulta visual; nenhuma coluna nova no banco.
        docentes = {p['cpf']: p['nome'] for p in participantes if p['tipo_participante'] == 2}
        if modulo == 'projetos' and s.admin:
            opcoes['coordenador'] = list(docentes.items())
        titulos={p['codigo_projeto']:p['titulo'] for p in projetos}
        if modulo in ('projetos','participantes'):
            vinculos=linhas(cur,'SELECT codigo_projeto,cpf,funcao_desempenhada FROM vinculo_projeto_participante WHERE excluido_em IS NULL')
            from modelos import FUNCOES
            funcoes=dict(FUNCOES)
            for r in rows:
                if modulo=='projetos':
                    r['coordenacao'] = ', '.join(
                        docentes[v['cpf']] for v in vinculos
                        if v['codigo_projeto'] == r['codigo_projeto']
                        and v['funcao_desempenhada'] == 3 and v['cpf'] in docentes
                    )
                else:
                    r['equipes']='; '.join(titulos[v['codigo_projeto']]+' / '+funcoes.get(v['funcao_desempenhada'],'Sem função') for v in vinculos if v['cpf']==r['cpf'] and v['codigo_projeto'] in titulos)
        if modulo=='financiamentos':
            destinos=linhas(cur,'SELECT codigo_projeto,codigo_financiamento FROM vinculo_projeto_financiamento WHERE excluido_em IS NULL')
            for r in rows:
                r['projetos_apoiados']=', '.join(titulos[v['codigo_projeto']] for v in destinos if v['codigo_financiamento']==r['codigo_financiamento'] and v['codigo_projeto'] in titulos)
        if modulo=='producoes':
            equipes = linhas(cur, """
                SELECT v.codigo_projeto, v.cpf, p.nome
                FROM vinculo_projeto_participante v
                JOIN participante p ON p.cpf = v.cpf
                WHERE v.excluido_em IS NULL AND p.excluido_em IS NULL
                ORDER BY p.nome, v.cpf
            """)
            opcoes['autores_por_projeto']={}
            for v in equipes:
                opcoes['autores_por_projeto'].setdefault(v['codigo_projeto'],[]).append((v['cpf'],v['nome']))
            autorias=linhas(cur,'SELECT a.codigo_projeto,a.codigo_prod,a.cpf,p.nome FROM autoria_producao a JOIN participante p ON p.cpf=a.cpf ORDER BY p.nome,a.cpf')
            for r in rows:
                autores=[a for a in autorias if (a['codigo_projeto'],a['codigo_prod'])==(r['codigo_projeto'],r['codigo_prod'])]
                r['autores']=[(a['cpf'], a['nome']) for a in autores]
                r['nomes_autores']='; '.join(a['nome'] for a in autores)
        return rows,opcoes

def _validar(m,dados):
    # Relações usam identificadores tipados, inclusive em chamadas fora da tela.
    d=validar(m['campos'],dados)
    for c in m['campos']:
        if c.tipo in ('projeto','financiamento'):
            if type(d[c.nome]) is not int or not 1<=d[c.nome]<=4294967295: raise ValueError('Selecione um registro válido.')
        elif c.tipo=='participante':
            from validacao import cpf_limpo
            d[c.nome]=cpf_limpo(str(d[c.nome]))
    if 'email' in d: d['email']=d['email'].lower()
    return d

def _exigir_docente(cur, cpf):
    if not linhas(cur, """
        SELECT cpf FROM participante
        WHERE cpf = %s AND tipo_participante = '2' AND excluido_em IS NULL
    """, (cpf,)):
        raise ValueError('Somente docentes podem exercer a função de coordenador.')


def salvar(modulo, dados, s=None, chave=None, cadastro=False, *, senha_admin=None):
    m=MODELOS[modulo]; d=_validar(m,dados)
    autores=validar_autores(dados.get('autores')) if modulo=='producoes' else []
    if modulo == 'projetos':
        # A descrição é opcional, mas a coluna no banco não aceita NULL.
        d['descricao'] = d['descricao'] or ''
    if cadastro:
        if modulo != 'participantes' or chave is not None:
            raise ValueError('O cadastro inicial serve apenas para criar participantes.')
        if d['tipo_participante'] != 1:
            try:
                autenticar(ADMIN_LOGIN, senha_admin or '')
            except ValueError as erro:
                raise ValueError('Docentes e técnicos precisam da autorização do administrador.') from erro
    pk=m['pk']; key=tuple(d[k] for k in pk)
    if chave is not None and key!=tuple(chave): raise ValueError('A chave do registro não pode ser alterada.')
    with transacao() as cur:
        # Todas as escritas da aplicação usam o mesmo lock transacional, já que
        # referências e unicidade de e-mail também são verificadas na aplicação.
        cur.execute("SELECT GET_LOCK('sigpesq_escrita',10) AS ok")
        if cur.fetchone()['ok']!=1: raise ValueError('Banco ocupado. Tente novamente.')
        try:
            coordenador = None
            if not cadastro:
                identidade(cur,s)
                if modulo=='participantes':
                    if not s.admin:
                        if chave is None or d['cpf']!=s.cpf: raise ValueError('Somente o administrador cadastra ou altera outras contas.')
                        atual=identidade(cur,s)
                        if d['tipo_participante']!=atual['tipo_participante']: raise ValueError('Somente o administrador altera o tipo da conta.')
                elif modulo=='financiamentos':
                    if not s.admin: raise ValueError('Somente o administrador gerencia contratos de financiamento.')
                else:
                    projeto = None if modulo == 'projetos' and chave is None else d['codigo_projeto']
                    exigir(cur, s, projeto, modulo=modulo)
                    if modulo == 'projetos' and chave is None:
                        coordenador = dados.get('coordenador') if s.admin else s.cpf
                        if coordenador:
                            _exigir_docente(cur, coordenador)
            where=' AND '.join(k+'=%s' for k in pk)
            existentes = linhas(cur, f"SELECT excluido_em FROM {m['tabela']} WHERE {where}", key)
            oculto = bool(existentes and existentes[0]['excluido_em'] is not None)
            reativar = chave is None and oculto and modulo in ('vinculos', 'alocacoes')
            if chave is None and existentes and not reativar:
                if modulo == 'participantes':
                    raise ValueError('CPF já cadastrado.')
                raise ValueError('Código ou vínculo já cadastrado.')
            if chave is not None and (not existentes or oculto):
                raise ValueError('Registro indisponível.')
            if modulo=='participantes':
                if d['email']==ADMIN_LOGIN or d['cpf']==ADMIN_LOGIN: raise ValueError('Login reservado ao administrador.')
                if chave is not None and d['tipo_participante'] != 2 and linhas(cur, """
                    SELECT v.codigo_projeto FROM vinculo_projeto_participante v
                    JOIN participante p ON p.cpf = v.cpf
                    WHERE v.cpf = %s AND v.funcao_desempenhada = '3'
                      AND v.excluido_em IS NULL AND p.tipo_participante <> %s
                    LIMIT 1
                """, (d['cpf'], str(d['tipo_participante']))):
                    raise ValueError('Altere a função de coordenador na equipe antes de mudar o tipo do participante.')
                if linhas(cur,'SELECT cpf FROM participante WHERE LOWER(email)=%s AND cpf<>%s',(d['email'],d['cpf'])): raise ValueError('E-mail já cadastrado.')
                if d['senha']: d['senha']=gerar_hash(d['senha'])
                elif chave is None: raise ValueError('Informe uma senha de 8 a 128 caracteres.')
                else: del d['senha']
            for campo,tabela,col in [('codigo_projeto','projeto','codigo_projeto'),('cpf','participante','cpf'),('codigo_financiamento','financiamento','codigo_financiamento')]:
                if campo in d and m['tabela']!=tabela:
                    if not linhas(cur,f'SELECT {col} FROM {tabela} WHERE {col}=%s AND excluido_em IS NULL',(d[campo],)): raise ValueError('O registro relacionado não existe.')
            if modulo == 'producoes':
                atuais = {
                    r['cpf'] for r in linhas(
                        cur, 'SELECT cpf FROM autoria_producao WHERE codigo_projeto=%s AND codigo_prod=%s', key,
                    )
                }
                equipe = {
                    r['cpf'] for r in linhas(cur, """
                        SELECT v.cpf FROM vinculo_projeto_participante v
                        JOIN participante p ON p.cpf = v.cpf
                        WHERE v.codigo_projeto = %s
                          AND v.excluido_em IS NULL AND p.excluido_em IS NULL
                    """, (d['codigo_projeto'],))
                }
                if set(autores).difference(atuais, equipe):
                    raise ValueError('Novos autores precisam ter um cadastro e um vínculo visíveis no projeto.')
            if modulo=='alocacoes':
                outra_destinacao = linhas(cur, """
                    SELECT codigo_financiamento
                    FROM vinculo_projeto_financiamento
                    WHERE codigo_projeto = %s AND codigo_financiamento <> %s
                      AND excluido_em IS NULL
                """, (d['codigo_projeto'], d['codigo_financiamento']))
                if outra_destinacao:
                    raise ValueError('O projeto já possui uma destinação de financiamento.')
                contrato=linhas(cur,'SELECT valor_total FROM financiamento WHERE codigo_financiamento=%s',(d['codigo_financiamento'],))[0]
                soma=sum(r['valor_destinado'] for r in linhas(cur,'SELECT valor_destinado FROM vinculo_projeto_financiamento WHERE codigo_financiamento=%s AND codigo_projeto<>%s AND excluido_em IS NULL',(d['codigo_financiamento'],d['codigo_projeto'])))
                if soma+d['valor_destinado']>contrato['valor_total']: raise ValueError('Destinação excede o valor disponível do contrato.')
            if modulo=='financiamentos' and chave:
                soma=sum(r['valor_destinado'] for r in linhas(cur,'SELECT valor_destinado FROM vinculo_projeto_financiamento WHERE codigo_financiamento=%s AND excluido_em IS NULL',key))
                if soma>d['valor_total']: raise ValueError('Valor inferior ao total já destinado.')

            if (
                modulo == 'vinculos'
                and d['funcao_desempenhada'] == 3
            ):
                _exigir_docente(cur, d['cpf'])
                coordenadores = linhas(
                    cur,
                    '''
                    SELECT cpf
                    FROM vinculo_projeto_participante
                    WHERE codigo_projeto = %s
                      AND funcao_desempenhada = '3'
                      AND excluido_em IS NULL
                      AND cpf <> %s
                    ''',
                    (d['codigo_projeto'], d['cpf'])
                )

                if coordenadores:
                    raise ValueError(
                        'Este projeto já possui um coordenador. '
                        'Altere a função do coordenador atual antes '
                        'de definir outro.'
                    )
                
            valores_sql = {
                campo: str(valor) if campo in CODIGOS_CATEGORIA else valor
                for campo, valor in d.items()
            }
            cols = list(valores_sql)
            if chave is None and not reativar:
                placeholders = ','.join(['%s'] * len(cols))
                cur.execute(
                    f"INSERT INTO {m['tabela']} ({','.join(cols)}) VALUES ({placeholders})",
                    tuple(valores_sql.values()),
                )
                if coordenador:
                    cur.execute(
                        'INSERT INTO vinculo_projeto_participante '
                        '(codigo_projeto,cpf,funcao_desempenhada,data_entrada) VALUES (%s,%s,%s,%s)',
                        (d['codigo_projeto'], coordenador, '3', d['data_inicio']),
                    )
            else:
                cols = [campo for campo in cols if campo not in pk]
                atribuicoes = ','.join(f'{campo}=%s' for campo in cols)
                if reativar:
                    atribuicoes += ',excluido_em=NULL'
                cur.execute(
                    f"UPDATE {m['tabela']} SET {atribuicoes} WHERE {where}",
                    tuple(valores_sql[campo] for campo in cols) + key,
                )
            if modulo == 'producoes':
                # A edição explícita da lista pode retirar uma assinatura.
                # Ocultar cadastros ou vínculos preserva as autorias.
                for cpf in autores:
                    if cpf not in atuais:
                        cur.execute(
                            'INSERT INTO autoria_producao (codigo_projeto,codigo_prod,cpf) VALUES (%s,%s,%s)',
                            key + (cpf,),
                        )
                for cpf in atuais.difference(autores):
                    cur.execute(
                        'DELETE FROM autoria_producao WHERE codigo_projeto=%s AND codigo_prod=%s AND cpf=%s',
                        key + (cpf,),
                    )
            # Libera somente após commit, evitando corrida na verificação de e-mail.
            cur.execute('COMMIT')
        except Exception:
            cur.execute('ROLLBACK')
            raise
        finally:
            cur.execute("SELECT RELEASE_LOCK('sigpesq_escrita')")
            cur.fetchall()

def _impedir_exclusao_com_contrato_ativo(cur, modulo, chave):
    origem = 'financiamento f'
    if modulo == 'financiamentos':
        filtro = 'f.codigo_financiamento = %s'
    elif modulo in ('projetos', 'alocacoes'):
        origem += """
            JOIN vinculo_projeto_financiamento v
              ON v.codigo_financiamento = f.codigo_financiamento
        """
        filtro = 'v.codigo_projeto = %s AND v.excluido_em IS NULL'
        if modulo == 'alocacoes':
            filtro += ' AND v.codigo_financiamento = %s'
    else:
        return

    contratos = linhas(cur, f"""
        SELECT f.codigo_financiamento
        FROM {origem}
        WHERE {filtro} AND f.excluido_em IS NULL
          AND %s BETWEEN f.data_inicio AND f.data_termino
        ORDER BY f.codigo_financiamento
        LIMIT 1
    """, (*chave, date.today()))
    if contratos:
        codigo = contratos[0]['codigo_financiamento']
        if modulo == 'projetos':
            raise ValueError(f'O projeto está vinculado ao contrato de financiamento ativo {codigo}.')
        raise ValueError(f'O contrato de financiamento {codigo} está ativo. A exclusão só é permitida fora da vigência.')


def excluir(modulo, chave, s):
    if not s or not s.admin:
        raise ValueError('Somente o administrador pode excluir registros.')
    modelo = MODELOS[modulo]
    dependentes = {
        'projetos': (
            ('producao_cientifica', 'codigo_projeto'),
            ('vinculo_projeto_participante', 'codigo_projeto'),
            ('vinculo_projeto_financiamento', 'codigo_projeto'),
        ),
        'participantes': (('vinculo_projeto_participante', 'cpf'),),
        'financiamentos': (('vinculo_projeto_financiamento', 'codigo_financiamento'),),
    }
    with transacao() as cur:
        cur.execute("SELECT GET_LOCK('sigpesq_escrita',10) AS ok")
        if cur.fetchone()['ok'] != 1:
            raise ValueError('Banco ocupado.')
        try:
            _impedir_exclusao_com_contrato_ativo(cur, modulo, chave)
            where = ' AND '.join(f'{coluna}=%s' for coluna in modelo['pk'])
            cur.execute(
                f"UPDATE {modelo['tabela']} SET excluido_em = CURRENT_TIMESTAMP "
                f"WHERE {where} AND excluido_em IS NULL",
                chave,
            )
            if cur.rowcount:
                for tabela, coluna in dependentes.get(modulo, ()):
                    cur.execute(
                        f"UPDATE {tabela} SET excluido_em = CURRENT_TIMESTAMP "
                        f"WHERE {coluna} = %s AND excluido_em IS NULL",
                        chave,
                    )
            cur.execute('COMMIT')
        except Exception:
            cur.execute('ROLLBACK')
            raise
        finally:
            cur.execute("SELECT RELEASE_LOCK('sigpesq_escrita')")
            cur.fetchall()


def validar_autores(valores):
    from validacao import cpf_limpo
    if not isinstance(valores,(list,tuple)) or not valores:
        raise ValueError('Selecione pelo menos um autor para a produção científica.')
    return list(dict.fromkeys(cpf_limpo(str(cpf)) for cpf in valores))
