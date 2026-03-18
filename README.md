# Park Xpress 🚗

Sistema de gestión de parqueos desarrollado con Next.js 15, Prisma y TypeScript. Permite registrar entradas y salidas de vehículos, manejar cajas, emitir tiquetes en PDF, administrar clientes con paquetes mensuales y enviar notificaciones por correo y Telegram.

---

## Características principales

- Registro de ingreso y salida de vehículos con generación de tiquetes PDF
- Reconocimiento automático de placas y color del vehículo mediante modelos propios (ver sección abajo)
- Gestión de cajas con apertura, cierre y auditoría de movimientos
- Sistema de paquetes mensuales para clientes frecuentes
- Autenticación dual: JWT personalizado + NextAuth (Google OAuth)
- Bot de Telegram para notas, consultas y registro de usuarios
- Dashboard con estadísticas en tiempo real
- Cron jobs para recordatorios de vencimiento y limpieza de paquetes expirados
- Documentación de API con Swagger integrado

---

## Reconocimiento de placas y color (ALPR)

Esta es la parte más interesante del proyecto técnicamente. En lugar de depender de un servicio de terceros, construimos un microservicio Python propio con dos modelos de inferencia corriendo en paralelo: uno para la placa y otro para el color del vehículo. El microservicio está desplegado en Railway y el frontend lo consume a través de un endpoint proxy en Next.js.

### Arquitectura general

```
Cámara del dispositivo (browser)
        ↓
useVehicleManagement.ts → recognizePlateFromImage()
        ↓
POST /api/recognize-plates   (Next.js — proxy)
        ↓
POST https://alpr-api-production.up.railway.app/recognize   (FastAPI — Railway)
        ↓
┌─────────────────────────────────────┐
│  ALPR pipeline (fast_alpr)          │
│  ├── YOLOv9 detector (ONNX)         │
│  │   └── detecta bounding box       │
│  └── MobileViT OCR (ONNX)           │
│      └── lee texto de la placa      │
│                                     │
│  Color pipeline                     │
│  ├── Recorta zona central (50%)     │
│  ├── Promedia píxeles RGB           │
│  └── KNN (k=1) → nombre del color  │
└─────────────────────────────────────┘
        ↓
{ "plate": "ABC-123", "color": "rojo" }
        ↓
Formulario de entrada pre-rellenado
```

### Detección de placa

El módulo `fast_alpr` (que adaptamos localmente en el proyecto) encadena dos modelos ONNX:

1. **Detector** (`DefaultDetector`): usa `open-image-models` con el modelo `yolo-v9-t-384-license-plate-end2end`. Recibe el frame completo y devuelve bounding boxes con confianza mínima de 0.4.

2. **OCR** (`DefaultOCR`): usa `fast-plate-ocr` con el modelo `global-plates-mobile-vit-v2-model`. Recibe el recorte de la placa en escala de grises y retorna el texto con probabilidades por carácter. El padding `_` que introduce el modelo se elimina en postprocesamiento.

El punto de entrada es `main.py`, que expone un endpoint `POST /recognize` con FastAPI. La imagen llega como `UploadFile`, se guarda en un archivo temporal, se procesa y el temporal se elimina en el bloque `finally`.

### Detección de color

Para el color construimos nuestro propio pipeline porque los modelos genéricos no mapean a nombres de colores en español, que es lo que necesitaba el sistema.

El flujo en `color_detector.py`:
- Abre la imagen con Pillow
- Recorta el 50% central del frame (para evitar fondo y cielo)
- Redimensiona a 50×50 píxeles
- Calcula el promedio RGB de todos los píxeles
- Pasa ese valor a un clasificador **KNN con k=1** que devuelve el nombre del color más cercano en el espacio RGB

El modelo fue entrenado en `train_color_model.py` con un diccionario de ~55 colores en español con sus valores RGB representativos (los mismos que usa el `colorMap` del frontend). Se serializa con pickle como `color_model.pkl` y se carga una sola vez al arrancar la API.

```python
# Entrenamiento — train_color_model.py
model = KNeighborsClassifier(n_neighbors=1)
model.fit(X, y)  # X = valores RGB, y = nombres en español

# Inferencia — color_detector.py
avg_color = tuple(np.mean(pixels, axis=0).astype(int))
predicted_color = model.predict([avg_color])[0]
```

