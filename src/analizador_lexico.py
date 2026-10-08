from tokens import Token, TipoToken as T
from gestor_errores import GestorErrores, TipoError as E

PUNTUACION_ASCII = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"


def es_espacio(c):
    return c == "" or c == " " or c == "\t"


def es_digito(c):
    return c != "" and "0" <= c <= "9"


def es_letra_ascii(c):
    return c != "" and ("a" <= c <= "z" or "A" <= c <= "Z")


def es_alfanumerico_ascii(c):
    return es_letra_ascii(c) or es_digito(c)


def es_hexadecimal(c):
    return es_digito(c) or (c != "" and ("a" <= c <= "f" or "A" <= c <= "F"))


class AnalizadorLexico:

    def __init__(self, texto):
        self.texto = texto
        self.gestor_errores = GestorErrores()
        self.tokens = []

        self.lineas = self._dividir_lineas(texto)
        self._termina_con_salto = len(texto) > 0 and texto[-1] in "\r\n"

        self._pendientes = []
        self._n = 0
        self._linea = ""
        self._num = 0
        self._terminado = False
        self._token_fin = None

    def siguiente_token(self):
        while not self._pendientes:
            if self._terminado:
                return self._token_fin
            if self._n < len(self.lineas):
                self._procesar_linea()
            else:
                self._cerrar_documento()
        token = self._pendientes.pop(0)
        self.tokens.append(token)
        return token

    def tokenizar(self):
        while True:
            token = self.siguiente_token()
            if token.tipo == T.FIN:
                return self.tokens

    @property
    def errores(self):
        return self.gestor_errores.errores

    def _dividir_lineas(self, texto):
        lineas = []
        actual = []
        k = 0
        while k < len(texto):
            c = texto[k]
            if c == "\r":
                if k + 1 < len(texto) and texto[k + 1] == "\n":
                    k += 1
                lineas.append("".join(actual))
                actual = []
            elif c == "\n":
                lineas.append("".join(actual))
                actual = []
            else:
                actual.append(c)
            k += 1
        if actual:
            lineas.append("".join(actual))
        return lineas

    def _c(self, k):
        return self._linea[k] if 0 <= k < len(self._linea) else ""

    def _saltar_espacios(self, k):
        while k < len(self._linea) and self._linea[k] in " \t":
            k += 1
        return k

    def _fin_sin_espacios(self):
        fin = len(self._linea)
        while fin > 0 and self._linea[fin - 1] in " \t":
            fin -= 1
        return fin

    def _emitir(self, tipo, lexema, columna, linea=None):
        token = Token(tipo, lexema, self._num if linea is None else linea, columna)
        self._pendientes.append(token)
        return token

    def _error(self, tipo, lexema, descripcion, columna):
        self.gestor_errores.agregar(tipo, lexema, descripcion, self._num, columna)

    def _procesar_linea(self):
        self._linea = self.lineas[self._n]
        self._num = self._n + 1
        self._n += 1

        if self._saltar_espacios(0) == len(self._linea):
            self._emitir_salto(T.SALTO_PARRAFO)
            return

        k = self._leer_indentacion(0)
        k = self._leer_cita(k)
        k = self._leer_indentacion(k)
        self._leer_contenido(k)
        self._emitir_salto(T.SALTO_LINEA)

    def _emitir_salto(self, tipo):
        if self._n < len(self.lineas) or self._termina_con_salto:
            self._emitir(tipo, "\n", len(self._linea) + 1)

    def _leer_indentacion(self, k):
        fin = self._saltar_espacios(k)
        if fin > k and fin < len(self._linea):
            self._emitir(T.INDENTACION, self._linea[k:fin], k + 1)
        return fin

    def _leer_cita(self, k):
        if self._c(k) != ">":
            return k
        inicio = k
        fin = k
        while self._c(k) == ">":
            k += 1
            fin = k
            if self._c(k) == " " and self._c(k + 1) == ">":
                k += 1
        self._emitir(T.CITA, self._linea[inicio:fin], inicio + 1)
        if self._c(k) == " ":
            k += 1
        return k

    def _leer_contenido(self, k):
        if self._es_encabezado(k):
            self._encabezado(k)
        elif self._es_cerca(k):
            self._cerca_codigo(k)
        elif self._es_linea_de(k, "-*_", 3):
            self._emitir(T.REGLA_HORIZONTAL, self._linea[k:self._fin_sin_espacios()], k + 1)
        elif self._es_linea_de(k, "=", 1):
            self._emitir(T.SUBRAYADO_H1, self._linea[k:self._fin_sin_espacios()], k + 1)
        elif self._es_delimitador_tabla(k):
            self._delimitador_tabla(k)
        elif self._es_item(k) is not None:
            self._item_lista(k)
        else:
            self._texto_de_linea(k)

    def _es_encabezado(self, k):
        n = 0
        while self._c(k + n) == "#":
            n += 1
        return n > 0 and es_espacio(self._c(k + n))

    def _encabezado(self, k):
        n = 0
        while self._c(k + n) == "#":
            n += 1
        if n > 6:
            self._error(E.ENCABEZADO_INVALIDO, "#" * n,
                        f"Encabezado inválido en línea {self._num}: máximo 6 niveles",
                        k + 1)
            self._texto_de_linea(k)
            return
        self._emitir(T.NUMERAL, "#" * n, k + 1)
        self._texto_de_linea(self._saltar_espacios(k + n))

    def _es_cerca(self, k):
        c = self._c(k)
        if c != "`" and c != "~":
            return False
        n = 0
        while self._c(k + n) == c:
            n += 1
        return n >= 3

    def _cerca_codigo(self, k):
        c = self._linea[k]
        n = 0
        while self._c(k + n) == c:
            n += 1
        self._emitir(T.CERCA_CODIGO, c * n, k + 1)
        inicio = self._saltar_espacios(k + n)
        fin = self._fin_sin_espacios()
        if inicio < fin:
            self._emitir(T.TEXTO, self._linea[inicio:fin], inicio + 1)

    def _es_linea_de(self, k, caracteres, minimo):
        c = self._c(k)
        if c == "" or c not in caracteres:
            return False
        cantidad = 0
        while k < len(self._linea):
            if self._linea[k] == c:
                cantidad += 1
            elif self._linea[k] not in " \t":
                return False
            k += 1
        return cantidad >= minimo

    def _es_delimitador_tabla(self, k):
        tiene_barra = False
        tiene_guion = False
        while k < len(self._linea):
            c = self._linea[k]
            if c == "|":
                tiene_barra = True
            elif c == "-":
                tiene_guion = True
            elif c not in ": \t":
                return False
            k += 1
        return tiene_barra and tiene_guion

    def _delimitador_tabla(self, k):
        fin = self._fin_sin_espacios()
        while k < fin:
            c = self._linea[k]
            if c == "|":
                self._emitir(T.BARRA_TABLA, "|", k + 1)
                k += 1
            elif c == ":" or c == "-":
                inicio = k
                while k < fin and self._linea[k] in ":-":
                    k += 1
                self._emitir(T.SEPARADOR_TABLA, self._linea[inicio:k], inicio + 1)
            else:
                k += 1

    def _es_item(self, k):
        c = self._c(k)
        if c != "" and c in "-*+":
            return (T.VINETA, k + 1) if es_espacio(self._c(k + 1)) else None
        j = k
        while es_digito(self._c(j)) and j - k < 9:
            j += 1
        if j > k and self._c(j) != "" and self._c(j) in ".)" and es_espacio(self._c(j + 1)):
            return (T.NUMERO_LISTA, j + 1)
        return None

    def _item_lista(self, k):
        tipo, fin_marcador = self._es_item(k)
        self._emitir(tipo, self._linea[k:fin_marcador], k + 1)

        k = self._saltar_espacios(fin_marcador)
        caja = self._linea[k:k + 3]
        if (len(caja) == 3 and caja[0] == "[" and caja[2] == "]"
                and caja[1] in " xX" and es_espacio(self._c(k + 3))):
            tipo_tarea = T.TAREA_PENDIENTE if caja[1] == " " else T.TAREA_COMPLETADA
            self._emitir(tipo_tarea, caja, k + 1)
            k = self._saltar_espacios(k + 3)

        self._texto_de_linea(k)

    def _texto_de_linea(self, inicio):
        fin = self._fin_sin_espacios()
        barras = 0
        while fin - barras - 1 >= inicio and self._linea[fin - barras - 1] == "\\":
            barras += 1
        if barras % 2 == 1 and fin == len(self._linea):
            self._en_linea(inicio, fin - 1)
            self._emitir(T.SALTO_LINEA_FORZADO, "\\", fin)
            return
        self._en_linea(inicio, fin)
        espacios_finales = self._linea[fin:]
        if len(espacios_finales) >= 2 and "\t" not in espacios_finales:
            self._emitir(T.SALTO_LINEA_FORZADO, espacios_finales, fin + 1)

    def _en_linea(self, inicio, fin):
        s = self._linea
        k = inicio
        inicio_texto = inicio

        while k < fin:
            c = s[k]
            siguiente = s[k + 1] if k + 1 < fin else ""
            nuevo = None

            if c == "\\" and siguiente != "" and siguiente in PUNTUACION_ASCII:
                self._vaciar_texto(inicio_texto, k)
                self._emitir(T.ESCAPE, s[k:k + 2], k + 1)
                nuevo = k + 2
            elif c == "`":
                n = self._largo_racha(k, fin)
                self._vaciar_texto(inicio_texto, k)
                self._emitir(T.CODIGO_INLINE, s[k:k + n], k + 1)
                nuevo = k + n
            elif c == "*" or c == "_" or c == "~":
                n = self._largo_racha(k, fin)
                tipo = self._tipo_delimitador(k, n, fin)
                if tipo is None:
                    k += n
                    continue
                self._vaciar_texto(inicio_texto, k)
                self._emitir(tipo, s[k:k + n], k + 1)
                nuevo = k + n
            elif c == "!" and siguiente == "[":
                self._vaciar_texto(inicio_texto, k)
                self._emitir(T.IMAGEN_ABRE, "![", k + 1)
                nuevo = k + 2
            elif c in "[]()|":
                tipos = {"[": T.CORCHETE_ABRE, "]": T.CORCHETE_CIERRA,
                         "(": T.PARENTESIS_ABRE, ")": T.PARENTESIS_CIERRA,
                         "|": T.BARRA_TABLA}
                self._vaciar_texto(inicio_texto, k)
                self._emitir(tipos[c], c, k + 1)
                nuevo = k + 1
            elif c == "h":
                fin_url = self._mirar_url(k, fin)
                if fin_url is not None:
                    self._vaciar_texto(inicio_texto, k)
                    self._emitir(T.URL, s[k:fin_url], k + 1)
                    nuevo = fin_url
            elif c == "<":
                encontrado = self._mirar_angular(k, fin)
                if encontrado is not None:
                    self._vaciar_texto(inicio_texto, k)
                    tipo, nuevo = encontrado
                    self._emitir(tipo, s[k:nuevo], k + 1)
            elif c == "&":
                fin_entidad = self._mirar_entidad(k, fin)
                if fin_entidad is not None:
                    self._vaciar_texto(inicio_texto, k)
                    self._emitir(T.ENTIDAD_HTML, s[k:fin_entidad], k + 1)
                    nuevo = fin_entidad

            if nuevo is None:
                k += 1
            else:
                k = nuevo
                inicio_texto = k

        self._vaciar_texto(inicio_texto, fin)

    def _vaciar_texto(self, inicio, fin):
        if fin > inicio:
            self._emitir(T.TEXTO, self._linea[inicio:fin], inicio + 1)

    def _largo_racha(self, k, fin):
        c = self._linea[k]
        n = 0
        while k + n < fin and self._linea[k + n] == c:
            n += 1
        return n

    def _tipo_delimitador(self, k, n, fin):
        c = self._linea[k]
        antes = self._linea[k - 1] if k > 0 else ""
        despues = self._linea[k + n] if k + n < fin else ""

        if es_espacio(antes) and es_espacio(despues):
            return None
        if c == "_" and es_alfanumerico_ascii(antes) and es_alfanumerico_ascii(despues):
            return None
        if c == "~":
            return T.TACHADO if n == 2 else None
        return {1: T.CURSIVA, 2: T.NEGRITA, 3: T.NEGRITA_CURSIVA}.get(n)

    def _mirar_url(self, k, fin):
        s = self._linea
        if s.startswith("https://", k, fin):
            j = k + 8
        elif s.startswith("http://", k, fin):
            j = k + 7
        else:
            return None
        inicio = j
        while j < fin and s[j] not in " \t<>()[]\"'":
            j += 1
        return j if j > inicio else None

    def _mirar_angular(self, k, fin):
        s = self._linea

        j = k + 1
        m = j
        while m < fin and (es_alfanumerico_ascii(s[m]) or s[m] in "+.-"):
            m += 1
        if es_letra_ascii(self._c(j)) and 2 <= m - j <= 32 and self._c(m) == ":":
            q = m + 1
            while q < fin and s[q] not in " \t<>":
                q += 1
            if q < fin and s[q] == ">":
                return (T.AUTOENLACE, q + 1)

        q = j
        arroba = False
        while q < fin and s[q] not in " \t<>":
            if s[q] == "@":
                arroba = True
            q += 1
        if arroba and q > j and q < fin and s[q] == ">":
            return (T.AUTOENLACE, q + 1)

        if s[k:k + 4] == "<!--":
            q = k + 4
            while q + 2 < fin:
                if s[q] == "-" and s[q + 1] == "-" and s[q + 2] == ">":
                    return (T.ETIQUETA_HTML, q + 3)
                q += 1
            return None

        q = j
        if self._c(q) == "/":
            q += 1
        if not es_letra_ascii(self._c(q)):
            return None
        while q < fin and (es_alfanumerico_ascii(s[q]) or s[q] == "-"):
            q += 1
        if q < fin and s[q] not in " \t/>":
            return None
        comilla = None
        while q < fin:
            c = s[q]
            if comilla:
                if c == comilla:
                    comilla = None
            elif c == '"' or c == "'":
                comilla = c
            elif c == ">":
                return (T.ETIQUETA_HTML, q + 1)
            q += 1
        return None

    def _mirar_entidad(self, k, fin):
        s = self._linea
        j = k + 1
        if j < fin and s[j] == "#":
            j += 1
            hexadecimal = j < fin and s[j] in "xX"
            if hexadecimal:
                j += 1
            inicio = j
            while j < fin and (es_hexadecimal(s[j]) if hexadecimal else es_digito(s[j])):
                j += 1
            valido = 1 <= j - inicio <= 7
        else:
            inicio = j
            while j < fin and es_alfanumerico_ascii(s[j]):
                j += 1
            valido = 1 <= j - inicio <= 32 and es_letra_ascii(self._c(inicio))
        if valido and j < fin and s[j] == ";":
            return j + 1
        return None

    def _cerrar_documento(self):
        ultima = len(self.lineas)
        if self._termina_con_salto or not self.lineas:
            linea, columna = ultima + 1, 1
        else:
            linea, columna = ultima, len(self.lineas[-1]) + 1
        self._token_fin = self._emitir(T.FIN, "", columna, linea)
        self._terminado = True
