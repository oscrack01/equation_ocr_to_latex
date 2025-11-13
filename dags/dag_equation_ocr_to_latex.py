# en dags/dag_equation_ocr_to_latex.py
import pendulum
import numpy as np
import cv2  # <--- Necesitamos importar cv2 aquí
import os
from airflow.decorators import dag, task

# Importa tus funciones
from equation_ocr.processing.image_utils import load_image
from equation_ocr.ocr.recognition import get_latex_string_from_image
from equation_ocr.latex.renderer import render_latex_to_image

# Rutas de E/S dentro del contenedor
INPUT_IMAGE_PATH = "/opt/airflow/inputs/test_equation.jpg"
TEMP_IMAGE_PATH = "/opt/airflow/outputs/temp_image.png" # Archivo intermedio
FINAL_IMAGE_PATH = "/opt/airflow/outputs/rendered_dag.png"

@dag(
    dag_id="handwritten_equation_to_latex",
    schedule=None,
    start_date=pendulum.today('UTC').add(days=-1),
    catchup=False,
    tags=["ocr", "latex", "mlops"],
)
def equation_pipeline():
    """
    Pipeline para transformar una imagen de ecuación.
    Usa un archivo intermedio para pasar datos de imagen entre tareas.
    """

    @task
    def extract_and_save(input_path: str, output_path: str) -> str:
        """
        Tarea 1: Carga la imagen de entrada, la guarda en una ruta
        temporal y devuelve esa ruta.
        """
        print(f"Cargando imagen desde: {input_path}")
        image_array = load_image(input_path)
        
        # Asegura que el directorio de salida exista
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Guarda la imagen en la ruta temporal
        print(f"Guardando imagen temporal en: {output_path}")
        cv2.imwrite(output_path, image_array)
        
        # Devuelve la ruta (un string), que JSON sí puede manejar
        return output_path

    @task
    def ocr_to_latex(temp_image_path: str) -> str:
        """
        Tarea 2: Recibe la RUTA de la imagen temporal, la carga,
        ejecuta el OCR y devuelve el string de LaTeX.
        """
        print(f"Cargando imagen temporal desde: {temp_image_path}")
        # Carga la imagen desde la ruta que nos pasó la Tarea 1
        image_array = load_image(temp_image_path)
        
        print("Ejecutando OCR sobre la imagen...")
        latex_str = get_latex_string_from_image(image_array)
        
        if not latex_str:
            raise ValueError("El OCR no pudo extraer texto.")
        
        return latex_str

    @task
    def latex_to_render(latex_string: str, final_output_path: str) -> str:
        """
        Tarea 3: Recibe el string de LaTeX y lo renderiza
        en la ruta de salida final.
        """
        print(f"Renderizando LaTeX en: {final_output_path}")
        success = render_latex_to_image(latex_string, final_output_path)
        if not success:
            raise RuntimeError(f"Fallo el renderizado de LaTeX para: {latex_string}")
        return final_output_path

    # --- Definición del flujo ---
    # 1. Tarea 1 toma la entrada y guarda un archivo temporal
    temp_path = extract_and_save(INPUT_IMAGE_PATH, TEMP_IMAGE_PATH)
    
    # 2. Tarea 2 usa la ruta del archivo temporal
    latex_result = ocr_to_latex(temp_path)
    
    # 3. Tarea 3 usa el string de LaTeX
    latex_to_render(latex_result, FINAL_IMAGE_PATH)

# Instancia el DAG
equation_pipeline()