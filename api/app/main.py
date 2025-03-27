from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import os

from app.services.rol_procedimentos import download_rol_procedimentos
from app.services.transformar_dados import executar_processo

app = FastAPI()

@app.get("/")
async def root():
    """
    Endpoint raiz da API.
    """
    return {"message": "API FastAPI rodando!"}

@app.post('/scrapping/rol-procedimentos')
async def download_rol_procedimentos_endpoint(request: Request):
    """
    Endpoint para realizar o download do rol de procedimentos.
    """
    res = download_rol_procedimentos()
    host = request.url.hostname
    port = request.url.port
    zip_file_url = f"http://{host}:{port}/downloads/{os.path.basename(res['zip_file_path'])}"

    return {
        "status": "success",
        "message": "Rol de procedimentos baixado e compactado com sucesso!",
        "file_url": zip_file_url
    }

@app.get('/downloads')
async def list_files():
    """
    Lista os arquivos disponíveis para download.
    """
    files = os.listdir("downloads")
    return {"files": files}

@app.get("/downloads/{file_name}")
async def download_file(file_name: str):
    """
    Faz o download de um arquivo disponível.
    """
    file_path = os.path.join("downloads", file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"status": "error", "message": f"Arquivo {file_name} não encontrado."}

@app.post("/processamento/rol-procedimentos")
async def processar_rol_procedimentos():
    """
    Processa os dados do rol de procedimentos:
    - Extrai dados do PDF
    - Substitui abreviações
    - Gera CSV e compacta em ZIP
    """
    res = executar_processo()
    return res
