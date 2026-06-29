import csv
import glob
import json
import os
import shutil

CSV_DIR = "data"
OUT_DIR = "output"

CHUNK_SIZE = 30000

# تنظيف المجلد القديم
if os.path.exists(OUT_DIR):
    shutil.rmtree(OUT_DIR)

os.makedirs(OUT_DIR, exist_ok=True)

chunk = []
part = 1
total = 0
files = []


def save_chunk(rows, index):
    filename = f"part_{index:04}.json"

    with open(
        os.path.join(OUT_DIR, filename),
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(rows, f, ensure_ascii=False)

    files.append(filename)
    print("Saved", filename, len(rows))


csv_files = sorted(glob.glob(os.path.join(CSV_DIR, "*.csv")))

for csv_file in csv_files:

    print("Reading", csv_file)

    with open(csv_file, encoding="utf-8-sig", newline="") as f:

        reader = csv.reader(f)

        for row in reader:

            if len(row) < 5:
                continue

            username = row[0].strip()
            kind = row[1].strip()
            name = row[2].strip()

            try:
                subscribers = int(row[3])
            except:
                subscribers = 0

            bio = row[4].strip()

            chunk.append({
                "username": username,
                "type": kind,
                "name": name,
                "followers": subscribers,
                "bio": bio
            })

            total += 1

            if len(chunk) >= CHUNK_SIZE:
                save_chunk(chunk, part)
                chunk = []
                part += 1

if chunk:
    save_chunk(chunk, part)

manifest = {
    "total": total,
    "parts": len(files),
    "chunk_size": CHUNK_SIZE,
    "files": files
}

with open(
    os.path.join(OUT_DIR, "manifest.json"),
    "w",
    encoding="utf-8"
) as f:
    json.dump(manifest, f, indent=2)

print()
print("Done")
print("Channels :", total)
print("Parts    :", len(files))
