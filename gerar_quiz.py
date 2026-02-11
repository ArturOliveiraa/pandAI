import os
import google.generativeai as genai
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega chaves
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def buscar_contexto(pergunta_usuario):
    print(f"🔎 Procurando conteúdo sobre: '{pergunta_usuario}'...")

    try:
        # --- FORÇANDO O TAMANHO 768 ---
        embedding = genai.embed_content(
            model="models/gemini-embedding-001",
            content=pergunta_usuario,
            task_type="retrieval_query",
            output_dimensionality=768  # <--- O SEGREDO: Força o tamanho correto
        )
        vetor_pergunta = embedding['embedding']
        
        # Debug para termos certeza
        print(f"   📏 Tamanho do vetor gerado: {len(vetor_pergunta)}")
        
        # Chama a função no Supabase
        response = supabase.rpc(
            "match_documents",
            {
                "query_embedding": vetor_pergunta,
                "match_threshold": 0.5, 
                "match_count": 3 # Pega 3 trechos para ter mais contexto
            }
        ).execute()

        return response.data
        
    except Exception as e:
        print(f"   ❌ Erro na busca: {e}")
        return []

def gerar_quiz(topico):
    contexto = buscar_contexto(topico)

    if not contexto:
        print("❌ Não encontrei nenhuma aula sobre esse assunto.")
        # Dica: Às vezes a busca é muito estrita, tente palavras-chave mais simples
        return

    # Formata o texto para a IA ler
    try:
        texto_base = "\n\n".join([f"--- TRECHO DE AULA ---\n{item['content']}" for item in contexto])
    except:
        texto_base = str(contexto)
    
    print(f"💡 Encontrei {len(contexto)} trechos relevantes! Gerando Quiz...")

    # Gera o Quiz
    model = genai.GenerativeModel("models/gemini-2.5-flash")
    
    prompt = f"""
    ATUE COMO UM PROFESSOR SÊNIOR.
    Baseado APENAS no contexto abaixo, crie um Quiz Técnico.
    
    CONTEXTO:
    {texto_base}
    
    REGRAS:
    1. Crie 3 perguntas de múltipla escolha (A, B, C).
    2. As perguntas devem ser técnicas e desafiadoras.
    3. Indique a resposta correta e explique o porquê.
    4. Se o contexto falar sobre 'cancelamento', foque nisso. Se falar sobre 'NFCe', foque nisso.
    
    SAÍDA ESPERADA:
    ---
    Pergunta 1: ...
    Opções...
    Resposta: ...
    ---
    """

    try:
        response = model.generate_content(prompt)
        print("\n" + "="*40)
        print(f"🎯 QUIZ GERADO: {topico.upper()}")
        print("="*40)
        print(response.text)
    except Exception as e:
        print(f"❌ Erro ao gerar texto: {e}")

if __name__ == "__main__":
    tema = input("Qual o tema do Quiz? (ex: cancelar venda): ")
    gerar_quiz(tema)