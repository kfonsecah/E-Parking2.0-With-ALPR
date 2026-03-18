from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import tempfile
import shutil
import uvicorn
import os

from fast_alpr.alpr import ALPR
from color_detector import detect_color_ai, load_color_model

app = FastAPI()

# Cargar modelo de color IA una sola vez
color_model = load_color_model()

# Instancia del lector de placas
alpr = ALPR()

@app.post("/recognize")
async def recognize_plate(file: UploadFile = File(...)):
    try:
        # Guardar archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            image_path = temp_file.name

        # Reconocer placa
        results = alpr.predict(image_path)
        plate = ""
        if results and results[0].ocr and results[0].ocr.text:
            plate = results[0].ocr.text.replace("_", "")

        # Detectar color con IA
        color = detect_color_ai(image_path, color_model)

        return {"plate": plate, "color": color}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        # Limpieza del archivo temporal
        if os.path.exists(image_path):
            os.remove(image_path)

# Solo para correr localmente
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
