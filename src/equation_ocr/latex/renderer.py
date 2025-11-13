import matplotlib.pyplot as plt
import os

def render_latex_to_image(latex_str: str, output_path: str) -> bool:
    """
    Renderiza un string de LaTeX a un archivo de imagen (PNG).
    Devuelve True si tuvo éxito, False si falló.
    """
    print(f"Renderizando LaTeX en: {output_path}")
    
    # Asegura que el string esté en modo matemático de LaTeX
    # Matplotlib lo necesita para interpretarlo
    formatted_str = f"${latex_str}$"
    
    # Asegura que el directorio de salida exista
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Crea una figura y un eje
        fig = plt.figure(figsize=(10, 2)) # Tamaño inicial (se ajustará)
        ax = fig.add_subplot(111)
        
        # Deshabilita los ejes y el marco
        ax.axis('off')
        
        # Renderiza el texto en el centro
        ax.text(0.5, 0.5, formatted_str, size=20, ha='center', va='center')
        
        # Guarda la figura, ajustando el borde (bbox_inches='tight')
        # y con fondo transparente (transparent=True)
        plt.savefig(
            output_path, 
            bbox_inches='tight', 
            dpi=300, 
            transparent=True
        )
        plt.close(fig) # Cierra la figura para liberar memoria
        
        print("Renderizado completado.")
        return True
    
    except Exception as e:
        print(f"Error al renderizar LaTeX: {e}")
        # Esto puede pasar si el LaTeX está malformado
        return False