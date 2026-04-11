#  Inkpick: The Universal Discovery Hub

Inkpick is a hand-drawn, high-performance discovery engine for **Movies**, **Music**, and **Learning**. Designed with a "Sketchbook" aesthetic, it prioritizes tactility and speed, delivering precision recommendations across hundreds of thousands of items without the bloat of modern frameworks.


---

##  Key Features

- ** Universal Hub:** A unified discovery stream blending Cinema, Music, and academic Courses into one seamless experience.
- ** Precision Filtering:** Metadata-level genre filtering (e.g., Bollywood, Sci-Fi, Web Dev) powered by optimized NumPy masking.
- ** Sketchbook Aesthetic:** A custom-built UI featuring hand-drawn strokes, paper textures, and tactile micro-animations.
- ** Sketchy (3D Mascot):** An interactive 3D robot companion that reacts to your discovery journey using `<model-viewer>`.
- ** My Sketchbook:** A personal persistence system to "heart" and save your favorite masterpieces for future reference.

---

##  The Tech Stack

### Backend (The "Masterpiece" Engine)
- **FastAPI:** High-performance Python web framework for the discovery API.
- **NumPy & Pandas:** Vectorized recommendation logic for near-instant search across 87k+ movies and 100k+ songs.
- **SuggestoRegistry:** A dynamic engine management system allowing cross-category expansion.

### Frontend (Tactile UI)
- **Vanilla JavaScript (ES6+):** Zero-framework architecture for lightning-fast interactivity.
- **Vanilla CSS3:** Custom-crafted design system with hand-drawn geometry and paper-texture tokens.
- **Lucide Icons:** Complementary hand-sketched iconography.

---

##  Getting Started

### Prerequisites
- Python 3.10+
- `uv` (recommended) or `pip`

### Local Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/MayankParashar28/Suggesto.git
   cd Suggesto
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   uvicorn main:app --reload
   ```

4. **Access the Hub:**
   Open `http://127.0.0.1:8000` in your browser.

---

## ☁️ Deployment
Suggesto is production-ready and includes a `Procfile` for one-click deployment to **Render** or **Railway**.

---

##  Design Philosophy
Inkpick rejects the sterile, flat design of modern web apps. It embraces the "Sketchbook" philosophy: digital discovery should feel like browsing through a curated notebook of hand-drawn scribbles. Every card, hover, and interaction is designed to feel human, tactile, and alive.

---

*Built with ❤️ for curious minds.*
