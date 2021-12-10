import os

for f in os.listdir(os.path.join(os.path.dirname(__file__), "../rare/resources/languages/")):
    if f.endswith(".ts") and f != "placeholder.ts":
        os.system(f"lrelease {os.path.join(os.path.dirname(__file__), '../rare/resources/languages/', f)}")
