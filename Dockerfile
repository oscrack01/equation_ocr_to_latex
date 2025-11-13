# Usa una imagen base de Airflow
FROM apache/airflow:2.8.0

# Instala dependencias del sistema
USER root
RUN apt-get update -yqq && apt-get install -yqq --no-install-recommends \
    # Dependencias de LaTeX (versión ligera)
    texlive-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    # Dependencias de OpenCV
    libopencv-dev \
    # ¡NUEVO! Dependencias de Matplotlib para renderizar fuentes
    fontconfig \
    libfreetype6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
USER airflow

# Copia e instala tus dependencias de Python
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

# Copia tu código fuente y lo instala
# (Gracias a MANIFEST.in y setup.py, esto copiará
# e instalará los archivos .py, .onnx y .json.gz)
# 1. Cambia a root para copiar tus archivos de código
USER root
COPY src /opt/airflow/src

# 2. Vuelve al usuario airflow para todo lo demás
USER airflow

# 3. ¡LA CLAVE! Añade tu carpeta 'src' directamente al PYTHONPATH
#    Ahora Python sabrá buscar 'equation_ocr' dentro de /opt/airflow/src
ENV PYTHONPATH="/opt/airflow/src:${PYTHONPATH}"