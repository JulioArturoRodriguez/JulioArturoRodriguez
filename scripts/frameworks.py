import requests
import os
import re
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

USER = "JulioArturoRodriguez"

# === FRAMEWORKS REALES (Front + Back + ML/DL) ===
FRAMEWORKS = {
    # FRONT-END
    "React": r"(import\s+React\b|from\s+['\"]react['\"])",
    "React Router": r"(from\s+['\"]react-router|from\s+['\"]react-router-dom)",
    "Styled Components": r"(from\s+['\"]styled-components['\"])",
    "Bootstrap": r"(bootstrap|class=\".*btn|class=\".*container)",

    # BACK-END
    "Express": r"(from\s+['\"]express['\"]|require\(['\"]express['\"]\))",
    "Spring Boot": r"@SpringBootApplication|spring-boot",
    "Spring Web": r"@RestController|@Controller|spring-web",
    "Spring Security": r"@EnableWebSecurity|spring-security",
    "Spring Data JPA": r"spring-data-jpa",
    "Hibernate": r"org\.hibernate|hibernate-core",

    # MACHINE LEARNING / DEEP LEARNING
    "TensorFlow": r"(import\s+tensorflow|from\s+tensorflow)",
    "Keras": r"(import\s+keras|from\s+keras)",
    "PyTorch": r"(import\s+torch|from\s+torch)",
    "Scikit-Learn": r"(import\s+sklearn|from\s+sklearn)"
}

# === EXTENSIONES A EXCLUIR (solo basura) ===
EXCLUDED_EXT = {
    ".pdf", ".doc", ".docx",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".mp4", ".mov", ".avi",
    ".zip", ".rar", ".tar", ".gz",
    ".exe", ".dll", ".so",
    ".mp3", ".wav"
}

TOKEN = os.getenv("GH_TOKEN")
headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

IGNORE_DIRS = {"node_modules", "vendor", "dist", "build", ".git", ".github"}

visited = set()
framework_counts = {}

def fetch_directory(url):
    all_items = []
    page = 1
    while True:
        paged_url = f"{url}?page={page}&per_page=100"
        response = requests.get(paged_url, headers=headers)
        if response.status_code != 200:
            break
        data = response.json()
        if not isinstance(data, list) or len(data) == 0:
            break
        all_items.extend(data)
        page += 1
        if page > 100:
            break
    return all_items

def fetch_file(url):
    r = requests.get(url, headers=headers)
    return r.text if r.status_code == 200 else ""

def detect_frameworks(text):
    found = []
    for tech, pattern in FRAMEWORKS.items():
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            found.append(tech)
    return found

def scan_directory(url):
    if url in visited:
        return
    visited.add(url)

    contents = fetch_directory(url)

    for item in contents:
        if item["type"] == "dir":
            if item["name"] in IGNORE_DIRS:
                continue
            scan_directory(item["url"])

        elif item["type"] == "file":
            ext = os.path.splitext(item["name"])[1].lower()
            if ext in EXCLUDED_EXT:
                continue  # ignorar basura

            download_url = item.get("download_url")
            if not download_url:
                download_url = item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

            text = fetch_file(download_url)
            found = detect_frameworks(text)

            for tech in found:
                framework_counts[tech] = framework_counts.get(tech, 0) + 1


# === ANALIZAR TODOS LOS REPOS ===
repos = requests.get(
    f"https://api.github.com/users/{USER}/repos?per_page=100",
    headers=headers
).json()

for repo in repos:
    print(f"Analizando repo: {repo['name']}")
    root_url = repo["contents_url"].replace("{+path}", "")
    scan_directory(root_url)

# === RUTAS MANUALES (se mantienen todas) ===
scan_directory("https://api.github.com/repos/JulioArturoRodriguez/DESARROLLADOR-JAVA-SPRING-BOOT-TALENTO-TECH/contents/src/main/java/com/techlab/demo")
scan_directory("https://api.github.com/repos/JulioArturoRodriguez/DESARROLLADOR-JAVA-SPRING-BOOT-TALENTO-TECH/contents/src/main/resources")
scan_directory("https://api.github.com/repos/JulioArturoRodriguez/www.backend-cudi-utn-proyect-julio-rodriguez/contents")
scan_directory("https://api.github.com/repos/JulioArturoRodriguez/www.front-diplomatura-proyect-utncudi-julioi-rodiguez.com/contents/src/inicio")
scan_directory("https://api.github.com/repos/JulioArturoRodriguez/FORMAR--Back-End/contents")
scan_directory("https://api.github.com/repos/JulioArturoRodriguez/MODULO-3-MACHINE-LEARNING-UNAM-ARGENTINA-PROGRAMA-4.0/contents")

# === GUARDAR RESULTADOS ===
os.makedirs("output", exist_ok=True)

sorted_fw = dict(sorted(framework_counts.items(), key=lambda x: x[1], reverse=True))
total = sum(sorted_fw.values())

with open("output/frameworks.md", "w") as f:
    f.write("## Frameworks detectados (Front + Back + ML/DL)\n\n")
    if total == 0:
        f.write("No se detectaron frameworks.\n")
    else:
        for tech, count in sorted_fw.items():
            percent = (count / total) * 100
            f.write(f"- **{tech}**: {count} apariciones (~{percent:.1f}%)\n")

# === GRAFICO DE BARRAS ===
labels = list(sorted_fw.keys())
values = list(sorted_fw.values())
percents = [(v / total) * 100 for v in values] if total > 0 else []

height = max(6, len(labels) * 0.5)
plt.figure(figsize=(14, height))
plt.barh(labels, percents, color="green")
plt.title("Proporción de Frameworks Detectados (%)")
plt.xlabel("Porcentaje del código analizado")
plt.tight_layout()
plt.savefig("output/frameworks.png")
plt.close()
