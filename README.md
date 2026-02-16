 FRIDAY: The Iron Man AI Agent
High-performance, real-time voice assistant powered by LiveKit and Gemini 2.5. Just like the movies
pip install livekit livekit-agents livekit-plugins-openai livekit-plugins-silero livekit-plugins-google livekit-plugins-noise-cancellation python-dotenv aiohttp requests pywhatkit duckduckgo-search mem0ai
 Configuration
Create a .env file in the root folder:

Code snippet
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
GOOGLE_API_KEY=your_gemini_key
GMAIL_SENDER=your_email@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
Security Note: > * Gmail: Requires a 16-character App Password (Security Key).

WhatsApp: Free via pywhatkit automation. Ensure you're logged into WhatsApp Web in your browser.


Launch the agent:PowerShell python agent.py dev


built using livekit and gemini API
