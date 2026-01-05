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

TOKEN = os.getenv("GH_TOKEN")
headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

visited = set()  # evita bucles infinitos

def fetch_file(url):
    r = requests.get(url, headers=headers)
    return r.text if r.status_code == 200 else ""

def detect_databases(text):
    found = []
    for tech, pattern in DATABASES.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(tech)
    return found

def scan_directory(url):
    if url in visited:
        return
    visited.add(url)

    contents = requests.get(url, headers=headers).json()

    if isinstance(contents, dict):
        return

    for item in contents:
        if item["type"] == "file":
            text = fetch_file(item["download_url"])
            found = detect_databases(text)
            for tech in found:
                db_counts[tech] = db_counts.get(tech, 0) + 1

        elif item["type"] == "dir":
            scan_directory(item["url"])

# === Obtener repos ===
repos = requests.get(
    f"https://api.github.com/users/{USER}/repos?per_page=100",
    headers=headers
).json()

db_counts = {}

for repo in repos:
    print(f"Analizando repo: {repo['name']}")
    root_url = repo["contents_url"].replace("{+path}", "")
    scan_directory(root_url)

os.makedirs("output", exist_ok=True)

sorted_db = dict(sorted(db_counts.items(), key=lambda x: x[1], reverse=True))

with open("output/databases.json", "w") as f:
    json.dump(sorted_db, f, indent=4)

with open("output/databases.md", "w") as f:
    f.write("## Bases de datos detectadas automáticamente\n\n")
    if not sorted_db:
        f.write("No se detectaron bases de datos.\n")
    else:
        for tech, count in sorted_db.items():
            f.write(f"- **{tech}**: {count} repos\n")

plt.figure(figsize=(12, 6))

if sorted_db:
    plt.bar(sorted_db.keys(), sorted_db.values(), color="blue")
else:
    plt.text(0.5, 0.5, "No se detectaron bases de datos", ha="center", va="center", fontsize=14)

plt.title("Bases de datos detectadas")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("output/databases.png")
plt.close()
