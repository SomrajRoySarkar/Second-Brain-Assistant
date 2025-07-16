import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import time
import re
from functools import lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

API_KEY = os.getenv('GOOGLE_API_KEY')
CSE_ID = os.getenv('GOOGLE_CSE_ID')

# Cache for search results
_search_cache = {}
_cache_lock = threading.Lock()

# Existing simple search

@lru_cache(maxsize=100)
def google_search(query, num_results=3):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": CSE_ID,
        "q": query,
        "num": num_results,
    }
    response = requests.get(url, params=params)
    results = []
    if response.status_code == 200:
        data = response.json()
        for item in data.get("items", []):
            results.append({
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "link": item.get("link"),
            })
    else:
        results.append({"title": "Error", "snippet": f"Status code: {response.status_code}", "link": ""})
    return results

# Advanced web search for best results

def advanced_web_search(query, gemini_model, num_results=5, snippet_enrich=True, query_expansion=True, sleep_between=0.5):
    """
    Advanced web search with LLM-powered snippet enrichment and query expansion.
    Requires a Gemini model for LLM tasks.
    """
    # Check cache first
    cache_key = f"{query}:{num_results}:{snippet_enrich}:{query_expansion}"
    with _cache_lock:
        if cache_key in _search_cache:
            return _search_cache[cache_key]
    
    all_results = []
    queries = [query]
    
    # 1. Query Expansion (reduced for speed)
    if query_expansion and len(query.split()) > 3:  # Only expand complex queries
        prompt = f"""Expand this search query into 1-2 alternative queries. Return as JSON list: "{query}"""
        try:
            resp = gemini_model.generate_content(prompt)
            expanded = resp.text if hasattr(resp, 'text') else resp.candidates[0].content.parts[0].text
            expanded = expanded.strip()
            match = re.search(r'\[.*\]', expanded, re.DOTALL)
            if match:
                try:
                    import json
                    expansions = json.loads(match.group(0))
                    if isinstance(expansions, list):
                        queries.extend([q for q in expansions[:1] if isinstance(q, str)])  # Limit to 1 expansion
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
    
    # 2. Parallel multi-query search
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_query = {executor.submit(google_search, q, num_results): q for q in queries[:2]}  # Limit queries
        for future in as_completed(future_to_query):
            try:
                results = future.result(timeout=5)  # 5 second timeout
                all_results.extend(results)
            except Exception:
                pass
    # 3. Deduplication (by link and title)
    seen = set()
    deduped = []
    for r in all_results:
        key = (r['link'], r['title'])
        if key not in seen and r['link']:
            deduped.append(r)
            seen.add(key)
    # 4. Ranking (simple: prioritize original query, then expansions)
    def rank_score(item):
        score = 0
        if query.lower() in (item['title'] or '').lower():
            score += 2
        if query.lower() in (item['snippet'] or '').lower():
            score += 1
        if any(domain in (item['link'] or '') for domain in ["wikipedia.org", "bbc.com", "nytimes.com", "nature.com", "mit.edu", "harvard.edu"]):
            score += 2
        score += len(item['snippet'] or '') / 200  # prefer longer snippets
        return score
    deduped.sort(key=rank_score, reverse=True)
    # 5. Snippet enrichment (fetch and summarize top N pages)
    if snippet_enrich:
        for i, item in enumerate(deduped[:2]):  # Only top 2 for speed
            try:
                resp = requests.get(item['link'], timeout=5)
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Get visible text
                texts = soup.stripped_strings
                page_text = ' '.join(list(texts)[:500])  # limit for speed
                # Summarize with LLM
                prompt = f"Summarize the following web page content in 2-3 sentences, focusing on the main facts and insights.\n\nContent:\n{page_text}\n\nSummary:"
                resp = gemini_model.generate_content(prompt)
                summary = resp.text if hasattr(resp, 'text') else resp.candidates[0].content.parts[0].text
                summary = summary.strip()
                item['enriched_snippet'] = summary
            except Exception:
                item['enriched_snippet'] = None
    with _cache_lock:
        _search_cache[cache_key] = deduped[:num_results]
    return deduped[:num_results]
