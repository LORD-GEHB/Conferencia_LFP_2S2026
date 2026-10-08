class TipoToken:

    NUMERAL = "NUMERAL"
    SUBRAYADO_H1 = "SUBRAYADO_H1"

    VINETA = "VIÑETA"
    NUMERO_LISTA = "NUMERO_LISTA"
    TAREA_PENDIENTE = "TAREA_PENDIENTE"
    TAREA_COMPLETADA = "TAREA_COMPLETADA"
    INDENTACION = "INDENTACION"

    CITA = "CITA"

    CERCA_CODIGO = "CERCA_CODIGO"
    CODIGO_INLINE = "CODIGO_INLINE"

    REGLA_HORIZONTAL = "REGLA_HORIZONTAL"
    SALTO_LINEA = "SALTO_LINEA"
    SALTO_LINEA_FORZADO = "SALTO_LINEA_FORZADO"
    SALTO_PARRAFO = "SALTO_PARRAFO"

    NEGRITA = "NEGRITA"
    CURSIVA = "CURSIVA"
    NEGRITA_CURSIVA = "NEGRITA_CURSIVA"
    TACHADO = "TACHADO"

    CORCHETE_ABRE = "CORCHETE_ABRE"
    CORCHETE_CIERRA = "CORCHETE_CIERRA"
    IMAGEN_ABRE = "IMAGEN_ABRE"
    PARENTESIS_ABRE = "PARENTESIS_ABRE"
    PARENTESIS_CIERRA = "PARENTESIS_CIERRA"
    URL = "URL"
    AUTOENLACE = "AUTOENLACE"

    BARRA_TABLA = "BARRA_TABLA"
    SEPARADOR_TABLA = "SEPARADOR_TABLA"

    ESCAPE = "ESCAPE"
    ETIQUETA_HTML = "ETIQUETA_HTML"
    ENTIDAD_HTML = "ENTIDAD_HTML"
    TEXTO = "TEXTO"
    FIN = "FIN"


class Token:

    def __init__(self, tipo, lexema, linea, columna):
        self.tipo = tipo
        self.lexema = lexema
        self.linea = linea
        self.columna = columna

    def __repr__(self):
        return f"Token({self.tipo}, {self.lexema!r}, {self.linea}:{self.columna})"
