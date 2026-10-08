from analizador_lexico import AnalizadorLexico
from interfaz import InterfazMarkdown


def analizar(texto):
    lexico = AnalizadorLexico(texto)
    tokens = lexico.tokenizar()
    return tokens, lexico.errores


def main():
    app = InterfazMarkdown(analizar)
    app.mainloop()


if __name__ == "__main__":
    main()
