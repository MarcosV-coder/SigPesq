from telas.base import TelaCadastro


class Producoes(TelaCadastro):
    def __init__(self, master, app):
        super().__init__(master, app, "producoes")
