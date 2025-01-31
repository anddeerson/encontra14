import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd
import re
import unicodedata
from PyPDF2 import PdfReader

# Configuração do Tesseract (se necessário para OCR)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Exemplo para Windows


def normalizar_texto(texto):
    """Remove acentos e converte para minúsculas."""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    return texto.lower().strip()


def fix_spacing(text):
    """
    Corrige a falta de espaços no texto extraído do PDF.
    Adiciona espaço antes das letras maiúsculas que estão grudadas sem espaço antes.
    """
    fixed_text = re.sub(r'(?<=[a-záéíóúç])(?=[A-ZÁÉÍÓÚÇ])', ' ', text)
    return fixed_text


def extrair_texto_pdf(pdf_file):
    """Extrai e corrige o texto de PDFs baseados em texto."""
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"

    # Aplicar correção de espaçamento
    text = fix_spacing(text)

    return text


def extrair_nomes_pdf(pdf_file):
    """Extrai nomes completos do PDF, normalizando-os."""
    text = extrair_texto_pdf(pdf_file)
    matches = re.findall(r'\b[A-ZÀ-Ú][A-ZÀ-Úa-zà-ú]+\s[A-ZÀ-Úa-zà-ú ]+\b',
                         text)  # Expressão regular para capturar nomes completos
    return sorted({normalizar_texto(name) for name in matches})


def check_names_in_pdf(pdf_file, names):
    """Verifica quais nomes da lista estão no PDF."""
    found_names = []
    approved_names = extrair_nomes_pdf(pdf_file)

    for name in names:
        normalized_name = normalizar_texto(name)
        if normalized_name in approved_names:
            found_names.append(name)

    return found_names


def main(names, pdf_files):
    results = []
    for pdf_file in pdf_files:
        found_names = check_names_in_pdf(pdf_file, names)
        for name in found_names:
            results.append({"Nome": name, "PDF": pdf_file.name})

    df = pd.DataFrame(results).drop_duplicates()  # Remove duplicatas
    df = df.sort_values(by="Nome")  # Ordena os resultados em ordem alfabética
    return df


# Interface do Streamlit
st.title("Encontra aluno(s). Versão 1.4 - Busca pelo nome completo - Scan com opção de OCR")
st.write("Cole a lista de nomes e faça upload dos PDFs para verificar quais nomes completos estão presentes.")

names_input = st.text_area("Cole a lista de nomes (um por linha):")
names = [name.strip() for name in names_input.split("\n") if name.strip()]

pdf_files = st.file_uploader("Faça upload dos PDFs", type="pdf", accept_multiple_files=True)

if st.button("Analisar PDFs"):
    if not names:
        st.warning("Por favor, insira pelo menos um nome.")
    elif not pdf_files:
        st.warning("Por favor, faça upload de pelo menos um PDF.")
    else:
        with st.spinner("Analisando PDFs..."):
            resultados = main(names, pdf_files)
            if resultados.empty:
                st.write("Nenhum nome foi encontrado nos PDFs.")
            else:
                st.write("Resultados:")
                st.dataframe(resultados)

                # Download CSV
                csv = resultados.to_csv(index=False).encode("utf-8")
                st.download_button("Baixar resultados em CSV", data=csv, file_name="resultados.csv", mime="text/csv")
