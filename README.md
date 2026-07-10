### Scheme Setu
Scheme Setu is a Telegram bot that helps users in India discover relevant government schemes by accepting Hinglish voice notes, converting speech to text, extracting structured facts, matching against real scheme data with RAG, and replying with clear eligibility guidance plus required documents in both text and voice.

### Mesh API Integration
All AI calls are routed through `mesh.py` only. The function `extract_fields()` performs structured information extraction from transcript + prior context (category, income, purpose, state, summary), while `reason_eligibility()` performs final reasoning over extracted facts and RAG-matched schemes. Two calls are used intentionally: extraction is deterministic/structured, and reasoning is narrative/user-facing, which keeps the pipeline more reliable and easier to debug.

### Setup
1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill all keys.
4. Install Google Chrome (required for Selenium form screenshot generation).
5. Run the bot:
   ```bash
   python bot.py
   ```

### Pipeline Overview
When a user sends a voice note, the bot downloads the audio, transcribes it using Voxtral STT, loads prior conversation fields from SQLite memory, extracts updated structured fields through Mesh, retrieves top scheme matches from local ChromaDB, asks Mesh to reason eligibility and required documents, saves the turn in memory, synthesizes a spoken response via ElevenLabs, generates a mock filled application form screenshot with Selenium, and sends text + voice + image back to the user.

### Scheme Sources
The bot uses exactly 10 real schemes sourced from official government portals/program pages, including National Scholarship Portal (NSP), PM-JAY, PMAY, PM YASASVI, NHFDC, Sukanya Samriddhi, NMMS, West Bengal Kanyashree, and West Bengal Swasthya Sathi.

### Notes
- Missing required API keys are surfaced with clear error messages naming the missing environment variable.
- Selenium automation targets only local `file://` `mock_form.html` and never any real government website.