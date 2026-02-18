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
                "match_threshold": 0.80, 
                "match_count": 6
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
ATUE COMO UM PROFESSOR SÊNIOR ESPECIALISTA NO TEMA DO CONTEXTO.

OBJETIVO:
Gerar um Quiz Técnico AVANÇADO com base EXCLUSIVAMENTE no conteúdo fornecido no CONTEXTO.

CONTEXTO:
{texto_base}

INSTRUÇÕES OBRIGATÓRIAS:

1. Utilize SOMENTE informações presentes no CONTEXTO.
2. NÃO inclua conhecimentos externos, suposições ou exemplos não mencionados.
3. Se o CONTEXTO mencionar:
   - "cancelamento" → foque prioritariamente em regras, prazos, validações, impactos e exceções.
   - "NFCe" → foque em regras técnicas, obrigatoriedades, rejeições, contingências e validações fiscais.
4. As perguntas devem ser técnicas, específicas e desafiadoras.
5. Evite perguntas conceituais genéricas.
6. Crie alternativas plausíveis (distratores tecnicamente coerentes).
7. Apenas UMA alternativa deve estar correta.

FORMATO DE SAÍDA (OBRIGATÓRIO):

---
Pergunta 1:
Enunciado técnico detalhado.

A) ...
B) ...
C) ...
D) ...
E) ...

Resposta Correta: X

Explicação Técnica:
Explique detalhadamente o motivo da alternativa correta e por que as demais estão incorretas.

---
Pergunta 2:
...

---
Pergunta 3:
...
---

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
