import os
import json
import requests
from datetime import datetime, timedelta

# Ensure SERPER_API_KEY is in your GitHub Secrets
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Step 1: Hunt quality Operations Analyst jobs across the web."""
    # Broad queries to capture multiple operations specialties
    queries = [
        'intitle:"Operations Analyst" "United States" job',
        'intitle:"Business Operations Analyst" "United States" job',
        'intitle:"Supply Chain Analyst" "United States" job',
        'intitle:"Financial Operations Analyst" "United States" job',
        'intitle:"Sales Operations Analyst" "United States" job'
    ]
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': str(SERPER_KEY), 'Content-Type': 'application/json'}
    all_results = []

    for q in queries:
        try:
            # num: 10 allows for a wider reach across the general web
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
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try: 
                database = json.load(f)
            except: 
                database = []

    # Step 4: Cleanup jobs older than 72 hours
    three_days_ago = datetime.now() - timedelta(days=3)
    database = [j for j in database if datetime.strptime(j['found_at'], "%Y-%m-%d %H:%M") > three_days_ago]

    # Step 5: 6PM LOCK (23:00 UTC) - Archive "New" jobs
    if datetime.now().hour == 23:
        for job in database:
            if job['status'] == 'New':
                job['status'] = 'Best_Archived'

    existing_urls = {j['url'] for j in database}
    new_entries = []
    
    for lead in new_raw_leads:
        url = lead.get('link')
        if url and url not in existing_urls:
            title = lead.get('title', 'Operations Analyst')
            posted_time = lead.get('date', 'Just now') 
            
            # Extract company name from common title formats
            company = "US Company"
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

    # Combine new leads at the top, cap database at 100 for global search
    database = (new_entries + database)[:100]

    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
    
    print(f"✅ Success: {len(new_entries)} new Operations leads. Total: {len(database)}")

if __name__ == "__main__":
    if not SERPER_KEY:
        print("❌ Error: SERPER_API_KEY environment variable not found.")
    else:
        update_database(get_jobs())
