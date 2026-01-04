import requests
import os
import re
import json
import matplotlib.pyplot as plt

USER = "JulioArturoRodriguez"

TOOLS = {
    "Vite": r"vite",
    "Maven": r"maven",
    "Spring Initializr": r"spring-initializr",
    "Visual Studio Code": r"vscode|visual studio code",
    "IntelliJ IDEA": r"intellij",
    "Eclipse": r"eclipse",
    "NetBeans": r"netbeans",
    "CodeBlocks": r"code::blocks"
}

def fetch_file(url):
    r = requests.get(url)
    return r.text if r.status_code == 200 else ""

def detect_tools(text):
    found = []
    for tech, pattern in TOOLS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(tech)
    return found

repos = requests.get(f"https://api.github.com/users/{USER}/repos").json()

tools_counts = {}

for repo in repos:
    contents = requests.get(repo["contents_url"].replace("{+path}", "")).json()
    if isinstance(contents, dict):
        continue

    for item in contents:
        if item["type"] == "file":
            text = fetch_file(item["download_url"])
            found = detect_tools(text)
            for tech in found:
                tools_counts[tech] = tools_counts.get(tech, 0) + 1

os.makedirs("output", exist_ok=True)

sorted_tools = dict(sorted(tools_counts.items(), key=lambda x: x[1], reverse=True))

with open("output/tools_stats.json", "w") as f:
    json.dump(sorted_tools, f, indent=4)

with open("output/tools_stats.md", "w") as f:
    f.write("## Herramientas detectadas automáticamente\n\n")
    for tech, count in sorted_tools.items():
        f.write(f"- **{tech}**: {count} repos\n")

if sorted_tools:
    plt.figure(figsize=(12, 6))
    plt.bar(sorted_tools.keys(), sorted_tools.values(), color="brown")
    plt.title("Herramientas detectadas")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/tools_stats.png")
    plt.close()
