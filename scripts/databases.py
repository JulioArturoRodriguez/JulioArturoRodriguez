import requests
import os
import re
import json
import matplotlib.pyplot as plt

USER = "JulioArturoRodriguez"

DATABASES = {
    "MongoDB": r"mongo",
    "MySQL": r"mysql",
    "SQLite": r"sqlite"
}

def fetch_file(url):
    r = requests.get(url)
    return r.text if r.status_code == 200 else ""

def detect_databases(text):
    found = []
    for tech, pattern in DATABASES.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(tech)
    return found

repos = requests.get(f"https://api.github.com/users/{USER}/repos").json()

db_counts = {}

for repo in repos:
    contents = requests.get(repo["contents_url"].replace("{+path}", "")).json()
    if isinstance(contents, dict):
        continue

    for item in contents:
        if item["type"] == "file":
            text = fetch_file(item["download_url"])
            found = detect_databases(text)
            for tech in found:
                db_counts[tech] = db_counts.get(tech, 0) + 1

os.makedirs("output", exist_ok=True)

sorted_db = dict(sorted(db_counts.items(), key=lambda x: x[1], reverse=True))

with open("output/database_stats.json", "w") as f:
    json.dump(sorted_db, f, indent=4)

with open("output/database_stats.md", "w") as f:
    f.write("## Bases de datos detectadas automáticamente\n\n")
    for tech, count in sorted_db.items():
        f.write(f"- **{tech}**: {count} repos\n")

if sorted_db:
    plt.figure(figsize=(12, 6))
    plt.bar(sorted_db.keys(), sorted_db.values(), color="blue")
    plt.title("Bases de datos detectadas")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/database_stats.png")
    plt.close()


