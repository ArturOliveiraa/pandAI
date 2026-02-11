import os
import google.generativeai as genai
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Configurações
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def gerar_e_salvar_embedding(lesson_id, texto_da_aula):
    # 1. Gera o Embedding usando o modelo do Google
    # O modelo 'text-embedding-004' é otimizado para isso
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=texto_da_aula,
        task_type="retrieval_document", # Otimiza para documentos que serão buscados
        title=f"Aula {lesson_id}" # Opcional, ajuda na precisão
    )
    
    vetor = result['embedding'] # Isso é uma lista de 768 números float

    # 2. Salva no Supabase
    data = {
        "lesson_id": lesson_id,
        "content": texto_da_aula, # É bom salvar o texto original junto
        "embedding": vetor
    }
    
    response = supabase.table("aula_embeddings").insert(data).execute()
    print(f"✅ Embedding salvo para a aula {lesson_id}")
    
    gerar_e_salvar_embedding(id_da_aula_no_banco, texto_transcricao)