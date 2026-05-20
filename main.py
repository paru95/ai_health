import os, io
import PIL.Image
from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
app = FastAPI()

# Enable connection from frontend
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Initialize Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Persistent chat history
chat_history = []

# System Instruction to define the "Nexus" persona
NEXUS_SYSTEM_INSTRUCTION = """
You are the AI Health Nexus Core, a professional clinical decision support system. 
Your goal is to provide evidence-based health analysis.
Rules:
1. Always include a 'Confidence Score' (0-100%).
2. If an image is provided, analyze it for clinical markers (redness, inflammation, symmetry).
3. Use a structured format: [Analysis], [Triage Level: Low/Medium/High/Emergency], [Suggested Next Steps].
4. Always end with a medical disclaimer: "Nexus is an AI assistant, not a doctor. Consult a professional for diagnosis."
5. Be concise and factual. Do not use conversational 'fluff'.
"""

@app.post("/chat")
async def chat_endpoint(message: str = Form(""), image: UploadFile = File(None)):
    async def stream_response():
        global chat_history
        try:
            content_parts = []
            
            # 1. Handle Text Input
            if message:
                content_parts.append(types.Part.from_text(text=message))

            # 2. Handle Image Input (Medical Imaging / Photos)
            if image:
                img_bytes = await image.read()
                content_parts.append(
                    types.Part.from_bytes(
                        data=img_bytes, 
                        mime_type=image.content_type
                    )
                )

            # Update history with user input
            chat_history.append({"role": "user", "parts": content_parts})

            # 3. Call Gemini 2.5 Flash with clinical optimizations
            response = await client.aio.models.generate_content_stream(
                model="gemini-2.5-flash", 
                contents=chat_history,
                config=types.GenerateContentConfig(
                    system_instruction=NEXUS_SYSTEM_INSTRUCTION,
                    temperature=0.2,  # Maximum factual precision
                    top_p=0.8,        # Focus on high-probability medical outcomes
                    # Uncomment below to enable real-time 2026 web grounding
                    # tools=[types.Tool(google_search=types.GoogleSearch())] 
                )
            )

            full_ai_response = ""
            async for chunk in response:
                if chunk.text:
                    full_ai_response += chunk.text
                    yield chunk.text
            
            # Save final response to history
            chat_history.append({"role": "model", "parts": [types.Part.from_text(text=full_ai_response)]})
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                yield "⚠️ Nexus Alert: Rate limit reached. The system is cooling down."
            else:
                yield f"⚠️ Nexus System Error: {error_msg}"

    return StreamingResponse(stream_response(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    # Keeping your port 8001 as per your original setup
    uvicorn.run(app, host="127.0.0.1", port=8001)