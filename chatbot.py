from google import genai
import os
from dotenv import load_dotenv
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from PyPDF2 import PdfReader

class mensagem_entrada(BaseModel):
    mensagem: str
    token: str

load_dotenv()

app = FastAPI()

@app.post("/chat/")
def chat_endpoint(mensagem: mensagem_entrada):
    resposta = validacao(mensagem.mensagem)
    token = mensagem.token
    return {"resposta": resposta}

gemini_api_key = os.getenv("GEMINI_API_KEY")

url = os.getenv("URL_API")

def extracao(mensagem):
    
    try:
        print("Chamada para a API do Gemini")
        mensagem_usuario = mensagem
        client = genai.Client(api_key=gemini_api_key)

        prompt = client.models.generate_content(
            model="gemini-2.5-flash", contents= f"""
        Sua tarefa é extrair o nome da peça de moto e o modelo da moto a partir de uma frase.
        Responda apenas com um objeto JSON contendo as chaves "peca", "moto" e "ano", e corrija caso a peca ou o modelo tenha sido escrito errado.
        Se não conseguir identificar um dos tres, retorne um valor nulo para a chave correspondente.

        Exemplo 1:
        Frase: "preciso de uma pastilha de freio da cb 300 ano 2010"
        {{"peca": "pastilha de freio", "moto": "cb 300", "ano": 2010}}

        Exemplo 2:
        Frase: "quanto custa o filtro de oleo pra fan 250 2020?"
        {{"peca": "filtro de oleo", "moto": "fan 250", "ano": 2020}}

        Exemplo 3:
        Frase: "tem pneu?"
        {{"peca": "pneu", "moto": null, "ano": null}}

        Exemplo 4:
        Frase: "quanto custa o retrodisor pra fazer 250 2023?"
        {{"peca": "retrovisor", "moto": "fazer 250", "ano": 2023}}

        Agora, analise a seguinte frase:
        Frase: "{mensagem_usuario}"
        """
        )
        print("Resposta da API do Gemini:")
        
        return prompt.text
    
    except Exception as e:
        return f"Ocorreu um erro ao chamar a API: {e}"
    
def validacao(mensagem):
    print(mensagem)

    frases = mensagem.split(",")
    
    print(frases[0])
    
    if "null" in frases[0]:
        return "Digite o nome da peça que deseja."
    elif "null" in frases[1]:
        return "Digite o modelo da moto."
    elif "null" in frases[2]:
        return "Digite o ano da moto."
    else:
        return True
    
def requisição_peca(mensagem):
    extracao_resultado = extracao(mensagem)

    print("Requisição da peça:")
    if validacao(extracao_resultado) == True:
        pecas = extracao_resultado.split(",")
        peca_nome = pecas[0].split('{')
        print(peca_nome[1])
        # produtos = api_java(peca_nome[1], token)
        # return produtos
        return f"Peça: {peca_nome[1]}"

    else:
        return "Peca invalida"

def api_java(peca, token):
    try:
        headers = {
            # "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        peca_json= {peca}

        response = requests.get(url, headers=headers)


        response.raise_for_status() 


        dados = response.json()

        for produto in dados:
            id_produto = produto['id']
            url_foto = produto['urlFoto']
            url_doc = produto['urlDocumento']
            nome_doc = produto['nomeDocumento']

            # print(f"--- PRODUTO ENCONTRADO ---")
            # print()
            # print(id_produto)
            # print()
            # print(url_foto)
            # print()
            # print(url_doc)

        baixar_arquivo(url_doc, nome_doc)
        tem = buscar_e_apagar_pdf(nome_doc, "PROCURE TRATAMENTO MÉDICO")


        print(dados)    
        print(tem)

        return None


    except requests.exceptions.HTTPError as errh:
        print(f"Erro HTTP: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Erro de Conexão: {errc}")
    except requests.exceptions.Timeout as errt: 
        print(f"Erro de Timeout: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Erro na Requisição: {err}")

def baixar_arquivo(url, nome_arquivo_local):

    try:
        print(f"Baixando '{nome_arquivo_local}' de {url}...")
        
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            with open(nome_arquivo_local, 'wb') as f:
                f.write(response.content)
            print(f"Sucesso! Arquivo salvo como '{nome_arquivo_local}'")
        else:
            print(f"Erro ao baixar! Status HTTP: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")

def buscar_e_apagar_pdf(nome_arquivo_pdf, termo_busca):

    
    paginas_encontradas = []
    termo_busca_lower = termo_busca.lower()

    if not os.path.exists(nome_arquivo_pdf):
        print(f"Erro: Arquivo não encontrado em '{nome_arquivo_pdf}'")
        return paginas_encontradas

    try:
        print(f"Buscando por '{termo_busca}' no arquivo '{nome_arquivo_pdf}'...")
        reader = PdfReader(nome_arquivo_pdf)
        
        for i, page in enumerate(reader.pages):
            texto_da_pagina = page.extract_text()
            
            if texto_da_pagina and termo_busca_lower in texto_da_pagina.lower():
                numero_da_pagina = i + 1
                paginas_encontradas.append(numero_da_pagina)
    
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao ler o PDF: {e}")
    
    finally:
        try:
            os.remove(nome_arquivo_pdf)
            print(f"\nArquivo '{nome_arquivo_pdf}' foi lido e apagado com sucesso.")
        except OSError as e:

            print(f"Erro ao tentar apagar o arquivo '{nome_arquivo_pdf}': {e}")


    if paginas_encontradas:
        return True
    else:
        return False    
    
print(api_java("filtro de oleo", os.getenv("API_KEY")))