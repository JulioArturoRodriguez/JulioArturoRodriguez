import os
import re
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ========= CONFIG =========

USER = "JulioArturoRodriguez"

# Solo FRAMEWORKS (no librerías)
FRAMEWORKS = {
    # FRONT-END
    "React": r"(import\s+React\b|from\s+['\"]react['\"])",
    "React Router": r"(from\s+['\"]react-router['\"]|from\s+['\"]react-router-dom['\"])",
    "Styled Components": r"(from\s+['\"]styled-components['\"])",
    "Bootstrap": r"(bootstrap|class=\".*btn|class=\".*container)",

    # BACK-END
    "Express": r"(from\s+['\"]express['\"]|require\(['\"]express['\"]\))",
    "Spring Boot": r"@SpringBootApplication|spring-boot",
    "Spring Web": r"@RestController|@Controller|spring-web",
    "Spring Security": r"@EnableWebSecurity|spring-security",
    "Spring Data JPA": r"spring-data-jpa",
    "Hibernate": r"org\.hibernate|hibernate-core",

    # MACHINE LEARNING / DEEP LEARNING (solo frameworks)
    "TensorFlow": r"(import\s+tensorflow|from\s+tensorflow)",
    "Keras": r"(import\s+keras|from\s+keras)",
    "PyTorch": r"(import\s+torch|from\s+torch)",
    "Scikit-Learn": r"(import\s+sklearn|from\s+sklearn)"
}

# Extensiones que NO tiene sentido analizar (basura o muy pesadas)
EXCLUDED_EXT = {
    ".pdf", ".doc", ".docx",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".mp4", ".mov", ".avi",
    ".zip", ".rar", ".tar", ".gz",
    ".exe", ".dll", ".so",
    ".mp3", ".wav",
    ".log",
    ".min.js",
    ".ipynb"  # los frameworks ya aparecen en .py
}

# Tamaño máximo de archivo a leer (1 MB)
MAX_FILE_SIZE = 1_000_000

TOKEN = os.getenv("GH_TOKEN")
headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

IGNORE_DIRS = {"node_modules", "vendor", "dist", "build", ".git", ".github", ".idea", ".vscode", "__pycache__"}

visited_dirs = set()
framework_counts = {}


# ========= HELPERS =========

def fetch_directory(url: str):
    """Obtiene el contenido de un directorio de la API de GitHub con paginación."""
    all_items = []
    page = 1
    while True:
        paged_url = f"{url}?page={page}&per_page=100"
        try:
            resp = requests.get(paged_url, headers=headers, timeout=15)
        except Exception as e:
            print(f"[WARN] Error al pedir {paged_url}: {e}")
            break

        if resp.status_code != 200:
            print(f"[WARN] No se pudo leer el directorio ({resp.status_code}): {paged_url}")
            break

        data = resp.json()
        if not isinstance(data, list) or not data:
            break

        all_items.extend(data)
        page += 1
        if page > 100:
            break

    return all_items


def build_raw_url(item: dict) -> str | None:
    """Construye una URL RAW confiable para el archivo."""
    if item.get("download_url"):
        return item["download_url"]

    html_url = item.get("html_url")
    if not html_url:
        return None

    # https://github.com/user/repo/blob/branch/path -> raw.githubusercontent.com/user/repo/branch/path
    raw_url = html_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
    return raw_url


def fetch_file(url: str) -> str:
    """Descarga el contenido de un archivo como texto."""
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            print(f"[WARN] No se pudo leer archivo ({resp.status_code}): {url}")
            return ""
        # Intentar UTF-8, fallback a latin-1
        try:
            return resp.text
        except UnicodeDecodeError:
            return resp.content.decode("latin-1", errors="ignore")
    except Exception as e:
        print(f"[WARN] Error al descargar archivo {url}: {e}")
        return ""


def detect_frameworks(text: str):
    """Devuelve lista de frameworks encontrados en el texto."""
    found = []
    for tech, pattern in FRAMEWORKS.items():
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            found.append(tech)
    return found


