import os
import gzip
import json
import numpy as np
import cv2
import onnxruntime as ort

# --- Configuración de Rutas (Robusto) ---
# Esto encuentra la ruta del directorio actual (src/equation_ocr/ocr)
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Sube un nivel (a src/equation_ocr) y luego entra a 'models'
_MODEL_DIR = os.path.join(_CURRENT_DIR, "..", "models")
MODEL_PATH = os.path.join(_MODEL_DIR, "model.onnx")
VOCAB_PATH = os.path.join(_MODEL_DIR, "vocab.json.gz")


class LatexOCR:
    """
    Clase para encapsular el modelo ONNX de OCR de LaTeX.
    Adaptado del notebook de Kaggle.
    """
    def __init__(self, model_path: str = MODEL_PATH, vocab_path: str = VOCAB_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Archivo de modelo no encontrado en: {model_path}\n"
                "Asegúrate de descargar 'model.onnx' y 'vocab.json.gz' "
                "del dataset de Kaggle 'Latex OCR ONNX Model' y "
                "colocarlos en 'src/equation_ocr/models/'"
            )
        
        # Inicializa la sesión de ONNX Runtime
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        
        # Carga el vocabulario
        with gzip.open(vocab_path, "rt", encoding="utf-8") as f:
            self.vocab_data = json.load(f)
        
        # ¡CORRECCIÓN! El vocabulario es un 'dict', no una 'list'.
        # self.vocab_data es algo como: {"0": "<PAD>", "1": "<START>", ...}
        
        # Convertimos las claves (keys) de string a entero
        # y este es nuestro mapa id_to_token
        self.id_to_token = {int(k): v for k, v in self.vocab_data.items()}
        
        # Creamos el mapa inverso (token_to_id)
        self.token_to_id = {v: k for k, v in self.id_to_token.items()}
        
        # Configuración del modelo (basado en el notebook)
        self.img_size = (1024, 192) # (Ancho, Alto) - ¡Ojo! cv2 usa (w, h)
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def pre_process(self, img: np.ndarray) -> np.ndarray:
        """
        Pre-procesa la imagen para el modelo ONNX.
        Debe escalar y rellenar (padding) para mantener la relación de aspecto.
        El modelo espera (1, 192, 1024, 3).
        """
        # 1. Asegurarse que es BGR (3 canales)
        if len(img.shape) == 2: # Si es gris, convertir a BGR
            img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4: # Si tiene Alfa, quitarlo
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        else:
            img_bgr = img # Ya es BGR

        # 2. Escalar y Rellenar (Padding) para mantener la relación de aspecto
        (h, w, _) = img_bgr.shape
        # El tamaño que el modelo espera (Alto, Ancho)
        target_h, target_w = self.img_size[1], self.img_size[0] # (192, 1024)

        # Crear un canvas blanco (color 255).
        # El modelo fue entrenado con fondo blanco, por eso normalizamos a 1.0 (blanco).
        canvas = np.ones((target_h, target_w, 3), dtype=np.uint8) * 255
        
        # Calcular la nueva escala (cuál es la restricción, alto o ancho)
        scale = min(target_w / w, target_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Redimensionar la imagen original con la escala correcta
        resized_img = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Calcular dónde pegarla (centrada)
        x_offset = (target_w - new_w) // 2
        y_offset = (target_h - new_h) // 2
        
        # Pegar la imagen en el centro del canvas blanco
        canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized_img

        # 3. Normalizar el canvas completo (0 a 1)
        img_normalized = canvas.astype(np.float32) / 255.0

        # 4. Añadir dimensión de Batch
        # (192, 1024, 3) -> (1, 192, 1024, 3)
        img_final = img_normalized[np.newaxis, :, :, :]
        return img_final

    def post_process(self, logits: np.ndarray) -> str:
        """
        Convierte los logits del modelo en un string de LaTeX.
        """
        # 1. Obtener la lista de IDs predichos
        # (Equivalente a 'res' en el notebook)
        predicted_ids = np.argmax(logits[0], axis=-1)
        
        tokens = []
        
        # 2. Iterar sobre cada ID (la lógica de la línea clave)
        for token_id in predicted_ids:
            
            # Lógica del 'if x != 0'
            # El ID 0 es un token de padding/ignorar
            if token_id == 0:
                continue # Simplemente lo saltamos

            # Lógica del 'str(x - 1)'
            # ¡AQUÍ ESTÁ LA CORRECCIÓN!
            # Restamos 1 para alinear el ID del modelo
            # con el ID del vocabulario (keys.json)
            lookup_id = token_id - 1
            
            # 3. Buscar el token en nuestro mapa
            token = self.id_to_token.get(lookup_id, "<UNK>")

            # 4. Filtrar tokens especiales (lógica nuestra, que es mejor)
            if token == "<END>":
                break
            if token == "<PAD>" or token == "<START>":
                continue
            
            tokens.append(token)
            
        # 5. Unir sin espacios
        return "".join(tokens)

    def __call__(self, img: np.ndarray) -> str:
        """
        Ejecuta el pipeline completo: pre-proceso, inferencia y post-proceso.
        """
        # 1. Pre-procesar
        processed_img = self.pre_process(img)
        
        # 2. Inferencia
        inputs = {self.input_name: processed_img}
        logits = self.session.run([self.output_name], inputs)[0]
        
        # 3. Post-procesar
        latex_str = self.post_process(logits)
        return latex_str

# --- Interfaz de Función para el DAG ---

# Creamos una instancia global del modelo.
# De esta forma, el modelo se carga UNA SOLA VEZ cuando el worker de Airflow
# importa este archivo, no en cada ejecución de la tarea.
try:
    _MODEL_INSTANCE = LatexOCR()
except FileNotFoundError as e:
    print(f"Error al inicializar el modelo: {e}")
    _MODEL_INSTANCE = None

def get_latex_string_from_image(image: np.ndarray) -> str:
    """
    Función "wrapper" que el DAG de Airflow llamará.
    Utiliza la instancia global del modelo de OCR.
    
    Toma una imagen (array de numpy BGR) y devuelve el string de LaTeX.
    """
    if _MODEL_INSTANCE is None:
        raise RuntimeError(
            "La instancia del modelo OCR no pudo ser cargada. "
            "Revisa los logs y asegúrate de que los archivos del modelo "
            "existen en 'src/equation_ocr/models/'"
        )
        
    print("Iniciando reconocimiento OCR con ONNX...")
    
    try:
        latex_str = _MODEL_INSTANCE(image)
        if not latex_str:
            print("OCR no pudo detectar ningún string de LaTeX.")
            return ""
        
        print(f"String de LaTeX detectado: {latex_str}")
        return latex_str
        
    except Exception as e:
        print(f"Error durante la inferencia de ONNX: {e}")
        return ""