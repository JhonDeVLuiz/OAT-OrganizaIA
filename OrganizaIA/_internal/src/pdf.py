"""Geracao de PDF (fpdf2) para a ferramenta criar_arquivo do chat."""
from fpdf import FPDF


def _latin1(texto):
    """Fontes core do PDF sao latin-1: troca o que nao couber (nunca quebra)."""
    return str(texto).encode("latin-1", "replace").decode("latin-1")


def gerar_pdf(alvo, titulo, texto):
    """Escreve um PDF simples (titulo + corpo) em `alvo`. Devolve o Path."""
    pdf = FPDF(format="A4")
    pdf.set_margins(18, 18, 18)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 8, _latin1(titulo))
    pdf.ln(4)
    pdf.set_font("Helvetica", size=11)
    for linha in str(texto).splitlines():
        if linha.strip():
            pdf.multi_cell(0, 6, _latin1(linha))
            pdf.ln(1)
        else:
            pdf.ln(4)
    pdf.output(str(alvo))
    return alvo


def disponivel():
    """True se a biblioteca de PDF esta instalada (degradacao graciosa)."""
    try:
        import fpdf  # noqa: F401
        return True
    except ImportError:
        return False
