import requests
import matplotlib.pyplot as plt
import json
import os

USER = "JulioArturoRodriguez"

# Obtener repos públicos del usuario
repos_url = f"https://api.github.com/users/{USER}/repos"
repos = requests.get(repos_url).json()

language_totals = {}

# Recorrer cada repo y sumar bytes por lenguaje
for repo in repos:
    langs = requests.get(repo["languages_url"]).json()
    for lang, bytes_count in langs.items():
        language_totals[lang] = language_totals.get(lang, 0) + bytes_count

# Calcular porcentajes
total_bytes = sum(language_totals.values())
language_percentages = {
    lang: round((count / total_bytes) * 100, 2)
    for lang, count in language_totals.items()
}

# Ordenar lenguajes por porcentaje
sorted_langs = dict(sorted(language_percentages.items(), key=lambda x: x[1], reverse=True))

# Crear carpeta output si no existe
os.makedirs("output", exist_ok=True)

# Guardar JSON con los datos
with open("output/languages.json", "w") as f:
    json.dump(sorted_langs, f, indent=4)

# Guardar ranking en texto (Markdown)
with open("output/languages.md", "w") as f:
    f.write("## 📊 Lenguajes más usados (actualizado automáticamente)\n\n")
    for lang, pct in sorted_langs.items():
        f.write(f"- **{lang}**: {pct}%\n")

# Generar gráfico de barras
plt.figure(figsize=(12, 6))
plt.bar(sorted_langs.keys(), sorted_langs.values(), color='skyblue')
plt.title(f"Porcentaje de lenguajes usados por {USER} en GitHub")
plt.xlabel("Lenguajes")
plt.ylabel("Porcentaje (%)")
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()

# Guardar imagen
plt.savefig("output/languages.png")
