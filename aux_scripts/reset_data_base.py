import sys
import os
import shutil

# Asegura que el microservicio esté en el path para importar settings
sys.path.append(os.getcwd())

from app.core.config import settings

def reset_data_base():
    # 1. Obtener la ruta desde la configuración centralizada
    persist_dir = settings.CHROMA_PERSIST_DIRECTORY
    
    print(f"Checking for existing vector store at: {persist_dir}")
    
    # 2. Validación de seguridad y borrado
    if persist_dir and os.path.exists(persist_dir):
        try:
            print(f"Removing existing vector store data at {persist_dir}...")
            shutil.rmtree(persist_dir)
            print("Cleaned successfully.")
        except Exception as e:
            print(f"Error while deleting directory: {e}")
    else:
        print("No existing vector store found or path is empty.")

if __name__ == "__main__":
    reset_data_base()