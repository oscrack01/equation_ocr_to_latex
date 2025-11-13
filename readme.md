# Equation OCR to LaTeX Pipeline

This project implements a full MLOps pipeline using Docker and Apache Airflow to convert images of mathematical equations into rendered LaTeX images.

The pipeline performs the following steps:
1.  **Extract:** Loads an input image (JPG, PNG) from a directory.
2.  **Transform (OCR):** Uses an ONNX model to perform Optical Character Recognition (OCR) and extract the LaTeX string.
3.  **Load (Render):** Uses Matplotlib (with a LaTeX engine) to render the string back into a clean image.

---

## 🚀 Quickstart Guide

Follow these steps to build and run the entire pipeline on your local machine.

### Prerequisites

* **Git:** [https://git-scm.com/](https://git-scm.com/)
* **Docker Desktop:** [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
    * *After installing, you **must** start Docker Desktop before proceeding.*

---

### 1. Clone the Repository

Clone the project to your local machine:

```bash
git clone [https://github.com/oscrack01/equation_ocr_to_latex.git](https://github.com/oscrack01/equation_ocr_to_latex.git)
cd equation_ocr_to_latex
```

### 2. Manual Setup: Download Models
This repository does not include the ML model files (they are too large for GitHub). You must download them manually.

1. **Create the models folder**:

```bash

# On Windows (PowerShell)
mkdir -p src/equation_ocr/models

# On macOS / Linux
mkdir -p src/equation_ocr/models
```
2. **Download the Model & Vocab**: Download the following two files and place them inside the src/equation_ocr/models/ folder you just created:

- Model File:

    - Download: https://models.arz.ai/ocr_v2.onnx

    - Save As: model.onnx

- Vocabulary File:

    - Download: https://models.arz.ai/ocr_v2.json

    - Save As: keys.json (Note: Do not compress this file)

3. **Prepare Input/Output Folders**
Create the local folders that Airflow will use to read your images and write the results.

```bash

mkdir my-inputs
mkdir outputs
```
Now, place any equation image (e.g., test_equation.jpg) inside the ./my-inputs folder.

4. **Build and Launch Airflow**
This single command builds your custom Docker image, downloads Postgres and Redis, and launches the entire Airflow suite.

    Note: The first build will take several minutes (10-20 min) as it downloads and installs the LaTeX system.

```bash
docker-compose up -d --build
```

5. **Run Your Pipeline!**
Wait about 60 seconds for all services to start.

Open your web browser and go to: http://localhost:8080

Log in with:

**Username**: airflow

**Password**: airflow

You will see the handwritten_equation_to_latex DAG.

Click the toggle switch on the left to turn it On.

Click the Play button (▶️) on the right and select "Trigger DAG".

6. **Check Your Results**
After a few moments, the pipeline will finish (the task squares will turn green).

Go to the ./outputs folder in your project. You will find your rendered image (e.g., rendered_dag.png) inside!