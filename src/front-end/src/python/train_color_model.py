import pickle
from sklearn.neighbors import KNeighborsClassifier
import numpy as np

# Diccionario de colores extendido con valores RGB aproximados
color_data = {
    "rojo": (255, 0, 0),
    "azul": (0, 0, 255),
    "verde": (0, 255, 0),
    "amarillo": (255, 255, 0),
    "negro": (0, 0, 0),
    "blanco": (255, 255, 255),
    "gris": (128, 128, 128),
    "morado": (128, 0, 128),
    "violeta": (238, 130, 238),
    "naranja": (255, 165, 0),
    "rosa": (255, 192, 203),
    "marrón": (139, 69, 19),
    "café": (139, 69, 19),
    "celeste": (135, 206, 235),
    "turquesa": (64, 224, 208),
    "dorado": (255, 215, 0),
    "plateado": (192, 192, 192),
    "fucsia": (255, 0, 255),
    "coral": (255, 127, 80),
    "salmón": (250, 128, 114),
    "índigo": (75, 0, 130),
    "esmeralda": (46, 204, 113),
    "aqua": (0, 255, 255),
    "cian": (0, 255, 255),
    "lima": (0, 255, 0),
    "oliva": (128, 128, 0),
    "beige": (245, 245, 220),
    "lavanda": (230, 230, 250),
    "mostaza": (218, 165, 32),
    "vino": (128, 0, 32),
    "carmesí": (220, 20, 60),
    "perla": (255, 239, 213),
    "menta": (245, 255, 250),
    "pistacho": (154, 205, 50),
    "arándano": (138, 43, 226),
    "canela": (139, 69, 19),
    "plomo": (112, 128, 144),
    "ámbar": (255, 191, 0),
    "acero": (70, 130, 180),
    "esmeralda_claro": (144, 238, 144),
    "esmeralda_oscuro": (46, 139, 87),
    "gris_claro": (211, 211, 211),
    "gris_oscuro": (169, 169, 169),
    "rojo_oscuro": (139, 0, 0),
    "azul_oscuro": (0, 0, 139),
    "verde_oscuro": (0, 100, 0),
    "naranja_oscuro": (255, 140, 0),
    "rosa_claro": (255, 182, 193),
    "amarillo_claro": (255, 255, 224),
    "chocolate": (210, 105, 30),
    "arena": (245, 222, 179),
    "ocre": (160, 82, 45),
    "carbón": (105, 105, 105),
    "perla_rosada": (255, 228, 225)
}

# Preparar datos
X = np.array(list(color_data.values()))
y = list(color_data.keys())

# Entrenar modelo
from sklearn.neighbors import KNeighborsClassifier
model = KNeighborsClassifier(n_neighbors=1)
model.fit(X, y)

# Guardar modelo    
with open("color_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("✅ Modelo entrenado con todos los colores de colorMap.")
