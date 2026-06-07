import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai
from google.genai import types

# 1. Import and run load_dotenv
from dotenv import load_dotenv
load_dotenv() 

# 2. Python will now automatically read GEMINI_API_KEY and SSL_CERT_FILE from your .env file!
app = FastAPI(title="TradeConnect BD-DE")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)


TRADE_SYSTEM_PROMPT = """You are an expert trade advisor specializing in Bangladesh-Germany bilateral commerce.
Bangladesh-Germany bilateral trade was USD 9.81 billion in 2024.
Germany is Bangladesh's second-largest export destination (10.96% of total exports).
Key trade flows:
- Bangladesh to Germany: textiles (90%+ of exports), pharmaceuticals, leather goods, footwear
- Germany to Bangladesh: machinery ($241M), medical/optical apparatus ($68M), electronics ($62M), chemicals ($46M), food products ($16M)

When a user describes a trade they want to make, provide:
1. Recommended product categories with estimated HS code ranges
2. Key compliance and regulatory considerations (EU/Bangladesh regulations)
3. Cost optimization suggestions
4. Similar successful trade patterns

Format your response as structured JSON with keys: product_categories, compliance_notes, cost_optimization, trade_patterns."""

from pydantic import BaseModel

# Describe the exact JSON keys we want Gemini to return
class GeminiTradeResponse(BaseModel):
    product_categories: str
    compliance_notes: str
    cost_optimization: str
    trade_patterns: str

# Define the shape of incoming trade queries
class TradeQuery(BaseModel):
    query: str
    direction: str = "bd_to_de"

# Define the shape of outgoing recommendations
class TradeRecommendation(BaseModel):
    query: str
    direction: str
    recommendation: str


@app.post("/recommend", response_model=TradeRecommendation)
async def get_recommendation(trade_query: TradeQuery):
    # Determine human-readable direction label
    direction_label = (
        "Bangladesh to Germany"
        if trade_query.direction == "bd_to_de"
        else "Germany to Bangladesh"
    )
    # Build the prompt that gets sent to Gemini
    user_prompt = f"Trade direction: {direction_label}\nUser query: {trade_query.query}"

    # Call Gemini 2.5 Flash with the trade system prompt
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=TRADE_SYSTEM_PROMPT,
            temperature=0.3,
            max_output_tokens=4096,            
            response_mime_type="application/json", # Force JSON mimetype
            response_schema=GeminiTradeResponse, # Force adherence to our exact Pydantic keys
        ),
    )

    # Return the structured response
    return TradeRecommendation(
        query=trade_query.query,
        direction=trade_query.direction,
        recommendation=response.text,
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "TradeConnect BD-DE"}

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return FileResponse("static/index.html") 

