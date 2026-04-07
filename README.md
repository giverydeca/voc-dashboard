<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/1eTREm85ICLpE7RxbQNUl6aSsZikAyx4S

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Create a `.env` (or `.env.local`) file and set your OpenAI API key:

   ```bash
   VITE_OPENAI_API_KEY=sk-xxxx...
   # (optional) override default model
   # Examples: gpt-5.2 / gpt-5.1 / gpt-5-mini
   VITE_OPENAI_MODEL=gpt-5.2
   ```

   Optional tuning knobs:
   ```bash
   # Chunk size controls (characters)
   CSV_CHUNK_CHAR_LIMIT=20000
   CSV_CHUNK_CHAR_LIMIT_MINI=12000
   # Fast mode chunk multiplier (default: 1.2)
   CSV_FAST_CHUNK_MULTIPLIER=1.2
   # Concurrency caps
   MAX_PARALLEL_REQUESTS=24
   PARALLEL_REQUESTS_CAP=64
   # Retry behavior
   OPENAI_MAX_RETRIES=2
   OPENAI_RETRY_BASE_MS=800
   OPENAI_RETRY_MAX_MS=5000
   ```

3. Run the app:
   `npm run dev`
