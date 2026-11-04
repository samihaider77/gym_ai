# GymAI Backend Service

FastAPI backend application implementing Modular Monolith Clean Architecture.

---

## 🚀 Local Development Setup

1. **Activate Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   ```

4. **Run Server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Test Health Endpoint**
   ```bash
   curl http://localhost:8000/health
   # Returns: {"status": "healthy"}
   ```