def scan_directory(url: str):
    """Escanea recursivamente un directorio de la API de GitHub."""
    if url in visited_dirs:
        return
    visited_dirs.add(url)

    contents = fetch_directory(url)

    for item in contents:
        try:
            if item["type"] == "dir":
                if item["name"] in IGNORE_DIRS:
                    continue
                scan_directory(item["url"])

            elif item["type"] == "file":
                ext = os.path.splitext(item["name"])[1].lower()

                if ext in EXCLUDED_EXT:
                    continue

                size = item.get("size", 0)
                if isinstance(size, int) and size > MAX_FILE_SIZE:
                    # Saltar archivos gigantes
                    continue

                raw_url = build_raw_url(item)
                if not raw_url:
                    continue

                text = fetch_file(raw_url)
                if not text:
                    continue

                found = detect_frameworks(text)
                for tech in found:
                    framework_counts[tech] = framework_counts.get(tech, 0) + 1

        except Exception as e:
            print(f"[WARN] Error procesando item {item.get('path', item.get('name', '?'))}: {e}")
            continue


# ========= MAIN =========

def main():
    # Obtener repos del usuario
    print(f"Obteniendo repositorios de {USER}...")
    try:
        resp = requests.get(
            f"https://api.github.com/users/{USER}/repos?per_page=100",
            headers=headers,
            timeout=20
        )
    except Exception as e:
        print("ERROR al conectar con GitHub:", e)
        return

    if resp.status_code != 200:
        print("ERROR al obtener repositorios:", resp.status_code, resp.text)
        return

    repos = resp.json()
    if not isinstance(repos, list):
        print("La API no devolvió una lista de repositorios:", repos)
        return

    # Escanear todos los repos
    for repo in repos:
        name = repo.get("name", "SIN NOMBRE")
        print(f"Analizando repo: {name}")
        contents_url = repo.get("contents_url")
        if not contents_url:
            continue
        root_url = contents_url.replace("{+path}", "")
        scan_directory(root_url)

    # Rutas manuales importantes
    scan_directory("https://api.github.com/repos/JulioArturoRodriguez/DESARROLLADOR-JAVA-SPRING-BOOT-TALENTO-TECH/contents/src/main/java")
    scan_directory("https://api.github.com/repos/JulioArturoRodriguez/DESARROLLADOR-JAVA-SPRING-BOOT-TALENTO-TECH/contents/src/main/resources")
    scan_directory("https://api.github.com/repos/JulioArturoRodriguez/www.backend-cudi-utn-proyect-julio-rodriguez/contents")
    scan_directory("https://api.github.com/repos/JulioArturoRodriguez/www.front-diplomatura-proyect-utncudi-julioi-rodiguez.com/contents")
    scan_directory("https://api.github.com/repos/JulioArturoRodriguez/FORMAR--Back-End/contents")
    scan_directory("https://api.github.com/repos/JulioArturoRodriguez/MODULO-3-MACHINE-LEARNING-UNAM-ARGENTINA-PROGRAMA-4.0/contents")

    # Generar salida
    os.makedirs("output", exist_ok=True)

    sorted_fw = dict(sorted(framework_counts.items(), key=lambda x: x[1], reverse=True))
    total = sum(sorted_fw.values())

    with open("output/frameworks.md", "w", encoding="utf-8") as f:
        f.write("## 🚀 Frameworks detectados (solo frameworks reales)\n\n")
        if total == 0:
            f.write("No se detectaron frameworks.\n")
        else:
            for tech, count in sorted_fw.items():
                percent = (count / total) * 100 if total > 0 else 0
                f.write(f"- **{tech}**: {count} apariciones (~{percent:.1f}%)\n")

    # Gráfico
    labels = list(sorted_fw.keys())
    values = list(sorted_fw.values())
    percents = [(v / total) * 100 for v in values] if total > 0 else []

    if labels:
        height = max(6, len(labels) * 0.5)
        plt.figure(figsize=(14, height))
        plt.barh(labels, percents, color="green")
        plt.title("Proporción de Frameworks Detectados (%)")
        plt.xlabel("Porcentaje del código analizado")
        plt.tight_layout()
        plt.savefig("output/frameworks.png")
        plt.close()
    else:
        print("No hay frameworks para graficar.")


if __name__ == "__main__":
    main()
