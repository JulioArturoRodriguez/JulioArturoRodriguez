import requests
import os
import re
import json
import matplotlib.pyplot as plt

USER = "JulioArturoRodriguez"

FRAMEWORKS = {
    "React": r"react",
    "Angular": r"angular",
    "Vue": r"vue",
    "Django": r"django",
    "Flask": r"flask",
    "FastAPI": r"fastapi",
    "Laravel": r"laravel",
    "Spring": r"spring",
    "Express": r"express"
}

# === TOKEN ===
TOKEN = os.getenv("GH_TOKEN")
headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

# Extensiones que SÍ analizamos
VALID_EXT = (
    ".py", ".js", ".ts", ".java", ".php", ".rb", ".go", ".cs",
    ".json", ".yml", ".yaml", ".md"
)

# Carpetas que ignoramos
IGNORE_DIRS = {"node_modules", "vendor", "dist", "build", ".git", ".github"}

visited = set()
framework_counts = {}

def fetch_file(url):
    r = requests.get(url, headers=headers)
    return r.text if r.status_code == 200 else ""

def detect_frameworks(text):
    found = []
    for tech, pattern in FRAMEWORKS.items():
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
        if item["type"] == "dir":
            if item["name"] in IGNORE_DIRS:
                continue
            scan_directory(item["url"])

        elif item["type"] == "file":
            if not any(item["name"].endswith(ext) for ext in VALID_EXT):
                continue

            text = fetch_file(item["download_url"])
            found = detect_frameworks(text)
            for tech in found:
                framework_counts[tech] = framework_counts.get(tech, 0) + 1

# Obtener repos
repos = requests.get(
    f"https://api.github.com/users/{USER}/repos?per_page=100",
    headers=headers
).json()

for repo in repos:
    print(f"Analizando repo: {repo['name']}")
    root_url = repo["contents_url"].replace("{+path}", "")
    scan_directory(root_url)

os.makedirs("output", exist_ok=True)

sorted_fw = dict(sorted(framework_counts.items(), key=lambda x: x[1], reverse=True))

with open("output/frameworks.json", "w") as f:
    json.dump(sorted_fw, f, indent=4)

with open("output/frameworks.md", "w") as f:
    f.write("## Frameworks detectados automáticamente\n\n")
    if not sorted_fw:
        f.write("No se detectaron frameworks.\n")
    else:
        for tech, count in sorted_fw.items():
            f.write(f"- **{tech}**: {count} repos\n")

plt.figure(figsize=(12, 6))

if sorted_fw:
    plt.bar(sorted_fw.keys(), sorted_fw.values(), color="green")
else:
    plt.text(0.5, 0.5, "No se detectaron frameworks", ha="center", va="center", fontsize=14)

plt.title("Frameworks detectados")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("output/frameworks.png")
plt.close()
