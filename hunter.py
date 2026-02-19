import os
import json
import requests
from datetime import datetime, timedelta

# Ensure you have set this in your GitHub Repo Secrets
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Step 1: Hunt quality Manufacturing Data Analyst jobs from across the internet."""
    # Broad queries without site-specific limitations
    queries = [
        'intitle:"Manufacturing Systems Analyst" "United States" job',
        'intitle:"ERP Production Analyst" "United States" job',
        'intitle:"Manufacturing Data Analyst" "United States" job',
        'intitle:"Production Planning Analyst" "United States" job',
        'intitle:"Supply Chain Data Analyst" "Manufacturing" "United States" job'
    ]
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': str(SERPER_KEY), 'Content-Type': 'application/json'}
    all_results = []

    for q in queries:
        try:
            # num: 10 allows for more results per query since we are searching the whole web
            # tbs: "qdr:d" ensures we only get results from the last 24 hours
            res = requests.post(url, headers=headers, json={"q": q, "num": 10, "tbs": "qdr:d"})
            organic = res.json().get('organic', [])
            all_results.extend(organic)
        except Exception as e:
            print(f"Error fetching for query {q}: {e}")
            continue
            
    return all_results

def update_database(new_raw_leads):
    file_path = 'jobs.json'
    database = []
    
    # Load existing jobs
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try: 
                database = json.load(f)
            except: 
                database = []

    # Step 4: Update History (Cleanup jobs older than 72 hours)
    three_days_ago = datetime.now() - timedelta(days=3)
    database = [j for j in database if datetime.strptime(j['found_at'], "%Y-%m-%d %H:%M") > three_days_ago]

    # Step 5: 6PM LOCK (23:00 UTC) - Move 'New' to 'Best_Archived'
    if datetime.now().hour == 23:
        for job in database:
            if job['status'] == 'New':
                job['status'] = 'Best_Archived'

    # Step 2 & 3: Filter duplicates and format new leads
    existing_urls = {j['url'] for j in database}
    new_entries = []
    
    for lead in new_raw_leads:
        url = lead.get('link')
        if url and url not in existing_urls:
            title = lead.get('title', 'Manufacturing Data Analyst')
            posted_time = lead.get('date', 'Just now') 
            
            # Refined company extraction for broader search results
            company = "US Manufacturing Co"
            if " at " in title:
                company = title.split(" at ")[-1].split(" - ")[0]
            elif " | " in title:
                company = title.split(" | ")[-1]

            new_entries.append({
                "title": title,
                "url": url,
                "company": company,
                "status": "New",
                "posted_at": posted_time,
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            existing_urls.add(url)

    # Combine new leads at the top, cap total database at 100 for broader searches
    database = (new_entries + database)[:100]

    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
    
    print(f"✅ Success: {len(new_entries)} new leads found. Total: {len(database)}")

if __name__ == "__main__":
    if not SERPER_KEY:
        print("❌ Error: SERPER_API_KEY not found in environment variables.")
    else:
        update_database(get_jobs())
