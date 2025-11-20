import pendulum
import numpy as np
import cv2
import os
import glob # <--- Importante: para buscar archivos
from typing import Dict, List # <--- Para mejor type-hinting
import logging
from airflow.decorators import dag, task

# Importa tus funciones del paquete
from equation_ocr.processing.image_utils import load_image
from equation_ocr.ocr.recognition import get_latex_string_from_image
from equation_ocr.latex.renderer import render_latex_to_image

# Rutas de E/S dentro del contenedor
INPUT_DIR = "/opt/airflow/inputs"
OUTPUT_DIR = "/opt/airflow/outputs"

@dag(
    dag_id="handwritten_equation_to_latex",
    schedule=None,
    start_date=pendulum.today('UTC').add(days=-1),
    catchup=False,
    tags=["ocr", "latex", "mlops", "dynamic"],
)
def dynamic_equation_pipeline():
    """
    Pipeline dinámico para procesar TODAS las imágenes de la carpeta de entrada.

    1. Escanea la carpeta /opt/airflow/inputs.
    2. Para CADA imagen, ejecuta un pipeline de 3 pasos:
       - Guarda la imagen cargada (ej. 'img1_loaded_image.png')
       - Guarda el texto LaTeX (ej. 'img1_latex.txt')
       - Guarda la imagen renderizada (ej. 'img1_rendered.png')
    """

    @task
    def scan_input_directory(input_dir: str) -> List[str]:
        """
        Tarea 1: Escanea la carpeta de entrada y devuelve una lista
        de rutas a todas las imágenes .jpg y .png.
        """
        print(f"Escaneando directorio: {input_dir}")
        # Busca todos los tipos de imagen comunes
        search_paths = [
            os.path.join(input_dir, "*.jpg"),
            os.path.join(input_dir, "*.jpeg"),
            os.path.join(input_dir, "*.png")
        ]
        
        image_paths = []
        for path in search_paths:
            image_paths.extend(glob.glob(path))
            
        if not image_paths:
            raise ValueError(f"No se encontraron imágenes en {input_dir}")
            
        print(f"Se encontraron {len(image_paths)} imágenes: {image_paths}")
        return image_paths

    @task
    def process_one_image(input_path: str) -> Dict[str, str]:
        """
        Tarea 2: Carga UNA imagen, ejecuta el OCR y guarda los
        archivos de salida solicitados (temp y txt).
        
        Devuelve un diccionario con el string de LaTeX y el nombre base
        para la siguiente tarea.
        """
        print(f"Procesando: {input_path}")
        
        # 1. Genera los nombres de archivo dinámicos
        # ej. 'image1.jpg' -> 'image1'
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        
        # 2. Carga la imagen
        image_array = load_image(input_path)

        # 3. [Requisito]: Guarda la imagen cargada (temp)
        temp_path = os.path.join(OUTPUT_DIR, f"{base_name}_loaded_image.png")
        cv2.imwrite(temp_path, image_array)
        print(f"Imagen temporal guardada en: {temp_path}")
        
        # 4. Ejecuta el OCR
        latex_str = get_latex_string_from_image(image_array)
        if not latex_str:
            raise ValueError(f"El OCR no pudo extraer texto de {input_path}")
        
        # 5. [Requisito]: Guarda el archivo .txt
        text_path = os.path.join(OUTPUT_DIR, f"{base_name}_latex.txt")
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(latex_str)
        print(f"Archivo LaTeX TXT guardado en: {text_path}")

        # 6. Pasa el string de LaTeX y el nombre base a la siguiente tarea
        return {
            "latex_string": latex_str,
            "base_name": base_name
        }

    @task
    def render_final_image(ocr_data: Dict[str, str]) -> str:
        """
        Tarea 3: Toma el string de LaTeX y el nombre base
        y renderiza la imagen final.
        Si el LaTeX es inválido, loguea el error pero NO falla la tarea.
        """
        latex_str = ocr_data["latex_string"]
        base_name = ocr_data["base_name"]

        final_path = os.path.join(OUTPUT_DIR, f"{base_name}_rendered.png")

        print(f"Renderizando imagen final en: {final_path}")

        # --- ¡CAMBIO CLAVE AQUÍ! ---
        # Usamos try...except para capturar el ParseSyntaxException

        try:
            # Intentamos renderizar la imagen
            success = render_latex_to_image(latex_str, final_path)

            if not success:
                # Esto es por si la función maneja el error internamente
                logging.warning(f"La función de renderizado devolvió False para: {base_name}")
                return f"Renderizado fallido (devuelto False) para {base_name}"

        except Exception as e:
            # ¡Aquí capturamos el error! (Ej. ParseSyntaxException)
            logging.error(f"FALLO EL RENDERIZADO DE {base_name} DEBIDO A SINTAXIS INVÁLIDA.")
            logging.error(f"Error: {e}")
            logging.error(f"String de LaTeX que falló: {latex_str}")

            # NO HACEMOS 'raise RuntimeError'.
            # Simplemente devolvemos un string diciendo que falló.
            # Como no lanzamos una excepción, Airflow marcará la tarea como 'SUCCESS'.
            return f"Renderizado fallido (Excepción capturada) para {base_name}"

        # Si try/except pasa sin problemas, devuelve la ruta exitosa
        return final_path

    # --- Definición del Flujo Dinámico ---
    
    # 1. Ejecuta la Tarea 1 UNA VEZ para obtener la lista de archivos
    image_paths_list = scan_input_directory(INPUT_DIR)
    
    # 2. Llama a .expand() para ejecutar la Tarea 2 MÚLTIPLES VECES,
    #    una por cada 'input_path' en la lista.
    ocr_results = process_one_image.expand(input_path=image_paths_list)
    
    # 3. Llama a .expand() de nuevo para la Tarea 3,
    #    una por cada resultado de la Tarea 2.
    render_final_image.expand(ocr_data=ocr_results)


# Instancia el DAG
dynamic_equation_pipeline()