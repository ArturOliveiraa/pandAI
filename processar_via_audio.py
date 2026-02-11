import os
import time
import glob
import google.generativeai as genai
from yt_dlp import YoutubeDL
from supabase import create_client, Client
from dotenv import load_dotenv

# 1. Configurações
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Conexão Supabase
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def baixar_audio(video_url, id_aula):
    output_name = f"audio_aula_{id_aula}"
    for f in glob.glob(f"{output_name}*"):
        try: os.remove(f)
        except: pass

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio', 
        'outtmpl': output_name,
        'quiet': True,
        'noplaylist': True,
    }

    try:
        print(f"   🎧 Baixando áudio...")
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        arquivos = glob.glob(f"{output_name}*")
        return arquivos[0] if arquivos else None
    except Exception as e:
        print(f"   ❌ Erro no download: {e}")
        return None

def processar_tudo_com_audio():
    print("🔄 Conectando ao Supabase...")
    response = supabase.table("lessons").select("id, videoUrl, title").execute()
    aulas = response.data
    print(f"📂 Encontradas {len(aulas)} aulas.")

    for aula in aulas:
        aula_id = aula['id']
        video_url = aula.get('videoUrl')
        titulo = aula['title']

        if not video_url or ("youtube" not in video_url and "youtu.be" not in video_url):
            continue

        # Verifica se já processou
        check = supabase.table("aula_embeddings").select("id").eq("lesson_id", aula_id).execute()
        if len(check.data) > 0:
            print(f"⏩ Aula {aula_id} já processada. Pulando.")
            continue

        print(f"\n🧠 Processando Aula {aula_id}: {titulo}")
        arquivo_path = baixar_audio(video_url, aula_id)
        
        if arquivo_path:
            try:
                print("   ☁️ Enviando áudio para o Gemini...")
                audio_file = genai.upload_file(path=arquivo_path, mime_type="audio/mp4")
                
                while audio_file.state.name == "PROCESSING":
                    time.sleep(2)
                    audio_file = genai.get_file(audio_file.name)

                print("   ⚡ Transcrevendo (usando Flash Lite)...")
                
                # --- MUDANÇA AQUI: Usando o alias de maior cota da sua lista ---
                model = genai.GenerativeModel("models/gemini-2.5-flash")
                prompt = "Transcreva este áudio técnico detalhadamente. Ignore músicas de intro."
                
                # Loop de tentativa com espera em caso de 429
                sucesso = False
                while not sucesso:
                    try:
                        response_ia = model.generate_content([prompt, audio_file])
                        texto_transcrito = response_ia.text
                        
                        embedding_result = genai.embed_content(
                            model="models/gemini-embedding-001", 
                            content=texto_transcrito,
                            task_type="retrieval_document",
                            output_dimensionality=768
                        )
                        
                        supabase.table("aula_embeddings").insert({
                            "lesson_id": aula_id,
                            "content": texto_transcrito,
                            "embedding": embedding_result['embedding']
                        }).execute()
                        
                        print("   ✅ SUCESSO!")
                        sucesso = True
                    except Exception as e:
                        if "429" in str(e):
                            print("   ⏳ Cota de tokens atingida. Esperando 60 segundos...")
                            time.sleep(60)
                        else:
                            print(f"   ❌ Erro na IA: {e}")
                            break

                try:
                    os.remove(arquivo_path)
                    audio_file.delete()
                except: pass
                
                # Pausa maior para não estressar a API
                print("   ☕ Pausa de 45s para respirar...")
                time.sleep(45)

            except Exception as e:
                print(f"   ❌ Erro geral: {e}")
        else:
            print("   ⚠️ Erro ao baixar áudio.")

if __name__ == "__main__":
    processar_tudo_com_audio()