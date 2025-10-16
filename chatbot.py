from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

def extracao(mensagem):
    
    try:
        print("Chamada para a API do Gemini")
        mensagem_usuario = mensagem
        client = genai.Client(api_key=gemini_api_key)

        prompt = client.models.generate_content(
            model="gemini-2.5-flash", contents= f"""
        Sua tarefa é extrair o nome da peça de moto e o modelo da moto a partir de uma frase.
        Responda apenas com um objeto JSON contendo as chaves "peca", "moto" e "ano".
        Se não conseguir identificar um dos tres, retorne um valor nulo para a chave correspondente.

        Exemplo 1:
        Frase: "preciso de uma pastilha de freio da cb 300 ano 2010"
        JSON: {{"peca": "pastilha de freio", "moto": "cb 300", "ano": 2010}}

        Exemplo 2:
        Frase: "quanto custa o filtro de oleo pra fan 250 2020?"
        JSON: {{"peca": "filtro de oleo", "moto": "fan 250", "ano": 2020}}

        Exemplo 3:
        Frase: "tem pneu?"
        JSON: {{"peca": "pneu", "moto": null, "ano": null}}

        Agora, analise a seguinte frase:
        Frase: "{mensagem_usuario}"
        JSON:
        """
        )
        print("Resposta da API do Gemini:")
        
        return prompt.text
    
    except Exception as e:
        return f"Ocorreu um erro ao chamar a API: {e}"
    


mensagem_usuario = input("Informe a peça, modelo e ano da moto:")
resultado = extracao(mensagem_usuario)

print(resultado)
