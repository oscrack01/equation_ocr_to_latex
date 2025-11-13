import os
from setuptools import setup, find_packages

# Función para leer las dependencias desde requirements.txt
def read_requirements():
    """Lee el archivo requirements.txt y devuelve una lista de dependencias."""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if not os.path.exists(requirements_path):
        print(f"Advertencia: No se encontró el archivo 'requirements.txt' en {requirements_path}")
        return []
        
    with open(requirements_path, 'r') as req_file:
        # Filtra líneas vacías y comentarios
        return [
            line.strip() 
            for line in req_file 
            if line.strip() and not line.strip().startswith('#')
        ]

setup(
    # --- Información Básica ---
    name="equation_ocr",
    version="0.1.0",
    description="Pipeline para convertir imágenes de ecuaciones a LaTeX renderizado.",
    author="Tu Nombre",  # Reemplaza esto
    author_email="tu_email@ejemplo.com",  # Reemplaza esto
    url="https_://github.com/oscrack01/equation_ocr_to_latex",  # La URL de tu repo

    # --- Detección de Paquetes ---
    # La parte más importante para la estructura 'src/'
    packages=find_packages(where="src"),
    package_dir={"": "src"},

# --- Inclusión de Archivos No-Python ---
    # ¡NUEVA LÍNEA!
    # Esto le dice a setup.py que lea el archivo MANIFEST.in
    include_package_data=True,
    
    # --- Dependencias ---
    # Lee las dependencias desde requirements.txt
    install_requires=read_requirements(),

    # --- Metadatos Adicionales (Opcional) ---
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Image Recognition",
    ],
    python_requires='>=3.8',
)