import os
import json
import requests
from datetime import datetime, timedelta

# Ensure you have set this in your GitHub Repo Secrets
SERPER_KEY = os.getenv("SERPER_API_KEY")

def get_jobs():
    """Step 1: Hunt 15-20 quality Software Engineering jobs."""
    # Targeted queries for Software Engineering roles in the US
    queries = [
        'intitle:"Software Engineer" "United States" site:jobs.lever.co',
        'intitle:"Full Stack Engineer" "United States" site:jobs.lever.co',
        'intitle:"Backend Engineer" "United States" site:job-boards.greenhouse.io',
        'intitle:"Frontend Engineer" "United States" site:job-boards.greenhouse.io',
        'intitle:"Software Developer" "United States" site:boards.greenhouse.io'
    ]
    
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': str(SERPER_KEY), 'Content-Type': 'application/json'}
    all_results = []

    for q in queries:
        try:
            # Fetching 4 results per query to stay within a healthy limit
            res = requests.post(url, headers=headers, json={"q": q, "num": 4, "tbs": "qdr:d"})
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

    # Step 5: 6PM LOCK (23:00 UTC) - Move 'New' to 'Best_Archived' for Morning Review
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
            title = lead.get('title', 'Software Engineer')
            posted_time = lead.get('date', 'Just now') 
            
            # Simple company extraction logic
            company = "US Tech Co"
            if " at " in title:
                company = title.split(" at ")[-1].split(" - ")[0]
            elif " - " in title:
                company = title.split(" - ")[0]

            new_entries.append({
                "title": title,
                "url": url,
                "company": company,
                "status": "New",
                "posted_at": posted_time,
                "found_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            existing_urls.add(url)

    # Combine new leads at the top, cap total database at 50
    database = (new_entries + database)[:50]

    with open(file_path, 'w') as f:
        json.dump(database, f, indent=4)
    
    print(f"✅ Success: {len(new_entries)} new Software Engineer leads found. Total: {len(database)}")

if __name__ == "__main__":
    if not SERPER_KEY:
        print("❌ Error: SERPER_API_KEY not found in environment variables.")
    else:
        update_database(get_jobs())
