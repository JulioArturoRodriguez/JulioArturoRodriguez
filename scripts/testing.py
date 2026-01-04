import requests
import os
import re
import json
import matplotlib.pyplot as plt

USER = "JulioArturoRodriguez"

TESTING_TOOLS = {
    "Selenium": r"selenium",
    "Postman": r"postman",
    "Insomnia": r"insomnia"
}

def fetch_file(url):
    r = requests.get(url)
    return r.text if r.status_code == 200 else ""

def detect_testing(text):
    found = []
    for tech, pattern in TESTING_TOOLS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(tech)
    return found

repos = requests.get(f"https://api.github.com/users/{USER}/repos").json()

testing_counts = {}

for repo in repos:
    contents = requests.get(repo["contents_url"].replace("{+path}", "")).json()
    if isinstance(contents, dict):
        continue

    for item in contents:
        if item["type"] == "file":
            text = fetch_file(item["download_url"])
            found = detect_testing(text)
            for tech in found:
                testing_counts[tech] = testing_counts.get(tech, 0) + 1

os.makedirs("output", exist_ok=True)

sorted_testing = dict(sorted(testing_counts.items(), key=lambda x: x[1], reverse=True))

with open("output/testing.json", "w") as f:
    json.dump(sorted_testing, f, indent=4)

with open("output/testing.md", "w") as f:
    f.write("## Testing detectado automáticamente\n\n")
    for tech, count in sorted_testing.items():
        f.write(f"- **{tech}**: {count} repos\n")

if sorted_testing:
    plt.figure(figsize=(12, 6))
    plt.bar(sorted_testing.keys(), sorted_testing.values(), color="red")
    plt.title("Testing detectado")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/testing.png")
    plt.close()
