### Scheme Setu
Scheme Setu helps users discover relevant welfare schemes from Hinglish input. The pipeline is shared across Telegram and web demo paths.

### Shared Pipeline
`pipeline.py` runs one full turn:
1. Extract fields from transcript
2. Retrieve best matching scheme(s)
3. Check missing prerequisite certificates (income/caste/domicile)
4. Generate eligibility guidance
5. Produce reply audio and a mock filled local HTML form

### Setup
1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill keys.
   - `OPENAI_API_KEY` is primary for mesh calls.
   - `MESH_API_KEY` and `MESH_BASE_URL` are optional fallback.
   - `TELEGRAM_BOT_TOKEN` is optional unless you run `bot.py`.

### Run Browser Demo
```bash
uvicorn server:app --reload
```
Open `http://127.0.0.1:8000` in browser.

### Run Telegram Bot (optional)
```bash
python bot.py
```

### Notes
- Forms are local mock HTML only; no real government form automation.
- Placeholder values are used for Aadhaar and sensitive fields.
