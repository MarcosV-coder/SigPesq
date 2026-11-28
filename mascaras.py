"""Máscaras locais; a validação definitiva continua em validacao.py."""
import re
from decimal import Decimal


def digitos(texto):
    return re.sub(r'[^0-9]', '', texto)


def mascarar(texto, tipo):
    limites = {'cpf': 11, 'data': 8, 'ano': 4, 'horas': 3, 'inteiro': 10}
    numeros = digitos(texto)
    if tipo == 'dinheiro':
        if not numeros:
            return ''
        # Entrada em centavos: 123456 corresponde a 1.234,56.
        valor = Decimal(numeros[:20]) / 100
        return f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    numeros = numeros[:limites.get(tipo, len(numeros))]
    if tipo in ('cpf', 'data'):
        grupos = (3, 3, 3, 2) if tipo == 'cpf' else (2, 2, 4)
        separadores = ('.', '.', '-') if tipo == 'cpf' else ('/', '/')
        partes = []; inicio = 0
        for i, tamanho in enumerate(grupos):
            parte = numeros[inicio:inicio+tamanho]
            if not parte: break
            if i: partes.append(separadores[i-1])
            partes.append(parte); inicio += tamanho
        return ''.join(partes)
    return numeros


def aplicar_mascara(widget, tipo):
    """Formata digitação, colagem e edição sem alterar campos livres ou senhas."""
    if tipo not in ('cpf', 'data', 'dinheiro', 'inteiro', 'ano', 'horas'):
        return
    entrada = widget._entry

    def atualizar(event=None):
        if str(entrada.cget('state')) == 'disabled': return
        original = widget.get()
        posicao = entrada.index('insert')
        antes = len(digitos(original[:posicao]))
        novo = mascarar(original, tipo)
        if novo == original: return
        widget.delete(0, 'end'); widget.insert(0, novo)
        if posicao == len(original):
            destino = len(novo)
        else:
            destino = 0; vistos = 0
            for i, caractere in enumerate(novo):
                if caractere.isdigit(): vistos += 1
                if vistos >= antes:
                    destino = i + 1 if antes else 0; break
        entrada.icursor(destino)

    def apagar(event):
        # Ao apagar uma pontuação, apaga também o dígito adjacente.
        if entrada.selection_present(): return
        pos = entrada.index('insert'); texto = widget.get()
        if event.keysym == 'BackSpace' and pos > 0 and not texto[pos-1].isdigit():
            entrada.delete(max(0, pos-2), pos); atualizar(); return 'break'
        if event.keysym == 'Delete' and pos < len(texto) and not texto[pos].isdigit():
            entrada.delete(pos, pos+2); atualizar(); return 'break'

    widget.bind('<KeyRelease>', atualizar, add='+')
    widget.bind('<BackSpace>', apagar, add='+')
    widget.bind('<Delete>', apagar, add='+')
    for evento in ('<<Paste>>', '<<Cut>>'):
        widget.bind(evento, lambda e: widget.after_idle(atualizar), add='+')
    widget.bind('<FocusOut>', atualizar, add='+')
    atualizar()
