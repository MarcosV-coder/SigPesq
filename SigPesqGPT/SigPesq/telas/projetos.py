from telas.base import TelaCadastro


class Projetos(TelaCadastro):
    def __init__(self, master, app):
        super().__init__(master, app, "projetos")
