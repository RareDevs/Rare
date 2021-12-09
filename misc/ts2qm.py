import os

for f in os.listdir("../rare/resources/languages/"):
    if f.endswith(".ts") and f != "placeholder.ts":
        os.system("lrelease ../rare/languages/" + f)
