"""
One-time setup: download NLTK corpora required by TextBlob.

Run once after creating the virtual environment:
    .venv\\Scripts\\python.exe setup_nltk.py
"""
import subprocess
import sys

subprocess.run(
    [sys.executable, "-m", "textblob.download_corpora"],
    check=True,
)
print("NLTK corpora ready.")
