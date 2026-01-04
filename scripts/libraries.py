import requests
import os
import re
import json
import matplotlib.pyplot as plt

USER = "JulioArturoRodriguez"

LIBRARIES = {
    "JWT": r"jsonwebtoken|jwt",
    "Bcrypt": r"bcrypt",
    "NumPy": r"numpy",
    "Pandas": r"pandas",
    "Matplotlib": r"matplotlib"
}

def fetch_file(url):
    r = requests.get(url)
    return r.text if r.status_code == 200 else ""

def detect_libraries(text):
    found = []
    for tech, pattern in LIBRARIES.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(tech)
    return found

repos = requests.get(f"https://api.github.com/users/{USER}/repos").json()

library_counts = {}

for repo in repos:
    contents = requests.get(repo["contents_url"].replace("{+path}", "")).json()
    if isinstance(contents, dict):
        continue

    for item in contents:
        if item["type"] == "file":
            text = fetch_file(item["download_url"])
            found = detect_libraries(text)
            for tech in found:
                library_counts[tech] = library_counts.get(tech, 0) + 1

os.makedirs("output", exist_ok=True)

sorted_lib = dict(sorted(library_counts.items(), key=lambda x: x[1], reverse=True))

with open("output/libraries.json", "w") as f:
    json.dump(sorted_lib, f, indent=4)

with open("output/libraries.md", "w") as f:
    f.write("## Librerías detectadas automáticamente\n\n")
    for tech, count in sorted_lib.items():
        f.write(f"- **{tech}**: {count} repos\n")

if sorted_lib:
    plt.figure(figsize=(12, 6))
    plt.bar(sorted_lib.keys(), sorted_lib.values(), color="green")
    plt.title("Librerías detectadas")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/libraries.png")
    plt.close()
