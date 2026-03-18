import sys
import json
import os

# fast_alpr import
from fast_alpr.alpr import ALPR

# Importar el nuevo módulo
from color_detector import detect_color_ai, load_color_model

def main():
    if len(sys.argv) < 2:
        print("Debe pasar una imagen como argumento.")
        return

    image_path = sys.argv[1]
    print(f"📸 Procesando imagen: {image_path}")

    # Detectar placa
    alpr = ALPR()
    results = alpr.predict(image_path)
    print("📋 Resultado ALPR crudo:", results)

    plate = ""
    if results and results[0].ocr and results[0].ocr.text:
        plate = results[0].ocr.text.replace("_", "")

    # Detectar color con IA
    try:
        model = load_color_model()
        color = detect_color_ai(image_path, model)
    except Exception as e:
        print("Error en detección de color:", e)
        color = "desconocido"

    # Resultado final
    print(json.dumps({
        "plate": plate,
        "color": color
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
