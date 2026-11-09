"""MySQL puro: conexão curta por operação e transações com rollback."""
from contextlib import contextmanager
import mysql.connector
from config import mysql_config


@contextmanager
def transacao():
    conn = mysql.connector.connect(**mysql_config())
    cursor = None
    try:
        conn.start_transaction()
        cursor = conn.cursor(dictionary=True, buffered=True)
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()


def consultar(sql, params=()):
    with transacao() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def executar(sql, params=()):
    with transacao() as cur:
        cur.execute(sql, params)
        return cur.rowcount


def testar_conexao():
    return consultar('SELECT DATABASE() AS banco, VERSION() AS versao')[0]


def mensagem_erro(exc):
    if isinstance(exc, mysql.connector.Error):
        messages = {
            1045: 'Acesso negado. Confira usuário, senha e permissões do MySQL.',
            1049: 'Banco inexistente. Execute database/schema.sql no Workbench.',
            1146: 'Tabela ausente. Execute schema.sql ou a migração indicada no README.',
            1054: 'Banco desatualizado. Execute database/migracao_pdf.sql uma vez.',
            1062: 'Registro duplicado: código, CPF, e-mail ou vínculo já cadastrado.',
            1451: 'Exclusão impedida por registros relacionados.',
            1452: 'O projeto, participante ou financiamento relacionado não existe.',
            2003: 'Não foi possível conectar ao MySQL. Confira serviço, host e porta.',
            3819: 'Os dados violam uma restrição do banco. Confira valores e datas.',
            4025: 'Os dados violam uma restrição do banco. Confira valores e datas.',
            1265: 'Categoria inválida para o banco. Confira a migração do esquema.',
        }
        return messages.get(exc.errno, f'Falha MySQL ({exc.errno}). Confira o esquema e os dados informados.')
    return str(exc)
