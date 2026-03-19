# Park Xpress 🚗

Parking management system built with Next.js 15, Prisma and TypeScript. Handles vehicle entry and exit, cashier management, PDF ticket generation, monthly client packages and notifications via email and Telegram.

---

## Features

- Vehicle entry and exit registration with PDF ticket generation
- Automatic license plate and vehicle color recognition via custom-built models (see section below)
- Cashier management with opening, closing and movement auditing
- Monthly package system for frequent clients
- Dual authentication: custom JWT + NextAuth (Google OAuth)
- Telegram bot for notes, queries and user registration
- Real-time statistics dashboard
- Cron jobs for expiration reminders and expired package cleanup
- Integrated API documentation with Swagger

---

## License Plate and Color Recognition (ALPR)

This is technically the most interesting part of the project. Instead of relying on a third-party service, we built our own Python microservice with two inference models running in parallel: one for the license plate and one for the vehicle color. The microservice is deployed on Railway and the frontend consumes it through a proxy endpoint in Next.js.

### General architecture

```
Device camera (browser)
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
│  │   └── detects bounding box       │
│  └── MobileViT OCR (ONNX)           │
│      └── reads plate text           │
│                                     │
│  Color pipeline                     │
│  ├── Crops central 50% of frame     │
│  ├── Averages RGB pixels            │
│  └── KNN (k=1) → color name        │
└─────────────────────────────────────┘
        ↓
{ "plate": "ABC-123", "color": "red" }
        ↓
Entry form pre-filled
```

### Plate detection

The `fast_alpr` module (which we adapted locally in the project) chains two ONNX models:

1. **Detector** (`DefaultDetector`): uses `open-image-models` with the `yolo-v9-t-384-license-plate-end2end` model. Receives the full frame and returns bounding boxes with a minimum confidence of 0.4.

2. **OCR** (`DefaultOCR`): uses `fast-plate-ocr` with the `global-plates-mobile-vit-v2-model`. Receives the cropped plate in grayscale and returns the text with per-character probabilities. The `_` padding introduced by the model is stripped in post-processing.

The entry point is `main.py`, which exposes a `POST /recognize` endpoint via FastAPI. The image arrives as an `UploadFile`, gets saved to a temporary file, processed, and the temp file is deleted in the `finally` block.

### Color detection

We built our own color pipeline because generic models don't map to Spanish color names, which is what the system needed.

The flow in `color_detector.py`:
- Opens the image with Pillow
- Crops the central 50% of the frame (to avoid background and sky)
- Resizes to 50×50 pixels
- Computes the average RGB across all pixels
- Passes that value to a **KNN classifier with k=1** that returns the nearest color name in RGB space

The model was trained in `train_color_model.py` using a dictionary of ~55 colors with their representative RGB values (the same ones used by the frontend's `colorMap`). It's serialized with pickle as `color_model.pkl` and loaded once when the API starts up.

```python
# Training — train_color_model.py
model = KNeighborsClassifier(n_neighbors=1)
model.fit(X, y)  # X = RGB values, y = color names

# Inference — color_detector.py
avg_color = tuple(np.mean(pixels, axis=0).astype(int))
predicted_color = model.predict([avg_color])[0]
```

Using KNN k=1 on the average RGB is intentional: it's deterministic, has no hyperparameters to tune, and mapping an average color to a name is essentially a nearest-neighbor search in perceptual space. The color dictionary is kept in sync with the frontend's `colorMap`, which guarantees that every name returned by the API always has a visual representation in the UI.

<div align="center">
<img src="./src/front-end/public/media/video_demostration.gif" width="800" height="800" alt="Demo"/>
</div>


### Next.js integration

The proxy at `/api/recognize-plates/route.ts` receives the `FormData` from the browser, forwards it as a `Blob` to the Python microservice, and returns the JSON directly to the client.

In the `useVehicleManagement.ts` hook, the `recognizePlateFromImage` function takes the `File` from the camera, builds the `FormData` and calls the endpoint. On receiving the response, it pre-fills the `plate` and `color` fields in the entry form using `formatPlateInput` to normalize the Costa Rican plate format (e.g. `ABC-123`, `CL-1234`, `AGV-001`).

While the image is being processed, the `InlinePlateLoader` component replaces the plate input with a Lottie animation, giving visual feedback without blocking the rest of the form.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, Tailwind CSS, shadcn/ui |
| Backend | Next.js API Routes, Prisma ORM |
| Database | PostgreSQL |
| Authentication | JWT (jose) + NextAuth v4 |
| PDF | pdf-lib |
| Emails | Nodemailer + Gmail SMTP |
| Bot | Telegram Bot API + axios |
| ALPR microservice | FastAPI + uvicorn (Python) |
| Plate detection | YOLOv9 + MobileViT (ONNX Runtime) |
| Color detection | KNN scikit-learn + RGB average |
| Microservice deploy | Railway |
| Animations | Lottie React |
| State management | TanStack Query v5 |

---

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd src/front-end

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env

# Generate Prisma client
npx prisma generate

# Run in development
npm run dev
```

The `dev` command starts Next.js with Turbopack and the cron job server in parallel via `concurrently`.

### Python microservice (local)

```bash
cd python
pip install -r requirements.txt

# Train color model (first time only)
python train_color_model.py

# Run the API
python main.py
# → http://localhost:8000
```

---

## Environment variables

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

## Folder structure

```
src/
├── app/
│   ├── api/
│   │   ├── recognize-plates/   # Proxy to the ALPR microservice
│   │   ├── vehicles/
│   │   ├── cashier/
│   │   └── ...
│   ├── hooks/
│   │   └── useVehicleManagement.ts   # recognizePlateFromImage()
│   └── parking/
│       └── entry/              # Entry page with integrated camera
├── components/
│   └── InlinePlateLoader.tsx   # Loader during plate detection
│
python/
├── main.py                     # FastAPI app — /recognize endpoint
├── fast_alpr/
│   ├── alpr.py                 # Full detector + OCR pipeline
│   ├── default_detector.py     # YOLOv9 wrapper
│   └── default_ocr.py          # MobileViT OCR wrapper
├── color_detector.py           # KNN-based color detection
├── train_color_model.py        # Script to train and serialize the model
└── color_model.pkl             # Trained model (generated locally)
```

---

## TODOs

- Split large components into separate files
- Remove `console.log` calls from production code
- Implement the Parking Plots view
- Complete the services section (`/service`)
- Improve color model accuracy with real vehicle images

---

## License

Internal use — Park Xpress © 2025
