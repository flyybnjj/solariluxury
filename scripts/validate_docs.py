import os
import re

docs_dir = r"C:\Users\avalo\Documents\tienda\docs"
index_file = os.path.join(docs_dir, "index.html")

with open(index_file, "r", encoding="utf-8") as f:
    content = f.read()

srcs = re.findall(r'src=["\']([^"\']+)["\']', content)
hrefs = re.findall(r'href=["\']([^"\']+)["\']', content)

missing = []
for ref in srcs:
    if ref.startswith("http") or ref.startswith("#"):
        continue
    clean = ref.split("?")[0]
    if clean.startswith("./"):
        clean = clean[2:]
    full = os.path.join(docs_dir, clean.replace("/", os.sep))
    if not os.path.exists(full):
        missing.append(("src", ref, full))

for ref in hrefs:
    if ref.startswith("http") or ref.startswith("#"):
        continue
    clean = ref.split("?")[0]
    if clean.startswith("./"):
        clean = clean[2:]
    full = os.path.join(docs_dir, clean.replace("/", os.sep))
    if not os.path.exists(full) and not os.path.exists(os.path.join(full, "index.html")):
        missing.append(("href", ref, full))

if missing:
    print(f"Missing {len(missing)} items:")
    for t, r, f in missing:
        print(f"  [{t}] {r} -> {f}")
else:
    print("ALL ASSETS AND LINKS IN docs/index.html VERIFIED AND PRESENT ON DISK! (100% OK)")
