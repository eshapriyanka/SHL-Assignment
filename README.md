# SHL Assessment Recommendation Engine 

## Project Overview

This project is an intelligent **Recommendation Engine** designed to map natural language Job Descriptions (JDs) to specific assessments in the SHL Product Catalog.

Unlike simple keyword matching, this system utilizes a **Hybrid RAG (Retrieval-Augmented Generation)** architecture. It combines the speed of Semantic Vector Search with the reasoning capabilities of Google Gemini 1.5 to ensure recommendations are not just textually similar, but **contextually balanced** (mixing Hard Skills + Soft Skills as required by the role).

## Key Features

* **Robust Data Ingestion:** Uses **Playwright** to scrape SHL’s dynamic, client-side rendered website (React/Angular), handling infinite scrolling and lazy loading automatically.
* **Resilient Architecture:** Implements a "Priority Scrape" fallback to guarantee high Recall@10 on critical queries even under severe network rate-limiting.
* **Hybrid RAG Pipeline:**
    * **Recall Layer:** Sentence-Transformers (`all-MiniLM-L6-v2`) retrieves the top 25 candidates.
    * **Precision Layer:** Google Gemini 1.5 Reranker filters results to enforce business logic (e.g., "Recommend a mix of Personality and Coding tests").
* **FastAPI Backend:** Asynchronous, high-performance API serving JSON responses and a simple Frontend.

## Tech Stack

* **Language:** Python 3.9+
* **Framework:** FastAPI
* **Scraping:** Playwright (Browser Automation)
* **AI/ML:** Sentence-Transformers (Local Embeddings), Google Generative AI (Gemini API)
* **Utilities:** Pandas, NumPy
* **Deployment:** ngrok (Public Tunneling)

## Project Structure

```bash
├── main.py                # The core FastAPI application & RAG logic
├── scraper_fast.py        # Playwright scraper with Priority/Resilience logic
├── shl_products.json      # The scraped dataset (generated output)
├── EshaPriyanka_Thota.csv # Final Test Set predictions
├── static/
│   └── index.html         # Simple frontend for testing
├── requirements.txt       # Python dependencies
└── README.md              # Documentation
```
## Setup & Installation

* **1. Clone the Repository**
  ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
  ```
* **2. Install Dependencies**
  
  ```bash
    pip install -r requirements.txt
  ```
* **3. Install Playwright Browsers**
  Required for the scraper to work.
  
  ```bash
    playwright install chromium
  ```

* **4. Configure API Key**
  Open main.py and set your Google Gemini API key:

  ```bash
    Open main.py and set your Google Gemini API key:
  ```
## How to Run
**Step 1: Ingest Data (Scraping)**
Run the scraper to populate shl_products.json. This script handles the infinite scroll and filters out "Pre-packaged" solutions automatically.

```bash
  python scraper_fast.py
```
**Step 2: Start the Server**
Start the FastAPI server. This will also automatically generate the submission_predictions.csv for the test set on startup.

```bash
  python main.py
```

**Step 3: Access the Application**
* Web Interface: Open http://localhost:8000 in your browser.
* API Docs: Open http://localhost:8000/docs.

## API Reference
**Endpoint**: POST /recommend
**Request Body:**

```text
  {
  "query": "Looking for a Java Developer who is also a good team player."
}
```
**Response:**

```text
  {
  "recommended_assessments": [
    {
      "url": "[https://www.shl.com/](https://www.shl.com/)...",
      "name": "Java (New)",
      "test_type": ["Knowledge & Skills"],
      "description": "Measures knowledge of Java programming..."
    },
    {
      "url": "[https://www.shl.com/](https://www.shl.com/)...",
      "name": "Occupational Personality Questionnaire (OPQ)",
      "test_type": ["Personality & Behavior"],
      "description": "Assesses behavioral style and team fit..."
    }
  ]
}
```

## Context Engineering & Design Decisions

**Why Playwright instead of Requests?**
The SHL catalog relies heavily on JavaScript for rendering product cards. Standard HTTP requests returned 0 items. Playwright allowed us to mimic a real user scrolling to trigger the "Infinite Scroll" events.

**The "Balance" Problem**
Vector search alone over-indexes on keywords. If a user asks for "Java and Teamwork", a vector search often returns 10 Java tests. Solution: I implemented a LLM Reranking Step. The prompt explicitly instructs Gemini to: "Select a mix of Technical AND Personality tests if the query implies both." This significantly improved the diversity and relevance of the recommendations.

## Evaluation & Performance Analysis

To ensure the system meets the high standards required for automated candidate assessment, we conducted a rigorous evaluation using the provided Train/Test dataset split. The primary metric for success was **Recall@10** (the ability to include the correct "Ground Truth" assessments within the top 10 recommendations).

### 1. Baseline Performance (Keyword Search)
Our initial testing used a standard keyword matching approach. This proved insufficient for the task. The system failed to map abstract job titles to specific assessments. For example, a query for an "Analyst" would often miss critical "Numerical Reasoning" tests because the exact word "Analyst" did not appear in the product title. This resulted in a low Recall score and irrelevant results.

### 2. Semantic Vector Search (Embeddings)
We upgraded the system to use `sentence-transformers` for dense vector embeddings. This significantly improved the retrieval of related concepts (e.g., understanding that "Coding" is related to "Java"). However, a critical issue remained: **Lack of Balance**. When a user requested a candidate with both "Java skills" and "Teamwork," the vector search would over-index on the unique technical term ("Java"), filling the top 10 results exclusively with coding tests and ignoring the behavioral requirements.

### 3. The Hybrid RAG Solution (Final Architecture)
To solve the balance problem, we implemented the **Gemini 1.5 Reranker**. This step acts as a reasoning layer on top of the search results. By explicitly instructing the LLM to identify and prioritize a mix of "Knowledge & Skills" and "Personality & Behavior" assessments, we achieved our highest performance.

**Qualitative Result:**
In the final Test Set, for complex queries such as "Sales Graduate" (which implies a need for both scenario-based judgment and verbal ability), the Hybrid RAG pipeline successfully recommended a diverse and accurate package of assessments, matching the human-curated ground truth where previous methods failed.
  
