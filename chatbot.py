from google.genai import Client
import os
from dotenv import load_dotenv
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import io

class mensagem_entrada(BaseModel):
    mensagem: str
    token: str

load_dotenv()

app = FastAPI()

origins = [
    "http://localhost:5173",
    "https://startup-vanguard.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # origens permitidas
    allow_credentials=True,
    allow_methods=["*"],            # todos os métodos (GET, POST, etc)
    allow_headers=["*"],            # todos os headers
)

@app.post("/chat/")
def chat_endpoint(mensagem: mensagem_entrada):
    resposta = chamada(mensagem.mensagem, mensagem.token)
    return {"resposta": resposta}

gemini_api_key = os.getenv("GEMINI_API_KEY")

url = os.getenv("URL_API")

def chamada(mensagem, token):

    requisitar = requisição_peca(mensagem, token)

    return requisitar

def extracao(mensagem):
    
    try:
        print("Chamada para a API do Gemini")
        mensagem_usuario = mensagem
        client = Client(api_key=gemini_api_key)

        prompt = client.models.generate_content(
            model="gemini-2.5-flash", contents= f"""
            Sua tarefa é extrair o nome da peça de moto e o "modelo com ano" da moto a partir de uma frase.
            REGRAS:
            1.  Extraia a "peca" e o "modelo_ano" (que é a combinação da moto e do ano).
            2.  Corrija erros de ortografia óbvios (ex: "retrodisor" -> "retrovisor").
            3.  Se a "peca" ou o "modelo_ano" não forem encontrados, use o valor `null` para a chave correspondente.
            4.  Sua saída deve ser **EXCLUSIVAMENTE** um objeto JSON válido.
            5.  NÃO inclua "json", markdown (```), explicações ou qualquer outro texto antes ou depois do objeto JSON.

            Exemplo 1:
            Frase: "preciso de uma pastilha de freio da cb 300 ano 2010"
            {{"peca": "pastilha de freio", "modelo_ano": "cb 300 2010"}}

            Exemplo 2:
            Frase: "quanto custa o filtro de oleo pra fan 250 2020?"
            {{"peca": "filtro de oleo", "modelo_ano": "fan 250 2020"}}

            Exemplo 3:
            Frase: "tem pneu?"
            {{"peca": "pneu", "modelo_ano": "null"}}

            Exemplo 4:
            Frase: "quanto custa o retrodisor pra fazer 250 2023?"
            {{"peca": "retrovisor", "modelo_ano": "fazer 250 2023"}}

            Exemplo 5:
            Frase: "guidão da titan 150"
            {{"peca": "guidão", "modelo_ano": "titan 150"}}

            Analise a frase abaixo e retorne **SOMENTE** o JSON:
            Frase: "{mensagem_usuario}"
            """
        )
        print("Resposta da API do Gemini:")
        
        return prompt.text
    
    except Exception as e:
        return f"Ocorreu um erro ao chamar a API: {e}"
    
def validacao(peca):

    if not peca or peca == "null":
        return "Digite o nome da peça que deseja."
    else:
        return True

def requisição_peca(mensagem , token):
    json_resposta = extracao(mensagem)

    peca, modelo_ano = separar(json_resposta)

    print(f"Requisição da peça: Peça='{peca}', Modelo='{modelo_ano}'")

    resultado_validacao = validacao(peca)

    if resultado_validacao is not True:
        return resultado_validacao
    
    print(f"Buscando API Java por: {peca}")

    produtos = api_java(peca, modelo_ano, token)

    return produtos

def api_java(peca, modelo, token):
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }

        peca_json= {"nome": peca}

        response = requests.get(url, headers=headers, params=peca_json) 

        response.raise_for_status() 

        dados = response.json()

        produtos_compativeis = []

        for produto in dados:
            id_produto = produto['id']
            url_doc = produto['urlDocumento']
            
            salvo = verificar_texto(url_doc, peca, modelo)
            
            print(f"--- PRODUTO ENCONTRADO (ID: {id_produto}) ---")
            
            resultado_verificacao = str(salvo).strip() 
            print(f"Resultado da Verificação: {resultado_verificacao}")

            if resultado_verificacao == "True":
                print(f"Produto {id_produto} é compatível. Adicionando.")

                produtos_compativeis.append(produto)
            else:
                print(f"Produto {id_produto} NÃO é compatível ou falhou na verificação.")

        
        return produtos_compativeis

    except requests.exceptions.HTTPError as errh:
        print(f"Erro HTTP: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Erro de Conexão: {errc}")
    except requests.exceptions.Timeout as errt: 
        print(f"Erro de Timeout: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Erro na Requisição: {err}")

def verificar_texto(url_doc, peca, modelo):
    try:

        if not url_doc:
            print("URL do documento está vazia. Retornando False.")
            return "False"
        
        client = Client(api_key=gemini_api_key)
        long_context_pdf_path = url_doc
        pdf_response = requests.get(long_context_pdf_path)
        pdf_response.raise_for_status() 
        doc_io = io.BytesIO(pdf_response.content)

        sample_doc = client.files.upload(
            file=doc_io,
            config=dict(
                mime_type='application/pdf')
        )

        prompt = contents= f"""
            ### FUNÇÃO ###
            Você é um assistente de verificação de compatibilidade de {peca} de moto.

            ### OBJETIVO ###
            Seu objetivo é ler um documento e uma CONSULTA para determinar se uma peça é compatível com um veículo específico (identificado pelo modelo e ano).

            ### REGRAS DE SAÍDA ###
            1.  Sua resposta DEVE ser **APENAS** a palavra `True` ou `False`.

            2.  Responda `True` SE:
                * (a) O CONTEXTO confirmar explicitamente que a peça é compatível com o {modelo} fornecido na CONSULTA;
                * OU (b) O CONTEXTO indicar que a peça é "universal".

            3.  Responda `False` SE:
                * (a) O CONTEXTO confirmar explicitamente a incompatibilidade com o {modelo};
                * OU (b) A compatibilidade não puder ser determinada (informação ausente) E a peça não for universal.

            4.  Não inclua nenhuma explicação, saudação ou texto adicional.
            """

        response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[sample_doc, prompt])
        return response.text
    
    except Exception as e:
        return f"Ocorreu um erro ao verificar o texto no PDF: {e}"
    
def separar(json_string):

    try:
        data = json.loads(json_string)
        peca = data.get("peca", "null")
        modelo_ano = data.get("modelo_ano", "null")

        return peca, modelo_ano
    
    except json.JSONDecodeError:
        print(f"Erro: A IA não retornou um JSON válido. Resposta: {json_string}")
        return "null", "null"
    

