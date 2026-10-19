
import sqlite3
from pathlib import Path
from PIL import Image

DB_PATH = Path(r"C:\Users\ADMIN\Downloads\archive\metadata.db")
IMAGE_DIR = Path(r"C:\Users\ADMIN\Downloads\archive\bin-images-224x224")

connection = sqlite3.connect(
    DB_PATH.as_uri() + "?mode=ro",
    uri=True
)

cursor = connection.cursor()
cursor.execute("SELECT name FROM metadata")

database_names = {row[0] for row in cursor.fetchall()}
connection.close()

image_paths = list(IMAGE_DIR.rglob("*.jpg"))
image_names = {path.name for path in image_paths}

missing_images = database_names - image_names
unmatched_images = image_names - database_names

print("Database filenames:", len(database_names))
print("Actual JPG filenames:", len(image_names))
print("Database entries without images:", len(missing_images))
print("Images without database entries:", len(unmatched_images))

print("\nChecking image readability...")
bad_images = []

for i, path in enumerate(image_paths, start=1):
    try:
        with Image.open(path) as img:
            img.verify()
    except Exception as exc:
        bad_images.append((path.name, str(exc)))

    if i % 50000 == 0:
        print(f"Checked {i:,} images")

print("\nUnreadable images:", len(bad_images))
print("Examples of unreadable images:", bad_images[:10])
