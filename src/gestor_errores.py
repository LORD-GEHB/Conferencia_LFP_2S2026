class TipoError:
    ENCABEZADO_INVALIDO = "ENCABEZADO_INVALIDO"


class ErrorAnalisis:

    def __init__(self, numero, lexema, tipo, descripcion, linea, columna, fase):
        self.numero = numero
        self.lexema = lexema
        self.tipo = tipo
        self.descripcion = descripcion
        self.linea = linea
        self.columna = columna
        self.fase = fase

    def __repr__(self):
        return f"Error({self.tipo}, {self.lexema!r}, {self.linea}:{self.columna})"


class GestorErrores:

    def __init__(self):
        self.errores = []

    def agregar(self, tipo, lexema, descripcion, linea, columna, fase="Léxico"):
        error = ErrorAnalisis(len(self.errores) + 1, lexema, tipo, descripcion,
                              linea, columna, fase)
        self.errores.append(error)
        return error

    def hay_errores(self):
        return len(self.errores) > 0

    def limpiar(self):
        self.errores = []
