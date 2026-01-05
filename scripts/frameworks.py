import requests
import os
import re
import json

# === Matplotlib para generar imagen en GitHub Actions ===
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

USER = "JulioArturoRodriguez"

# === FRAMEWORKS DETECTADOS SOLO POR CÓDIGO REAL ===
FRAMEWORKS_BY_LANG = {
    "py": {
        "NumPy": r"\bimport\s+numpy\b|\bfrom\s+numpy\b",
        "Pandas": r"\bimport\s+pandas\b|\bfrom\s+pandas\b",
        "Matplotlib": r"\bimport\s+matplotlib\b|\bfrom\s+matplotlib\b",
        "Scikit-Learn": r"\bimport\s+sklearn\b|\bfrom\s+sklearn\b",
        "TensorFlow": r"\bimport\s+tensorflow\b|\bfrom\s+tensorflow\b",
        "Keras": r"\bimport\s+keras\b|\bfrom\s+keras\b",
        "PyTorch": r"\bimport\s+torch\b|\bfrom\s+torch\b"
    },

    "js": {
        "React": r"from\s+['\"]react['\"]",
        "React Router": r"from\s+['\"]react-router['\"]",
        "Styled Components": r"from\s+['\"]styled-components['\"]",
        "Bootstrap": r"from\s+['\"]bootstrap['\"]",
        "Express": r"(from\s+['\"]express['\"]|require\(['\"]express['\"]\))",
        "Node.js": r"(require\(|module\.exports\b)",
        "JWT": r"(from\s+['\"]jsonwebtoken['\"]|require\(['\"]jsonwebtoken['\"]\))",
        "Bcrypt": r"(from\s+['\"]bcrypt['\"]|require\(['\"]bcrypt['\"]\))",
        "Mongoose": r"(from\s+['\"]mongoose['\"]|require\(['\"]mongoose['\"]\))"
    },

    "ts": {
        "React": r"from\s+['\"]react['\"]",
        "React Router": r"from\s+['\"]react-router['\"]",
        "Styled Components": r"from\s+['\"]styled-components['\"]",
        "Bootstrap": r"from\s+['\"]bootstrap['\"]",
        "Express": r"from\s+['\"]express['\"]",
        "Node.js": r"import\s+.*from\s+['\"]fs['\"]",
        "JWT": r"from\s+['\"]jsonwebtoken['\"]",
        "Bcrypt": r"from\s+['\"]bcrypt['\"]",
        "Mongoose": r"from\s+['\"]mongoose['\"]"
    },

    "java": {
        "Spring Boot": r"@SpringBootApplication",
        "Spring Web": r"@RestController",
        "Spring Security": r"@EnableWebSecurity",
        "Spring Data JPA": r"@Entity",
        "Hibernate": r"@Entity",
        "Lombok": r"@(Data|Getter|Setter|Builder)"
    },

    "php": {
        "Laravel": r"(use\s+Illuminate\\|namespace\s+App\\)"
    }
}

# === TOKEN ===
TOKEN = os.getenv("GH_TOKEN")
headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

# Solo analizamos archivos de código real
VALID_EXT = (".py", ".js", ".ts", ".java", ".php")

IGNORE_DIRS = {"node_modules", "vendor", "dist", "build", ".git", ".github"}

visited = set()
framework_counts = {}

def fetch_file(url):
    r = requests.get(url, headers=headers)
    return r.text if r.status_code == 200 else ""

def detect_frameworks(text, ext):
    found = []
    lang = ext.replace(".", "")
    if lang not in FRAMEWORKS_BY_LANG:
        return found

    for tech, pattern in FRAMEWORKS_BY_LANG[lang].items():
        if re.search(pattern, text):
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
            ext = os.path.splitext(item["name"])[1]
            if ext not in VALID_EXT:
                continue

            text = fetch_file(item["download_url"])
            found = detect_frameworks(text, ext)

            for tech in found:
                framework_counts[tech] = framework_counts.get(tech, 0) + 1


# === OBTENER REPOS ===
repos = requests.get(
    f"https://api.github.com/users/{USER}/repos?per_page=100",
    headers=headers
).json()

for repo in repos:
    print(f"Analizando repo: {repo['name']}")
    root_url = repo["contents_url"].replace("{+path}", "")
    scan_directory(root_url)

# === GUARDAR RESULTADOS ===
os.makedirs("output", exist_ok=True)

sorted_fw = dict(sorted(framework_counts.items(), key=lambda x: x[1], reverse=True))

with open("output/frameworks.json", "w") as f:
    json.dump(sorted_fw, f, indent=4)

with open("output/frameworks.md", "w") as f:
    f.write("## Frameworks detectados automáticamente (solo código real)\n\n")
    if not sorted_fw:
        f.write("No se detectaron frameworks.\n")
    else:
        for tech, count in sorted_fw.items():
            f.write(f"- **{tech}**: {count} apariciones en código\n")

# === GENERAR IMAGEN EN BARRAS ===
plt.figure(figsize=(12, 6))

if sorted_fw:
    plt.bar(sorted_fw.keys(), sorted_fw.values(), color="green")
else:
    plt.text(0.5, 0.5, "No se detectaron frameworks",
             ha="center", va="center", fontsize=14)

plt.title("Frameworks detectados (solo código real)")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig("output/frameworks.png")
plt.close()
