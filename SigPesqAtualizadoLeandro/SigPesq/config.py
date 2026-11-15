"""Configuração local, com substituição opcional por variáveis de ambiente."""
import json, os
from pathlib import Path
ARQUIVO=Path(__file__).with_name('config_local.json')
def local():
    if not ARQUIVO.exists(): return {}
    try: return json.loads(ARQUIVO.read_text(encoding='utf-8'))
    except (ValueError,OSError) as exc: raise ValueError('Configuração inválida. Execute python configurar.py novamente.') from exc
def opcao(nome,padrao=''):
    return os.getenv('SIGPESQ_'+nome,local().get(nome,padrao))
def mysql_config():
    try:
        port=int(opcao('DB_PORT',3306))
        if not 1<=port<=65535: raise ValueError()
    except (ValueError,TypeError) as exc: raise ValueError('Porta MySQL inválida.') from exc
    return dict(host=opcao('DB_HOST','127.0.0.1'),port=port,user=opcao('DB_USER','root'),password=opcao('DB_PASSWORD'),database=opcao('DB_NAME','sigpesq'),charset='utf8mb4',autocommit=False,connection_timeout=5)
