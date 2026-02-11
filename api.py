from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
# Importa a função que você JÁ CRIOU no outro arquivo
from gerar_quiz import buscar_contexto 

app = FastAPI()

# Configuração para o React conseguir acessar (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, troque '*' pelo endereço do seu site
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define o formato que o React vai mandar (JSON)
class SearchRequest(BaseModel):
    query: str

@app.post("/search-lessons")
def search_lessons(request: SearchRequest):
    print(f"📡 Recebi pedido do React: {request.query}")
    
    # Usa sua lógica pronta!
    resultados = buscar_contexto(request.query)
    
    # Retorna para o React
    return {"results": resultados}

# Para rodar: uvicorn api:app --reload