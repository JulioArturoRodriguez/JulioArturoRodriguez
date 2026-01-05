import os
import re
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ========= CONFIG =========

USER = "JulioArturoRodriguez"

# SOLO LIBRERÍAS (no frameworks)
LIBRARIES = {
    "JWT": r"(jsonwebtoken|jwt)",
    "Bcrypt": r"(bcrypt)",
    "Mongoose": r"(mongoose)",

    "NumPy": r"(import\s+numpy|from\s+numpy)",
    "Pandas": r"(import\s+pandas|from\s+pandas)",
    "Matplotlib": r"(import\s+matplotlib|from\s+matplotlib)",

    "Lombok": r"(lombok)"
}

EXCLUDED_EXT = {
    ".pdf", ".doc", ".docx",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".mp4", ".mov", ".avi",
    ".zip", ".rar", ".tar", ".gz",
    ".exe", ".dll", ".so",
    ".mp3", ".wav",
    ".log",
    ".min.js",
    ".ipynb"
}

MAX_FILE_SIZE = 1_000_000

TOKEN = os.getenv("GH_TOKEN")
headers = {"Authorization": f"token {TOKEN}"} if TOKEN else {}

IGNORE_DIRS = {"node_modules", "vendor", "dist", "build", ".git", ".github", ".idea", ".vscode", "__pycache__"}

visited_dirs = set()
library_counts = {}


# ========= HELPERS =========

def fetch_directory(url: str):
    """Obtiene contenido de un directorio con paginación."""
    all_items = []
    page = 1
    while True:
        paged_url = f"{url}?page={page}&per_page=100"
        try:
            resp = requests.get(paged_url, headers=headers, timeout=15)
        except:
            break

        if resp.status_code != 200:
            break

        data = resp.json()
        if not isinstance(data, list) or not data:
            break

        all_items.extend(data)
        page += 1
        if page > 100:
            break

    return all_items


def build_raw_url(item: dict):
    """Construye URL RAW confiable."""
    if item.get("download_url"):
        return item["download_url"]

    html_url = item.get("html_url")
    if not html_url:
        return None

    return html_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")


def fetch_file(url: str):
    """Descarga archivo como texto."""
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code != 200:
            return ""
        try:
            return resp.text
        except UnicodeDecodeError:
            return resp.content.decode("latin-1", errors="ignore")
    except:
        return ""


def detect_libraries(text: str):
    """Devuelve lista de librerías encontradas."""
    found = []
    for lib, pattern in LIBRARIES.items():
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            found.append(lib)
    return found


def scan_directory(url: str):
    """Escanea recursivamente un directorio."""
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
                    continue

                raw_url = build_raw_url(item)
                if not raw_url:
                    continue

                text = fetch_file(raw_url)
                if not text:
                    continue

                found = detect_libraries(text)
                for lib in found:
                    library_counts[lib] = library_counts.get(lib, 0) + 1

        except:
            continue


# ========= MAIN =========

def main():
    print(f"Obteniendo repositorios de {USER}...")

    try:
        resp = requests.get(
            f"https://api.github.com/users/{USER}/repos?per_page=100",
            headers=headers,
            timeout=20
        )
    except:
        return

    if resp.status_code != 200:
        return

    repos = resp.json()
    if not isinstance(repos, list):
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

    # Crear carpeta output
    os.makedirs("output", exist_ok=True)

    # Ordenar resultados
    sorted_libs = dict(sorted(library_counts.items(), key=lambda x: x[1], reverse=True))
    total = sum(sorted_libs.values())

    # ========= GENERAR libraries.md (siempre) =========
    with open("output/libraries.md", "w", encoding="utf-8") as f:
        f.write("## 📚 Librerías detectadas\n\n")
        if total == 0:
            f.write("No se detectaron librerías.\n")
        else:
            for lib, count in sorted_libs.items():
                percent = (count / total) * 100 if total > 0 else 0
                f.write(f"- **{lib}**: {count} apariciones (~{percent:.1f}%)\n")

    # ========= GENERAR libraries.png (siempre) =========
    labels = list(sorted_libs.keys())
    values = list(sorted_libs.values())
    percents = [(v / total) * 100 for v in values] if total > 0 else []

    plt.figure(figsize=(14, max(6, len(labels) * 0.5)))

    if labels:
        plt.barh(labels, percents, color="blue")
        plt.title("Proporción de Librerías Detectadas (%)")
        plt.xlabel("Porcentaje del código analizado")
    else:
        plt.text(0.5, 0.5, "No se detectaron librerías", ha="center", va="center", fontsize=16)
        plt.title("Librerías Detectadas")

    plt.tight_layout()
    plt.savefig("output/libraries.png")
    plt.close()


if __name__ == "__main__":
    main()
