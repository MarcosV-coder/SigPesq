"""Validação e autorização centralizadas; SQL parametrizado e transações."""
from datetime import date
from db import transacao
from modelos import MODELOS
from validacao import validar
from seguranca import gerar_hash

def linhas(cur,sql,params=()):
    cur.execute(sql,params)
    return cur.fetchall()

def identidade(cur,s):
    if not s: raise ValueError('Faça login para continuar.')
    if s.admin: return None
    rows=linhas(cur,'SELECT * FROM participante WHERE cpf=%s',(s.cpf,))
    if len(rows)!=1: raise ValueError('Conta não encontrada. Entre novamente.')
    return rows[0]

def ativo(v): return v['data_saida'] is None or v['data_saida']>=date.today()
def gestao(cur,s,projeto=None):
    a=identidade(cur,s)
    if s.admin: return True
    vs=linhas(cur,'SELECT * FROM vinculo_projeto_participante WHERE cpf=%s',(s.cpf,))
    if projeto is None:
        return a['tipo_participante']==2
    return any(v['codigo_projeto']==projeto and ativo(v) and (v['data_entrada'] is None or v['data_entrada']<=date.today()) and (a['tipo_participante']==3 or v['funcao_desempenhada']==3) for v in vs)

def exigir(cur,s,projeto=None):
    if not gestao(cur,s,projeto):
        if projeto is None: raise ValueError('Somente docentes ou o administrador podem cadastrar projetos.')
        raise ValueError('Apenas coordenadores ou técnicos vinculados e ativos podem alterar este projeto.')

def carregar(modulo,s):
    m=MODELOS[modulo]
    with transacao() as cur:
        identidade(cur,s)
        # Senha nunca é enviada à interface.
        cols=[c.nome for c in m['campos'] if c.nome!='senha']
        rows=linhas(cur,f"SELECT {','.join(cols)} FROM {m['tabela']}")
        projetos=linhas(cur,'SELECT codigo_projeto,titulo FROM projeto')
        opcoes={'projeto':[(r['codigo_projeto'],f"{r['codigo_projeto']} · {r['titulo']}") for r in projetos],
                'participante':[(r['cpf'],r['nome']) for r in linhas(cur,'SELECT cpf,nome FROM participante ORDER BY nome,cpf')],
                'financiamento':[(r['codigo_financiamento'],str(r['codigo_financiamento'])) for r in linhas(cur,'SELECT codigo_financiamento FROM financiamento')]}
        # Dados derivados para a consulta visual; nenhuma coluna nova no banco.
        nomes=dict(opcoes['participante'])
        titulos={p['codigo_projeto']:p['titulo'] for p in projetos}
        if modulo in ('projetos','participantes'):
            vinculos=linhas(cur,'SELECT codigo_projeto,cpf,funcao_desempenhada FROM vinculo_projeto_participante')
            from modelos import FUNCOES
            funcoes=dict(FUNCOES)
            for r in rows:
                if modulo=='projetos':
                    r['coordenacao']=', '.join(nomes.get(v['cpf'],'Participante indisponível') for v in vinculos if v['codigo_projeto']==r['codigo_projeto'] and v['funcao_desempenhada']==3)
                else:
                    r['equipes']='; '.join(titulos[v['codigo_projeto']]+' / '+funcoes.get(v['funcao_desempenhada'],'Sem função') for v in vinculos if v['cpf']==r['cpf'] and v['codigo_projeto'] in titulos)
        if modulo=='financiamentos':
            destinos=linhas(cur,'SELECT codigo_projeto,codigo_financiamento FROM vinculo_projeto_financiamento')
            for r in rows:
                r['projetos_apoiados']=', '.join(titulos[v['codigo_projeto']] for v in destinos if v['codigo_financiamento']==r['codigo_financiamento'] and v['codigo_projeto'] in titulos)
        if modulo=='producoes':
            equipes=linhas(cur,'SELECT v.codigo_projeto,v.cpf,p.nome FROM vinculo_projeto_participante v JOIN participante p ON p.cpf=v.cpf ORDER BY p.nome,v.cpf')
            opcoes['autores_por_projeto']={}
            for v in equipes:
                opcoes['autores_por_projeto'].setdefault(v['codigo_projeto'],[]).append((v['cpf'],v['nome']))
            autorias=linhas(cur,'SELECT a.codigo_projeto,a.codigo_prod,a.cpf,p.nome FROM autoria_producao a JOIN participante p ON p.cpf=a.cpf ORDER BY p.nome,a.cpf')
            for r in rows:
                autores=[a for a in autorias if (a['codigo_projeto'],a['codigo_prod'])==(r['codigo_projeto'],r['codigo_prod'])]
                r['autores']=[a['cpf'] for a in autores]
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

