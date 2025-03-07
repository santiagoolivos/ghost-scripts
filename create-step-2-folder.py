import os
import shutil

# Directorio de origen donde están los archivos Markdown
source_dir = "./"  # Cambia esto a la ruta de tu carpeta con los archivos

# Directorio de destino donde se copiarán los archivos
destination_dir = "./step-2"

# Asegurar que la carpeta de destino exista
os.makedirs(destination_dir, exist_ok=True)

# Buscar y copiar archivos que terminan en '-step2.md'
for filename in os.listdir(source_dir):
    if filename.endswith("-step2.md"):
        source_path = os.path.join(source_dir, filename)
        destination_path = os.path.join(destination_dir, filename)
        
        # Copiar archivo
        shutil.copy2(source_path, destination_path)
        print(f"Copiado: {filename} → {destination_dir}")

print("✅ Todos los archivos han sido copiados correctamente.")
