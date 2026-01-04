# Workflow updated
name: Update Framework Stats

permissions:
  contents: write

on:
  schedule:
    - cron: "0 0 * * *"   # Cada 24 horas a medianoche UTC
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: pip install matplotlib requests

      - name: Run framework analysis
        run: python scripts/frameworks.py

      - name: Update README with framework stats
        run: |
          sed -i '/<!-- AUTO-FRAMEWORKS -->/r output/frameworks.md' README.md

      - name: Commit and push results
        run: |
          git config --global user.name "GitHub Action"
          git config --global user.email "action@github.com"
          git add output/frameworks.png output/frameworks.json output/frameworks.md README.md
          git commit -m "Update framework stats" || echo "No changes to commit"
          git push