La decisión de usar KNN k=1 sobre el promedio RGB es intencional: es determinista, sin hiperparámetros que tunear, y la tarea de mapear un color promedio a un nombre es esencialmente una búsqueda del vecino más cercano en el espacio perceptual. El diccionario de colores está sincronizado con el `colorMap` del frontend, lo que garantiza que los nombres retornados por la API siempre tengan representación visual en la UI.

### Integración en Next.js

El proxy en `/api/recognize-plates/route.ts` recibe el `FormData` del browser, lo reenvía como `Blob` al microservicio Python, y retorna el JSON directamente al cliente.

En el hook `useVehicleManagement.ts`, la función `recognizePlateFromImage` toma el `File` de la cámara, construye el `FormData` y llama al endpoint. Al recibir la respuesta, pre-rellena los campos `plate` y `color` del formulario usando `formatPlateInput` para normalizar el formato de placa costarricense (ej: `ABC-123`, `CL-1234`, `AGV-001`).

Mientras la imagen se procesa, el componente `InlinePlateLoader` reemplaza el input de placa con una animación Lottie, dando feedback visual sin bloquear el resto del formulario.

---

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | Next.js 15, React 19, Tailwind CSS, shadcn/ui |
| Backend | Next.js API Routes, Prisma ORM |
| Base de datos | PostgreSQL |
| Autenticación | JWT (jose) + NextAuth v4 |
| PDF | pdf-lib |
| Correos | Nodemailer + Gmail SMTP |
| Bot | Telegram Bot API + axios |
| ALPR microservicio | FastAPI + uvicorn (Python) |
| Detección de placa | YOLOv9 + MobileViT (ONNX Runtime) |
| Detección de color | KNN scikit-learn + promedio RGB |
| Deploy microservicio | Railway |
| Animaciones | Lottie React |
| State management | TanStack Query v5 |

---

## Instalación

```bash
# Clonar el repositorio
git clone <repo-url>
cd src/front-end

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env

# Generar cliente de Prisma
npx prisma generate

# Correr en desarrollo
npm run dev
```

El comando `dev` levanta Next.js con Turbopack y el servidor de cron jobs en paralelo mediante `concurrently`.

### Microservicio Python (local)

```bash
cd python
pip install -r requirements.txt

# Entrenar modelo de color (solo la primera vez)
python train_color_model.py

# Correr la API
python main.py
# → http://localhost:8000
```

---

## Variables de entorno

```env
DATABASE_URL=
JWT_SECRET=
NEXTAUTH_SECRET=
NEXTAUTH_URL=

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

EMAIL_USER=
EMAIL_PASS=
EMAIL_FROM=

TELEGRAM_BOT_TOKEN=
NOTIFICATION_ENDPOINT=
```

---

## Estructura de carpetas relevante

```
src/
├── app/
│   ├── api/
│   │   ├── recognize-plates/   # Proxy al microservicio ALPR
│   │   ├── vehicles/
│   │   ├── cashier/
│   │   └── ...
│   ├── hooks/
│   │   └── useVehicleManagement.ts   # recognizePlateFromImage()
│   └── parking/
│       └── entry/              # Página con cámara integrada
├── components/
│   └── InlinePlateLoader.tsx   # Loader durante detección
│
python/
├── main.py                     # FastAPI app — endpoint /recognize
├── fast_alpr/
│   ├── alpr.py                 # Pipeline completo detector + OCR
│   ├── default_detector.py     # YOLOv9 wrapper
│   └── default_ocr.py          # MobileViT OCR wrapper
├── color_detector.py           # Detección de color con KNN
├── train_color_model.py        # Script para entrenar y serializar el modelo
└── color_model.pkl             # Modelo entrenado (generado localmente)
```

---

## Pendientes / TODOs

- Separar componentes grandes en archivos propios
- Eliminar `console.log` de producción
- Implementar la vista de Parking Plots
- Completar la sección de servicios (`/service`)
- Mejorar accuracy del modelo de color con imágenes reales de vehículos

---

## Licencia

Uso interno — Park Xpress © 2025
