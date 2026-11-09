"""Validação independente da interface, com Decimal para valores monetários."""
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation


def cpf_limpo(texto):
    # O SQL exige 11 dígitos, mas não valida os dígitos verificadores.
    value = re.sub(r'[.\-\s]', '', texto)
    if not re.fullmatch(r'\d{11}', value, flags=re.ASCII):
        raise ValueError('CPF deve conter 11 dígitos, com ou sem pontuação.')
    return value


def moeda(texto):
    value = texto.strip().replace('R$', '').replace(' ', '')
    if ',' in value:
        if not re.fullmatch(r'(?:\d{1,3}(?:\.\d{3})+|\d+),\d{1,2}', value):
            raise ValueError('Use 1.234,56 ou 1234.56 para valores monetários.')
        value = value.replace('.', '').replace(',', '.')
    elif not re.fullmatch(r'\d+(?:\.\d{1,2})?', value):
        raise ValueError('Informe um valor positivo com até duas casas decimais.')
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('Valor monetário inválido.') from exc
    if not result.is_finite() or result <= 0 or result > Decimal('999999999999999999.99'):
        raise ValueError('Valor deve ser positivo e caber em DECIMAL(20,2).')
    return result.quantize(Decimal('0.01'))


def data(texto):
    for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
        try:
            result = datetime.strptime(texto, fmt).date()
            if result.year < 1000:
                break
            return result
        except ValueError:
            pass
    raise ValueError('Data inválida. Use DD/MM/AAAA (ex.: 08/11/2026).')


def validar(campos, valores):
    dados = {}
    for c in campos:
        value = valores.get(c.nome)
        if isinstance(value, str):
            value = value.strip()
        if value is None or value == '' or value == []:
            if c.obrigatorio:
                raise ValueError(f'Preencha: {c.rotulo}.')
            dados[c.nome] = None
            continue
        if c.tipo == 'cpf':
            value = cpf_limpo(value)
        elif c.tipo == 'data':
            value = data(value)
        elif c.tipo == 'dinheiro':
            value = moeda(value)
        elif c.tipo in ('inteiro','ano','horas'):
            if not str(value).isascii() or not str(value).isdigit():
                raise ValueError(f'{c.rotulo}: informe um número inteiro.')
            value = int(value)
            low, high = (1000,9999) if c.tipo == 'ano' else ((1,168) if c.tipo == 'horas' else (1,4294967295))
            if not low <= value <= high:
                raise ValueError(f'{c.rotulo}: use um valor entre {low} e {high}.')
        elif c.tipo == 'opcao':
            if value not in dict(c.opcoes):
                raise ValueError(f'Selecione uma opção válida: {c.rotulo}.')
        elif c.tipo in ('texto','multilinha') and len(value) > c.limite:
            raise ValueError(f'{c.rotulo}: máximo de {c.limite} caracteres.')
        dados[c.nome] = value
    if 'email' in dados and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', dados['email']):
        raise ValueError('Informe um e-mail válido, por exemplo nome@universidade.br.')
    if 'nome' in dados and not re.fullmatch(r'[a-zA-ZÀ-ÿ ]+', dados['nome']):
        raise ValueError('Nome deve conter apenas letras e espaços (regra do SQL original).')
    for a,b in [('data_inicio','data_termino'),('data_entrada','data_saida'),('inicio','fim')]:
        if dados.get(b) and (not dados.get(a) or dados[b] < dados[a]):
            raise ValueError('O término exige um início e não pode ser anterior a ele.')
    if dados.get('projeto') and (not dados.get('funcao') or not dados.get('inicio')):
        raise ValueError('Para vincular o participante, informe função e início.')
    if 'projeto' in dados and not dados['projeto'] and any(dados.get(k) for k in ('funcao','inicio','fim')):
        raise ValueError('Selecione o projeto ou limpe os campos do vínculo inicial.')
    return dados


def formatar(value):
    if value is None:
        return '—'
    if isinstance(value, (date, datetime)):
        return value.strftime('%d/%m/%Y')
    if isinstance(value, Decimal):
        return 'R$ ' + f'{value:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
    return str(value)
