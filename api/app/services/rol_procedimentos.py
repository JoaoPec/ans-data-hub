import csv
import os
from zipfile import ZipFile

import pdfplumber
import requests
from bs4 import BeautifulSoup


def download_rol_procedimentos():
    """
    Função que realiza o scraping da página, encontra os links dos PDFs que contêm
    'Anexo I' ou 'Anexo II' no texto, faz o download, compacta em um ZIP e extrai os arquivos.
    """
    url = "https://www.gov.br/ans/pt-br/acesso-a-informacao/participacao-da-sociedade/atualizacao-do-rol-de-procedimentos"
    response = requests.get(url,timeout=30)
    if response.status_code != 200:
        return {"status": "error", "message": "Falha ao acessar a página."}

    soup = BeautifulSoup(response.content, "html.parser")
    
    pdf_links = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.endswith(".pdf") and ("Anexo I" in link.get_text() or "Anexo II" in link.get_text()):
            pdf_links.append(href)
    
    if not pdf_links:
        return {"status": "error", "message": "Nenhum link de PDF com 'Anexo I' ou 'Anexo II' encontrado."}

    save_dir = "downloads"
    extracted_dir = os.path.join(save_dir, "extracted")
    os.makedirs(save_dir, exist_ok=True)  
    os.makedirs(extracted_dir, exist_ok=True)  
    
    pdf_files = []
    for i, pdf_url in enumerate(pdf_links):
        if not pdf_url.startswith("http"):
            pdf_url = "https://www.gov.br" + pdf_url
        
        pdf_response = requests.get(pdf_url, timeout=20)
        if pdf_response.status_code == 200:
            pdf_filename = os.path.join(save_dir, f"document_{i + 1}.pdf")
            with open(pdf_filename, "wb") as f:
                f.write(pdf_response.content)
            pdf_files.append(pdf_filename)
        else:
            return {"status": "error", "message": f"Falha ao baixar o arquivo PDF {i + 1}"}

    zip_filename = os.path.join(save_dir, "rol_procedimentos.zip")
    with ZipFile(zip_filename, 'w') as zipf:
        for pdf in pdf_files:
            zipf.write(pdf, os.path.basename(pdf))  


    with ZipFile(zip_filename, 'r') as zipf:
        zipf.extractall(extracted_dir)

    return {
        "status": "success",
        "message": "Rol de procedimentos baixado, compactado e extraído com sucesso!",
        "zip_file_path": zip_filename,
        "extracted_files_path": extracted_dir
    }


CSV_PATH = "dados_rol.csv"

# Dicionário de substituições
SUBSTITUICOES = {
    "OD": "Seg. Odontológica",
    "AMB": "Seg. Ambulatorial",
}

def processar_zip():
    """
    Procura pelo ZIP 'rol_procedimentos.zip', extrai os PDFs e processa os dados.
    """
    # Buscar um ZIP que tenha "rol_procedimentos" no nome dentro de "downloads/"
    zip_files = [f for f in os.listdir("downloads") if "rol_procedimentos" in f.lower() and f.endswith(".zip")]
    
    if not zip_files:
        return {"status": "error", "message": "Nenhum arquivo ZIP com 'rol_procedimentos' encontrado."}
    
    zip_path = os.path.join("downloads", zip_files[0])
    
    # Criar diretório para extração se não existir
    extracted_dir = os.path.join("downloads", "extracted")
    os.makedirs(extracted_dir, exist_ok=True)

    # Extrair o ZIP
    with ZipFile(zip_path, 'r') as zipf:
        zipf.extractall(extracted_dir)

    # Buscar um PDF extraído que tenha "anexo_I" no nome
    pdf_files = [f for f in os.listdir(extracted_dir) if "anexo_I" in f.lower() and f.endswith(".pdf")]
    
    if not pdf_files:
        return {"status": "error", "message": "Nenhum PDF 'anexo_I' encontrado dentro do ZIP extraído."}
    
    pdf_path = os.path.join(extracted_dir, pdf_files[0])
    dados_extraidos = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for pagina in pdf.pages:
            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                for linha in tabela:
                    if linha and any(campo.strip() for campo in linha):  # Ignorar linhas vazias
                        dados_extraidos.append(linha)
    
    if not dados_extraidos:
        return {"status": "error", "message": "Nenhuma tabela encontrada no PDF."}
    
    # Salvar CSV
    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(dados_extraidos)

    return {"status": "success", "message": "Dados extraídos e salvos em CSV."}

def substituir_abreviacoes():
    """
    Substitui as abreviações OD e AMB pelas descrições completas.
    """
    dados_processados = []

    with open(CSV_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for linha in reader:
            linha_atualizada = [SUBSTITUICOES.get(valor, valor) for valor in linha]
            dados_processados.append(linha_atualizada)

    with open(CSV_PATH, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(dados_processados)

    return {"status": "success", "message": "Substituições realizadas."}

def compactar_csv():
    """
    Compacta o arquivo CSV em um ZIP.
    """
    zip_output_path = "downloads/Teste_seu_nome.zip"
    with ZipFile(zip_output_path, "w") as zipf:
        zipf.write(CSV_PATH)

    os.remove(CSV_PATH)  # Remove o CSV após compactação
    return {"status": "success", "message": "Arquivo CSV compactado em ZIP.", "zip_path": zip_output_path}

def executar_processo():
    """
    Função principal para executar todo o fluxo de processamento.
    """
    processamento = processar_zip()
    if processamento["status"] == "error":
        return processamento

    substituir_abreviacoes()
    compactacao = compactar_csv()
    
    return {
        "status": "success",
        "message": "Processo finalizado com sucesso.",
        "zip_path": compactacao["zip_path"]
    }

# Executar o processo
resultado = executar_processo()
print(resultado)

