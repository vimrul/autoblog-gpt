import os

required_dirs = [
    "storage/articles",
    "storage/images",
    "config"
]

for directory in required_dirs:
    os.makedirs(directory, exist_ok=True)
