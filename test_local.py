# test_local.py
import os
import sys

# --- Importa tus funciones del paquete ---
# Nota: 'preprocess_for_ocr' ya no existe, así que no la importamos.
from equation_ocr.processing.image_utils import load_image
from equation_ocr.ocr.recognition import get_latex_string_from_image
from equation_ocr.latex.renderer import render_latex_to_image

# --- Configuración ---
# Asegúrate de tener una imagen de prueba con este nombre en la raíz
INPUT_FILE = "my-inputs/test_equation.jpg" 
OUTPUT_DIR = "outputs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "final_render.png")

# Crear el directorio de salida si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_test():
    """Ejecuta el pipeline de prueba local."""
    try:
        # --- 1. Cargar imagen ---
        print(f"--- 1. Cargando imagen: {INPUT_FILE} ---")
        # El modelo ONNX espera una imagen BGR (color)
        original_image = load_image(INPUT_FILE)
        print("Imagen cargada exitosamente.")

        # --- 2. Ejecutar OCR ---
        print("\n--- 2. Ejecutando OCR (ONNX) ---")
        # Pasamos la imagen cruda. La clase LatexOCR se encarga 
        # internamente del pre-procesamiento (reescalar, normalizar).
        latex_str = get_latex_string_from_image(original_image)

        if not latex_str:
            print("ERROR: El OCR no devolvió ningún string.")
            return

        print(f"LaTeX detectado: {latex_str}")

        # --- 3. Renderizar LaTeX ---
        print("\n--- 3. Renderizando LaTeX a imagen ---")
        success = render_latex_to_image(latex_str, OUTPUT_FILE)

        if success:
            print(f"\n¡ÉXITO! ✨")
            print(f"Renderizado final guardado en: {OUTPUT_FILE}")
        else:
            print("ERROR: Fallo al renderizar el LaTeX. Revisa el string.")

    except FileNotFoundError as e:
        print(f"\nERROR CRÍTICO: {e}", file=sys.stderr)
        print("Asegúrate de tener los archivos del modelo ('model.onnx', 'vocab.json.gz')")
        print("en la carpeta 'src/equation_ocr/models/'")
        print("Y tu imagen de prueba ('test_equation.png') en la raíz.")
    except Exception as e:
        print(f"\nHA OCURRIDO UN ERROR INESPERADO: {e}", file=sys.stderr)

if __name__ == "__main__":
    run_test()