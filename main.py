import uvicorn
import os

if __name__ == "__main__":
    # A Discloud (e outras clouds) fornecem a porta via variável de ambiente.
    # Se não houver, usa a 8080 por defeito.
    port = int(os.environ.get("PORT", 8080))
    
    # Inicia o servidor apontando para o ficheiro 'api' e a instância 'app'
    print(f"🚀 A iniciar servidor na porta {port}...")
    uvicorn.run("api:app", host="0.0.0.0", port=port)