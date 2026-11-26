"""Login de participantes e administrador independente com credencial própria."""
import hashlib, secrets, hmac
from dataclasses import dataclass
ITERACOES=600_000
ADMIN_LOGIN="admin"
ADMIN_HASH='pbkdf2_sha256$600000$67746fb07cf1b3547d84318edc554ddd$a91b0ea1c96015e7d145b401e9f3a5a4fa2a3fb5b00818b488db71dd96c412d4'
@dataclass(frozen=True)
class Sessao:
    cpf: str | None
    nome: str
    admin: bool = False

def gerar_hash(senha):
    if not isinstance(senha,str) or not 8 <= len(senha) <= 128:
        raise ValueError('A senha deve ter entre 8 e 128 caracteres.')
    salt=secrets.token_hex(16)
    digest=hashlib.pbkdf2_hmac('sha256',senha.encode(),salt.encode(),ITERACOES).hex()
    return f'pbkdf2_sha256${ITERACOES}${salt}${digest}'

def conferir(senha,registro):
    try:
        algoritmo,n,salt,digest=registro.split('$')
        if algoritmo!='pbkdf2_sha256' or not 1 <= int(n) <= 2_000_000: return False
        atual=hashlib.pbkdf2_hmac('sha256',senha.encode(),salt.encode(),int(n)).hex()
        return hmac.compare_digest(atual,digest)
    except (ValueError,TypeError,AttributeError): return False

def autenticar(login,senha):
    from db import transacao
    login=login.strip().lower()
    if login==ADMIN_LOGIN:
        if conferir(senha,ADMIN_HASH): return Sessao(None,'Administrador geral',True)
    else:
        with transacao() as cur:
            cur.execute('SELECT cpf,nome,senha FROM participante WHERE excluido_em IS NULL AND (LOWER(email)=%s OR cpf=%s)',(login,login))
            rows=cur.fetchall()
            if len(rows)==1 and conferir(senha,rows[0]['senha']): return Sessao(rows[0]['cpf'],rows[0]['nome'])
    raise ValueError('Login ou senha inválidos.')
