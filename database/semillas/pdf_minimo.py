"""Arma un PDF de una página con texto, sin dependencias, que pasa la validación del backend."""


def _escapar(texto):
    return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def crear_pdf(lineas):
    cuerpo = "BT /F1 11 Tf 56 790 Td 16 TL\n"
    cuerpo += "".join(f"({_escapar(linea)}) Tj T*\n" for linea in lineas)
    cuerpo += "ET"
    contenido = cuerpo.encode("cp1252", errors="replace")
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        (
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
            b"/Encoding /WinAnsiEncoding >>"
        ),
        b"<< /Length %d >>\nstream\n" % len(contenido) + contenido + b"\nendstream",
    ]
    salida = b"%PDF-1.4\n"
    posiciones = []
    for numero, objeto in enumerate(objetos, 1):
        posiciones.append(len(salida))
        salida += b"%d 0 obj\n" % numero + objeto + b"\nendobj\n"
    inicio_xref = len(salida)
    salida += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objetos) + 1)
    for posicion in posiciones:
        salida += b"%010d 00000 n \n" % posicion
    salida += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objetos) + 1,
        inicio_xref,
    )
    return salida
