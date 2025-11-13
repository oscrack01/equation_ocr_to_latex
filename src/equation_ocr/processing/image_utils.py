import cv2
import numpy as np

def load_image(file_path: str) -> np.ndarray:
    """
    Carga una imagen desde una ruta de archivo.
    Siempre la carga como una imagen BGR de 3 canales.
    """
    # ¡CAMBIO AQUÍ! Usa IMREAD_COLOR para forzar 3 canales
    image = cv2.imread(file_path, cv2.IMREAD_COLOR) 
    
    if image is None:
        raise FileNotFoundError(f"No se pudo cargar la imagen en: {file_path}")
        
    print(f"Imagen BGR cargada desde {file_path} (Shape: {image.shape})")
    return image


