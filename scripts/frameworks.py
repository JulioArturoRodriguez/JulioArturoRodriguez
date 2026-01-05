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
        "React": r"(from\s+['\"]react['\"]|import\s+ReactDOM|import\s+.*\s+from\s+['\"]react['\"])",
        "React Router": r"(from\s+['\"]react-router['\"]|from\s+['\"]react-router-dom['\"])",
        "Styled Components": r"(from\s+['\"]styled-components['\"])",
        "Bootstrap": r"(from\s+['\"]bootstrap['\"]|from\s+['\"]react-bootstrap['\"])",
        "Express": r"(import\s+.*\s+from\s+['\"]express['\"]|require\(['\"]express['\"]\))",
        "Node.js": r"(require\(|module\.exports\b)",
        "JWT": r"(from\s+['\"]jsonwebtoken['\"]|require\(['\"]jsonwebtoken['\"]\)|import\s+.*\s+from\s+['\"]jsonwebtoken['\"])",
        "Bcrypt": r"(from\s+['\"]bcrypt['\"]|require\(['\"]bcrypt['\"]\)|from\s+['\"]bcryptjs['\"]|require\(['\"]bcryptjs['\"]\))",
        "Mongoose": r"(from\s+['\"]mongoose['\"]|require\(['\"]mongoose['\"]\))"
    },

    "ts": {
        "React": r"(from\s+['\"]react['\"])",
        "React Router": r"(from\s+['\"]react-router['\"]|from\s+['\"]react-router-dom['\"])",
        "Styled Components": r"(from\s+['\"]styled-components['\"])",
        "Bootstrap": r"(from\s+['\"]bootstrap['\"]|from\s+['\"]react-bootstrap['\"])",
        "Express": r"(from\s+['\"]express['\"])",
        "Node.js": r"(import\s+.*\s+from\s+['\"]fs['\"]|import\s+.*\s+from\s+['\"]path['\"])",
        "JWT": r"(from\s+['\"]jsonwebtoken['\"])",
        "Bcrypt": r"(from\s+['\"]bcrypt['\"]|from\s+['\"]bcryptjs['\"])",
        "Mongoose": r"(from\s+['\"]mongoose['\"])"
    },

    "java": {
        "Spring Boot": r"@SpringBootApplication|org\.springframework\.boot",
        "Spring Web": r"@RestController|@Controller|org\.springframework\.web",
        "Spring Security": r"@EnableWebSecurity|org\.springframework\.security",
        "Spring Data JPA": r"@Entity|org\.springframework\.data\.jpa",
        "Hibernate": r"@Entity|org\.hibernate",
        "Lombok": r"@(Data|Getter|Setter|Builder|NoArgsConstructor|AllArgsConstructor)|lombok\."
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

# === GENERAR IMÁGENES EN BARRAS (divididas automáticamente) ===

def chunk_list(data, size):
    items = list(data.items())
    for i in range(0, len(items), size):
        yield items[i:i + size]

if not sorted_fw:
    plt.figure(figsize=(10, 4))
    plt.text(0.5, 0.5, "No se detectaron frameworks",
             ha="center", va="center", fontsize=14)
    plt.savefig("output/frameworks_0.png")
    plt.close()
else:
    chunk_size = 10  # frameworks por imagen
    index = 0

    for chunk in chunk_list(sorted_fw, chunk_size):
        labels = [x[0] for x in chunk]
        values = [x[1] for x in chunk]

        height = max(6, len(labels) * 0.6)

        plt.figure(figsize=(14, height))
        plt.barh(labels, values, color="green")
        plt.title(f"Frameworks detectados (parte {index + 1})")
        plt.xlabel("Cantidad de apariciones")
        plt.tight_layout()

        plt.savefig(f"output/frameworks_{index}.png")
        plt.close()

        index += 1
