import requests
import os
import re
import json
import matplotlib.pyplot as plt

USER = "JulioArturoRodriguez"

ML_TECH = {
    "TensorFlow": r"tensorflow",
    "PyTorch": r"torch",
    "Keras": r"keras",
    "Scikit-Learn": r"sklearn",
    "OpenCV": r"opencv"
}

def fetch_file(url):
    r = requests.get(url)
    return r.text if r.status_code == 200 else ""

def detect_ml(text):
    found = []
    for tech, pattern in ML_TECH.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.append(tech)
    return found

repos = requests.get(f"https://api.github.com/users/{USER}/repos").json()

ml_counts = {}

for repo in repos:
    contents = requests.get(repo["contents_url"].replace("{+path}", "")).json()
    if isinstance(contents, dict):
        continue

    for item in contents:
        if item["type"] == "file":
            text = fetch_file(item["download_url"])
            found = detect_ml(text)
            for tech in found:
                ml_counts[tech] = ml_counts.get(tech, 0) + 1

os.makedirs("output", exist_ok=True)

sorted_ml = dict(sorted(ml_counts.items(), key=lambda x: x[1], reverse=True))

with open("output/ml_stats.json", "w") as f:
    json.dump(sorted_ml, f, indent=4)

with open("output/ml_stats.md", "w") as f:
    f.write("## Machine Learning detectado automáticamente\n\n")
    for tech, count in sorted_ml.items():
        f.write(f"- **{tech}**: {count} repos\n")

if sorted_ml:
    plt.figure(figsize=(12, 6))
    plt.bar(sorted_ml.keys(), sorted_ml.values(), color="orange")
    plt.title("Machine Learning detectado")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("output/ml_stats.png")
    plt.close()
