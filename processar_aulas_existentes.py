import os
import time
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Carrega variáveis
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not api_key or not supabase_url or not supabase_key:
    print("❌ ERRO: Verifique seu arquivo .env - Faltam chaves.")
    exit()

genai.configure(api_key=api_key)
supabase: Client = create_client(supabase_url, supabase_key)

def get_transcript(videoUrl):
    # 1. Extração robusta do ID do vídeo
    video_id = ""
    try:
        if "youtu.be" in videoUrl:
            video_id = videoUrl.split("/")[-1].split("?")[0]
        elif "v=" in videoUrl:
            video_id = videoUrl.split("v=")[1].split("&")[0]
        elif "embed" in videoUrl:
            video_id = videoUrl.split("/")[-1].split("?")[0]
        
        if not video_id:
            return None

        print(f"   🎥 Baixando legenda do ID: {video_id}...")
        
        # 2. TENTATIVA MODERNA (Listar e Escolher)
        # Isso funciona melhor para legendas geradas automaticamente
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Tenta achar nesta ordem de preferência:
        # Português (Brasil), Português (Portugal), Inglês
        transcript = transcript_list.find_transcript(['pt-BR', 'pt', 'en'])
        
        # Baixa os dados
        lista_legendas = transcript.fetch()
        
        # Junta tudo num texto só
        texto_formatado = " ".join([item['text'] for item in lista_legendas])
        return texto_formatado

    except NoTranscriptFound:
        print("   ⚠️ Nenhuma legenda encontrada (nem automática).")
        return None
    except TranscriptsDisabled:
        print("   🚫 Legendas desativadas neste vídeo.")
        return None
    except Exception as e:
        # Se for aquele erro de 'no element found', geralmente é pq não tem nada mesmo
        if "no element found" in str(e):
            print("   ⚠️ Erro de Leitura: O YouTube retornou vazio (provavelmente sem legenda).")
        else:
            print(f"   ❌ Erro técnico: {e}")
        return None

def processar_tudo():
    print("🔄 Conectando ao Supabase...")
    
    # Busca aulas
    response = supabase.table("lessons").select("id, videoUrl, title").execute()
    aulas = response.data

    print(f"📂 Encontradas {len(aulas)} aulas. Iniciando processamento...")

    for aula in aulas:
        aula_id = aula['id']
        video_url = aula.get('videoUrl') or ""
        titulo = aula['title']

        # Correção: Aceita 'youtu.be' ou 'youtube.com'
        if not video_url or ("youtube" not in video_url and "youtu.be" not in video_url):
            print(f"⏩ Aula {aula_id} ignorada (URL inválida).")
            continue

        # Verifica se já existe no banco (para não gastar IA repetida)
        check = supabase.table("aula_embeddings").select("id").eq("lesson_id", aula_id).execute()
        if len(check.data) > 0:
            print(f"⏩ Aula {aula_id} já processada. Pulando.")
            continue

        print(f"\n🧠 Processando Aula {aula_id}: {titulo}")
        
        # Pega o texto
        texto_completo = get_transcript(video_url)
        
        if texto_completo:
            try:
                print("   ⚡ Gerando Embedding (Cérebro da IA)...")
                # Gera o vetor
                embedding_result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=texto_completo,
                    task_type="retrieval_document",
                    title=titulo
                )
                vetor = embedding_result['embedding']

                # Salva no banco
                data = {
                    "lesson_id": aula_id,
                    "content": texto_completo,
                    "embedding": vetor
                }
                
                supabase.table("aula_embeddings").insert(data).execute()
                print("   ✅ SUCESSO! Salvo no banco.")
                
                time.sleep(1) # Pausa leve
                
            except Exception as e:
                print(f"   ❌ Erro ao salvar no Supabase/Gemini: {e}")
        else:
            print("   ⚠️ Pulando aula (sem texto extraído).")

if __name__ == "__main__":
    processar_tudo()