def salvar(modulo,dados,s=None,chave=None,cadastro=False):
    m=MODELOS[modulo]; d=_validar(m,dados)
    autores=validar_autores(dados.get('autores')) if modulo=='producoes' else []
    pk=m['pk']; key=tuple(d[k] for k in pk)
    if chave is not None and key!=tuple(chave): raise ValueError('A chave do registro não pode ser alterada.')
    with transacao() as cur:
        # Todas as escritas da aplicação usam o mesmo lock transacional, já que
        # referências e unicidade de e-mail também são verificadas na aplicação.
        cur.execute("SELECT GET_LOCK('sigpesq_escrita',10) AS ok")
        if cur.fetchone()['ok']!=1: raise ValueError('Banco ocupado. Tente novamente.')
        try:
            if cadastro:
                if modulo!='participantes' or chave is not None or d['tipo_participante']!=1: raise ValueError('Cadastro opcional cria somente conta discente. Docentes e técnicos são definidos pelo administrador.')
            else:
                identidade(cur,s)
                if modulo=='participantes':
                    if not s.admin:
                        if chave is None or d['cpf']!=s.cpf: raise ValueError('Somente o administrador cadastra ou altera outras contas.')
                        atual=identidade(cur,s)
                        if d['tipo_participante']!=atual['tipo_participante']: raise ValueError('Somente o administrador altera o tipo da conta.')
                elif modulo=='financiamentos':
                    if not s.admin: raise ValueError('Somente o administrador gerencia contratos de financiamento.')
                else: exigir(cur,s,None if modulo=='projetos' and chave is None else d['codigo_projeto'])
            where=' AND '.join(k+'=%s' for k in pk)
            existente=linhas(cur,f"SELECT {','.join(pk)} FROM {m['tabela']} WHERE {where}",key)
            if chave is None and existente: raise ValueError('Código, CPF ou vínculo já cadastrado.')
            if chave is not None and not existente: raise ValueError('Registro não encontrado.')
            if modulo=='participantes':
                from seguranca import ADMIN_LOGIN
                admin_login=ADMIN_LOGIN
                if d['email']==admin_login or d['cpf']==admin_login: raise ValueError('Login reservado ao administrador.')
                if linhas(cur,'SELECT cpf FROM participante WHERE LOWER(email)=%s AND cpf<>%s',(d['email'],d['cpf'])): raise ValueError('E-mail já cadastrado.')
                if d['senha']: d['senha']=gerar_hash(d['senha'])
                elif chave is None: raise ValueError('Informe uma senha de 8 a 128 caracteres.')
                else: del d['senha']
            for campo,tabela,col in [('codigo_projeto','projeto','codigo_projeto'),('cpf','participante','cpf'),('codigo_financiamento','financiamento','codigo_financiamento')]:
                if campo in d and m['tabela']!=tabela:
                    if not linhas(cur,f'SELECT {col} FROM {tabela} WHERE {col}=%s',(d[campo],)): raise ValueError('O registro relacionado não existe.')
            if modulo=='producoes':
                equipe={r['cpf'] for r in linhas(cur,'SELECT cpf FROM vinculo_projeto_participante WHERE codigo_projeto=%s',(d['codigo_projeto'],))}
                if not set(autores)<=equipe:
                    raise ValueError('Todos os autores devem estar vinculados ao projeto da produção.')
            if modulo=='alocacoes':
                contrato=linhas(cur,'SELECT valor_total FROM financiamento WHERE codigo_financiamento=%s',(d['codigo_financiamento'],))[0]
                soma=sum(r['valor_destinado'] for r in linhas(cur,'SELECT valor_destinado FROM vinculo_projeto_financiamento WHERE codigo_financiamento=%s AND codigo_projeto<>%s',(d['codigo_financiamento'],d['codigo_projeto'])))
                if soma+d['valor_destinado']>contrato['valor_total']: raise ValueError('Destinação excede o valor disponível do contrato.')
            if modulo=='financiamentos' and chave:
                soma=sum(r['valor_destinado'] for r in linhas(cur,'SELECT valor_destinado FROM vinculo_projeto_financiamento WHERE codigo_financiamento=%s',key))
                if soma>d['valor_total']: raise ValueError('Valor inferior ao total já destinado.')

            if (
                modulo == 'vinculos'
                and d['funcao_desempenhada'] == 3
            ):
                coordenadores = linhas(
                    cur,
                    '''
                    SELECT cpf
                    FROM vinculo_projeto_participante
                    WHERE codigo_projeto = %s
                      AND funcao_desempenhada = 3
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
                
            cols=list(d)
            if chave is None:
                cur.execute(f"INSERT INTO {m['tabela']} ({','.join(cols)}) VALUES ({','.join(['%s']*len(cols))})",tuple(d.values()))
                if modulo=='projetos' and not s.admin:
                    tipo=identidade(cur,s)['tipo_participante']
                    cur.execute('INSERT INTO vinculo_projeto_participante (codigo_projeto,cpf,funcao_desempenhada,data_entrada) VALUES (%s,%s,%s,%s)',(d['codigo_projeto'],s.cpf,1 if tipo==3 else 3,d['data_inicio']))
            else:
                cols=[c for c in cols if c not in pk]
                cur.execute(f"UPDATE {m['tabela']} SET {','.join(c+'=%s' for c in cols)} WHERE {where}",tuple(d[c] for c in cols)+key)
            if modulo=='producoes':
                cur.execute('DELETE FROM autoria_producao WHERE codigo_projeto=%s AND codigo_prod=%s',key)
                for cpf in autores:
                    cur.execute('INSERT INTO autoria_producao (codigo_projeto,codigo_prod,cpf) VALUES (%s,%s,%s)',key+(cpf,))
            # Libera somente após commit, evitando corrida na verificação de e-mail.
            cur.execute('COMMIT')
        except Exception:
            cur.execute('ROLLBACK')
            raise
        finally:
            cur.execute("SELECT RELEASE_LOCK('sigpesq_escrita')")
            cur.fetchall()

def excluir(modulo,chave,s):
    # Exclusão reservada ao administrador; remoções explícitas e proteção das autorias.
    if not s or not s.admin: raise ValueError('Somente o administrador pode excluir registros.')
    m=MODELOS[modulo]
    with transacao() as cur:
        cur.execute("SELECT GET_LOCK('sigpesq_escrita',10) AS ok")
        if cur.fetchone()['ok']!=1: raise ValueError('Banco ocupado.')
        try:
            if modulo=='vinculos' and linhas(cur,'SELECT cpf FROM autoria_producao WHERE codigo_projeto=%s AND cpf=%s',chave):
                raise ValueError('Este participante é autor de produções do projeto. Edite os autores antes de remover o vínculo.')
            if modulo=='participantes' and linhas(cur,'SELECT cpf FROM autoria_producao WHERE cpf=%s',chave):
                raise ValueError('Este participante é autor de produções. Edite os autores antes de excluir sua conta.')
            if modulo=='projetos':
                # Remove autorias antes dos vínculos protegidos por RESTRICT.
                cur.execute('DELETE FROM autoria_producao WHERE codigo_projeto=%s',chave)
                for t in ('producao_cientifica','vinculo_projeto_participante','vinculo_projeto_financiamento'):
                    cur.execute(f'DELETE FROM {t} WHERE codigo_projeto=%s',chave)
            if modulo=='participantes': cur.execute('DELETE FROM vinculo_projeto_participante WHERE cpf=%s',chave)
            if modulo=='financiamentos': cur.execute('DELETE FROM vinculo_projeto_financiamento WHERE codigo_financiamento=%s',chave)
            cur.execute(f"DELETE FROM {m['tabela']} WHERE "+' AND '.join(k+'=%s' for k in m['pk']),chave)
            if not cur.rowcount: raise ValueError('Registro não encontrado.')
            cur.execute('COMMIT')
        except Exception:
            cur.execute('ROLLBACK'); raise
        finally:
            cur.execute("SELECT RELEASE_LOCK('sigpesq_escrita')"); cur.fetchall()


def validar_autores(valores):
    from validacao import cpf_limpo
    if not isinstance(valores,(list,tuple)) or not valores:
        raise ValueError('Selecione pelo menos um autor para a produção científica.')
    return list(dict.fromkeys(cpf_limpo(str(cpf)) for cpf in valores))
