import json
import os
import pandas as pd
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer, util
import google.generativeai as genai

GOOGLE_API_KEY = "AIzaSyCS0_Xl4QLRkVJtiBO1cdU0yMmQOHMXpEQ" 
genai.configure(api_key=GOOGLE_API_KEY)
model_gemini = genai.GenerativeModel('gemini-1.5-flash')

app = FastAPI()

# frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse('static/index.html')

# LOAD & INDEX
print("Loading Data...")
try:
    with open('shl_products.json', 'r') as f:
        products = json.load(f)
    print(f"Loaded {len(products)} products.")
except FileNotFoundError:
    print("CRITICAL: shl_products.json not found! Running with empty data.")
    products = []

embedder = SentenceTransformer('all-MiniLM-L6-v2')
corpus_texts = [f"{p['name']} {p.get('description', '')}" for p in products]
corpus_embeddings = embedder.encode(corpus_texts, convert_to_tensor=True)

# LOGIC
def perform_search(query_text, k=25):
    if not products: return []
    query_vec = embedder.encode(query_text, convert_to_tensor=True)
    hits = util.semantic_search(query_vec, corpus_embeddings, top_k=min(k, len(products)))
    return [products[hit['corpus_id']] for hit in hits[0]]

def llm_rerank(user_query, candidates):
    if not candidates: return []
    
    # Simple summary for LLM
    summary = [f"ID {i}: {p['name']} - {p['test_type']}" for i, p in enumerate(candidates)]
    
    prompt = f"""
    Query: "{user_query}"
    Select top 5-10 relevant assessments from:
    {json.dumps(summary)}
    Return JSON list of IDs like [0, 2].
    """
    try:
        response = model_gemini.generate_content(prompt)
        # Clean markdown if present
        text = response.text.replace("```json", "").replace("```", "").strip()
        ids = json.loads(text)
        return [candidates[i] for i in ids if i < len(candidates)][:10]
    except:
        return candidates[:10]

# 3. API 
class QueryRequest(BaseModel):
    query: str

@app.post("/recommend")
def recommend(request: QueryRequest):
    cands = perform_search(request.query)
    final = llm_rerank(request.query, cands)
    return {"recommended_assessments": final}

# 4. CSV GENERATION (HARDCODED QUERIES)
# These are the exact queries from the Test Set.
TEST_QUERIES = [
    "Looking to hire mid-level professionals who are proficient in Python, SQL and Java Script. Need an assessment package that can test all skills with max duration of 60 minutes.",
    "I am hiring for an analyst and wants applications to screen using Cognitive and personality tests, what options are available within 45 mins.",
    """I have a JD Job Description\n\n People Science.\nPeople Answers !\n\nDo you love contributing to commercial growth and success? Join as a Presales Specialist!\nIn this role, you’ll support the Presales function...""",
    "I am new looking for new graduates in my sales team, suggest an 30 min long assessment",
    """For Marketing - Content Writer Position\nDepartment: Marketing\nLocation: Gurugram\nAbout Company\nShopClues.com is India's leading e-commerce platform...""",
    "I want to hire a product manager with 3-4 years of work experience and expertise in SDLC, Jira and Confluence",
    """Suggest me an assessment for the JD below Job Description\n Find purpose in each day while contributing to a workplace revolution!\nSHL, People Science. People Answers.\nAre you a driven business professional...""",
    "I want to hire Customer support executives who are expert in English communication."
]

def generate_csv():
    print("Generating CSV using INTERNAL query list (Bypassing file check)...")
    results = []
    
    for q in TEST_QUERIES:
        cands = perform_search(q)
        recs = llm_rerank(q, cands)
        
        for r in recs:
            results.append({"Query": q, "Assessment_url": r.get('url', '')})
            
    # Save directly to the requested name if you want, or rename later
    pd.DataFrame(results).to_csv("EshaPriyanka_Thota.csv", index=False)
    print("SUCCESS: EshaPriyanka_Thota.csv created.")

if __name__ == "__main__":
    generate_csv()
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
