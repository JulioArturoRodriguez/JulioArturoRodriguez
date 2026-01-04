import requests
import os
import re
import json
import matplotlib.pyplot as plt

USER = "JulioArturoRodriguez"

FRAMEWORKS = {
    "React": r"react",
    "React Router": r"react-router",
    "Styled Components": r"styled-components",
    "Express": r"express",
    "Node.js": r"node",
    "Bootstrap": r"bootstrap",
    "Mongoose": r"mongoose",
    "Spring Boot": r"spring-boot",
    "Spring Web": r"spring-web",
    "Spring Security": r"spring-security",
    "Spring Data JPA": r"spring-data-jpa",
    "Hibernate": r"hibernate",
    "Lombok": r"lombok"
}

def fetch_file(url):
    r = requests.get(url)
    return r.text if r.status_code == 200 else ""

def detect_frameworks(text):
    found = []
    for tech, pattern in FRAMEWORKS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(tech)
    return found

repos = requests.get(f"https://api.github.com/users/{USER}/repos").json()

framework_counts = {}

for repo in repos:
    contents = requests.get(repo["contents_url"].replace("{+path}", "")).json()
    if isinstance(contents, dict):
        continue

    for item in contents:
        if item["type"] == "file":
            text = fetch_file(item["download_url"])
            found = detect_frameworks(text)
            for tech in found:
                framework_counts[tech] = framework_counts.get(tech, 0) + 1

os.makedirs("output", exist_ok=True)

sorted_fw = dict(sorted(framework_counts.items(), key=lambda x: x[1], reverse=True))

with open("output/frameworks.json", "w") as f:
    json.dump(sorted_fw, f, indent=4)

with open("output/frameworks.md", "w") as f:
    f.write("## Frameworks detectados automáticamente\n\n")
    for tech, count in sorted_fw.items():
        f.write(f"- **{tech}**: {count} repos\n")

if sorted_fw:
    plt.figure(figsize=(12, 6))
    plt.bar(sorted_fw.keys(), sorted_fw.values(), color="purple")
    plt.title("Frameworks detectados")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/frameworks.png")
    plt.close()
