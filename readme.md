# 💡 Project: Equation OCR Pipeline (Airflow)

This project implements a data pipeline to convert images of mathematical equations into renderable LaTeX text.

The flow includes image pre-processing, an OCR model (based on ONNX), LaTeX rendering, and a key **Human-in-the-Loop** validation step to collect feedback on the model's accuracy.

## 🗺️ The Pipeline (DAG)

The DAG (`dag_id: equation_ocr_to_latex`) is composed of the following tasks:

1.  **Trigger (Manual):** The pipeline is started manually by providing the path to an input image (e.g., `{"image_path": "/path/to/my/equation.png"}`).
2.  `transform_image`: Takes the original image, applies transformations (filters, resizing), and saves it to a "transformed" folder.
3.  `run_ocr_model`: Loads an ONNX model (based on the Kaggle demo) and extracts the LaTeX *string* from the transformed image.
4.  `render_latex`: Takes the LaTeX *string* and uses `matplotlib` to render it into a new image (the "evaluated equation").
5.  `wait_for_feedback_file`: **The pipeline pauses here.** This task is a `FileSensor` that monitors a directory (`feedback/`) waiting for a file (`feedback_data.json`).
6.  `save_feedback`: Once the feedback file is detected, this task reads it, processes the information (e.g., saves it to a database), and the pipeline completes successfully.

## ⚙️ Setup

### 1. Prerequisites
* Python 3.8+ (with a `venv` virtual environment)
* Apache Airflow (recommend `pip install apache-airflow`)
* An OCR model in `.onnx` format (downloaded from the Kaggle notebook).

### 2. Python Dependencies
Install the necessary libraries found in the DAG:

```bash
# Main framework and sensors
pip install "apache-airflow[sensors]"
pip install pendulum

# Pipeline libraries
pip install pillow       # Or opencv-python, for transformation
pip install onnxruntime  # For the OCR model
pip install matplotlib   # For rendering LaTeX
```

### 3. Environment Configuration
This DAG relies on the local filesystem to pass data between tasks.

A. Create Directories: Ensure you create the folder structure defined in the DAG. The user running Airflow (worker) must have read/write permissions for them.

```bash

# Base path (adjust in the .py if necessary)
BASE_DIR="/tmp/equation_project"

mkdir -p $BASE_DIR
mkdir -p $BASE_DIR/transformed
mkdir -p $BASE_DIR/rendered
mkdir -p $BASE_DIR/feedback
```

B. Place Your Model: Save your .onnx file in an accessible location (e.g., a /models folder in your project) and ensure the path is correctly defined inside the run_ocr_model task.

### 4. Starting Airflow
For local development, the easiest way is to use airflow standalone:

```bash

# Initialize the Airflow database (only the first time)
airflow db init

# Create an admin user
airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.org

# Start the web server and scheduler
airflow standalone

```
Access the interface at http://localhost:8080.

🚀 How to Use the Pipeline
1. Start Airflow and navigate to http://localhost:8080.

2. Enable the DAG: Find equation_ocr_to_latex in the list and toggle the switch on.

3. Trigger the Pipeline:

    * Click on the DAG and press the "Play" (Trigger DAG ▶️) button.

    * Select "Trigger DAG w/ config".

    * In the JSON dialog box, provide the path to your input image:

        ```json

        {
        "image_path": "/full/path/to/your/original_equation.png"
        }
        ```
4. Human Review (Pause):

* The pipeline will run tasks 1-4, and then the wait_for_feedback_file task will enter a "running" (or "up_for_retry") state. This is expected.

* Go to the output folder: BASE_DIR/rendered/ (e.g., /tmp/equation_project/rendered/).

* Check the final_equation.png file to see if the model was correct.

5. Provide Feedback:

* For the pipeline to continue, you must create the file the sensor is waiting for.

* Open a terminal and create the feedback_data.json file with your evaluation:

```bash

# Example of "correct" feedback
echo '{"is_correct": true, "notes": "Looks perfect"}' > /tmp/equation_project/feedback/feedback_data.json

# Example of "incorrect" feedback
echo '{"is_correct": false, "correct_latex": "$\frac{1}{x^2}$"}' > /tmp/equation_project/feedback/feedback_data.json
```

6. Completion:

* Within 30 seconds (the poke_interval), the FileSensor will detect the file.

* The wait_for_feedback_file task will be marked as "success".

* The final save_feedback task will execute, read your JSON, and the pipeline will complete.