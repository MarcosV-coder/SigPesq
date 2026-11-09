from telas.base import TelaCadastro


class Participantes(TelaCadastro):
    def __init__(self, master, app):
        super().__init__(master, app, "participantes")
