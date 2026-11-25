"""Configura somente a conexão MySQL; o administrador já está disponível."""
import json, os
from getpass import getpass
from config import ARQUIVO, local

def main():
    anterior=local()
    print('Conexão MySQL — pressione Enter para manter o valor entre colchetes.')
    d={}
    d['DB_HOST']=input(f"Servidor [{anterior.get('DB_HOST','127.0.0.1')}]: ").strip() or anterior.get('DB_HOST','127.0.0.1')
    while True:
        porta=input(f"Porta [{anterior.get('DB_PORT',3306)}]: ").strip() or anterior.get('DB_PORT',3306)
        try:
            d['DB_PORT']=int(porta)
            if not 1<=d['DB_PORT']<=65535: raise ValueError()
            break
        except (ValueError,TypeError): print('Informe somente o número da porta, por exemplo 3306.')
    for k,label,padrao in [('DB_USER','Usuário MySQL','root'),('DB_NAME','Banco','sigpesq')]:
        default=anterior.get(k,padrao)
        d[k]=input(f'{label} [{default}]: ').strip() or default
    d['DB_PASSWORD']=getpass('Senha do MySQL: ') or anterior.get('DB_PASSWORD','')
    ARQUIVO.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    if os.name!='nt': ARQUIVO.chmod(0o600)
    from db import testar_conexao,mensagem_erro
    try:
        testar_conexao()
        print('Conexão OK. Execute python main.py e entre com admin / admin123.')
    except Exception as e: print(mensagem_erro(e)+' Corrija a conexão e execute configurar.py novamente.')

if __name__=='__main__':
    try: main()
    except (KeyboardInterrupt,EOFError): raise SystemExit('Configuração cancelada. Execute python configurar.py para tentar novamente.')
