import os
import pickle
import numpy as np
from PIL import Image

MODEL_FILENAME = "color_model.pkl"

def load_color_model():
    """Carga el modelo de clasificación de color desde un archivo .pkl"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, MODEL_FILENAME)
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"No se encontró el modelo '{MODEL_FILENAME}'")
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    return model


def detect_color_ai(image_path, model):
    try:
        img = Image.open(image_path).convert("RGB")
        width, height = img.size
        crop_box = (
            int(width * 0.25),
            int(height * 0.25),
            int(width * 0.75),
            int(height * 0.75),
        )
        cropped_img = img.crop(crop_box)
        resized_img = cropped_img.resize((50, 50))

        pixels = np.array(resized_img).reshape(-1, 3)
        avg_color = tuple(np.mean(pixels, axis=0).astype(int))
        print("🎯 Promedio RGB:", avg_color)

        predicted_color = model.predict([avg_color])[0]
        print("🧠 Color IA detectado:", predicted_color)

        return predicted_color
    except Exception as e:
        print("Error detectando color:", e)
        return "desconocido"
