import requests
import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import time
import re

load_dotenv()

API_KEY = os.getenv('GOOGLE_API_KEY')
CSE_ID = os.getenv('GOOGLE_CSE_ID')

# Existing simple search

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

def advanced_web_search(query, cohere_client, num_results=5, snippet_enrich=True, query_expansion=True, sleep_between=1):
    """
    Advanced web search: query expansion, multi-query, deduplication, ranking, snippet enrichment.
    Returns a list of dicts: {title, snippet, link, [enriched_snippet]}
    Requires a Cohere client for LLM tasks.
    """
    all_results = []
    queries = [query]
    # 1. Query Expansion
    if query_expansion:
        prompt = f"""
        Expand the following search query into 2-3 alternative queries that might yield more relevant or diverse web results. Return as a JSON list of strings.\n\nQuery: {query}\n\nJSON Output:
        """
        try:
            resp = cohere_client.chat(message=prompt, model="command-r-plus", temperature=0.4, max_tokens=100)
            match = re.search(r'\[.*\]', resp.text, re.DOTALL)
            if match:
                expansions = eval(match.group(0))
                if isinstance(expansions, list):
                    queries.extend([q for q in expansions if isinstance(q, str)])
        except Exception:
            pass
    # 2. Multi-query search
    for q in queries:
        results = google_search(q, num_results=num_results)
        all_results.extend(results)
        time.sleep(sleep_between)  # avoid rate limits
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
                summary = cohere_client.chat(message=prompt, model="command-r-plus", temperature=0.3, max_tokens=120).text.strip()
                item['enriched_snippet'] = summary
            except Exception:
                item['enriched_snippet'] = None
    return deduped[:num_results] 