import requests
import os
import re
import json
import matplotlib.pyplot as plt

USER = "JulioArturoRodriguez"

# Tecnologías a detectar por patrones
TECH_PATTERNS = {
    "React": r"react",
    "Node.js": r"node",
    "Express": r"express",
    "Bootstrap": r"bootstrap",
    "JWT": r"jsonwebtoken|jwt",
    "Mongoose": r"mongoose",
    "Spring Boot": r"spring-boot",
    "Spring Security": r"spring-security",
    "Spring Data JPA": r"spring-data-jpa",
    "Hibernate": r"hibernate",
    "Lombok": r"lombok",
    "NumPy": r"numpy",
    "Pandas": r"pandas",
    "Matplotlib": r"matplotlib",
    "Selenium": r"selenium",
    "MongoDB": r"mongo",
    "MySQL": r"mysql",
    "SQLite": r"sqlite",
    "Vite": r"vite",
    "Maven": r"maven",
    "Postman": r"postman",
    "Insomnia": r"insomnia"
}

def detect_technologies_in_text(text):
    found = []
    for tech, pattern in TECH_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(tech)
    return found

def fetch_file_content(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    return ""

repos_url = f"https://api.github.com/users/{USER}/repos"
repos = requests.get(repos_url).json()

tech_counts = {}

for repo in repos:
    contents_url = f"https://api.github.com/repos/{USER}/{repo['name']}/contents"
    contents = requests.get(contents_url).json()

    if isinstance(contents, dict) and contents.get("message"):
        continue

    for item in contents:
        if item["type"] == "file":
            file_text = fetch_file_content(item["download_url"])
            found_techs = detect_technologies_in_text(file_text)

            for tech in found_techs:
                tech_counts[tech] = tech_counts.get(tech, 0) + 1

# Ordenar tecnologías
sorted_techs = dict(sorted(tech_counts.items(), key=lambda x: x[1], reverse=True))

# Crear carpeta output
os.makedirs("output", exist_ok=True)

# Guardar JSON
with open("output/tech.json", "w") as f:
    json.dump(sorted_techs, f, indent=4)

# Guardar ranking en Markdown
with open("output/tech.md", "w") as f:
    f.write("## 🚀 Tecnologías más usadas (actualizado automáticamente)\n\n")
    for tech, count in sorted_techs.items():
        f.write(f"- **{tech}**: {count} repos\n")

# Graficar
plt.figure(figsize=(12, 6))
plt.bar(sorted_techs.keys(), sorted_techs.values(), color='orange')
plt.title(f"Tecnologías detectadas en repos de {USER}")
plt.xlabel("Tecnologías")
plt.ylabel("Cantidad de repos donde aparece")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("output/tech.png")
