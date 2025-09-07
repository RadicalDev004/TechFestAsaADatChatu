import kagglehub
import shutil
from pathlib import Path

def dataset_download():
    src_path = Path(kagglehub.dataset_download("prasad22/healthcare-dataset"))
    print("Cached at:", src_path)

    target = Path(__file__).resolve().parent
    print("Target folder:", target)

    # remove old files
    for item in target.iterdir():
        if item.is_dir() and item.name == "healthcare-dataset":
            shutil.rmtree(item)

    for child in src_path.iterdir():
        if child.is_file():
            shutil.copy2(child, target / child.name)
        elif child.is_dir():
            # copying subfolders
            shutil.copytree(child, target / child.name, dirs_exist_ok=True)

    print("Dataset copied into:", target.resolve())

if __name__ == "__main__":
    dataset_download()
