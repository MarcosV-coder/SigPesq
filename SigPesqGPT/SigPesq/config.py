"""Configuração por ambiente. Senhas nunca são gravadas no projeto."""
import os


def mysql_config():
    try:
        port = int(os.getenv('SIGPESQ_DB_PORT', '3306'))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError as exc:
        raise ValueError('SIGPESQ_DB_PORT deve ser um número entre 1 e 65535.') from exc
    return dict(host=os.getenv('SIGPESQ_DB_HOST', '127.0.0.1'), port=port,
                user=os.getenv('SIGPESQ_DB_USER', 'sigpesq_app'),
                password=os.getenv('SIGPESQ_DB_PASSWORD', ''),
                database=os.getenv('SIGPESQ_DB_NAME', 'sigpesq'),
                charset='utf8mb4', autocommit=False, connection_timeout=5)
