import requests
import os
import sys
import time

def get_str_env(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        print("ERROR: Required env var", key, "not set probably")
        sys.exit(1)

    return value

def get_optional_int_env(key: str, default: int) -> int:
    try:
        value = int(os.getenv(key, str(default)))
    except ValueError:
        value = default

    return value

API_KEY = get_str_env("STASH_API_KEY")
GRAPHQL_URL = get_str_env("STASH_URL")
SYMLINK_DIR = get_str_env("SYMLINK_PATH")
SRC_DIR = get_str_env("SRC_PATH")
UPDATE_INTERVAL = get_optional_int_env("UPDATE_INTERVAL", 24*3600)

os.makedirs(SYMLINK_DIR , exist_ok=True)

query = """
query {
  allScenes {
    id
    rating100
    files {
      path
    }
  }
}
"""

headers = {
    "ApiKey": API_KEY,
    "Content-Type": "application/json"
}

while True:
    response = requests.post(
        GRAPHQL_URL,
        json={"query": query},
        headers=headers
    )

    data = response.json()
    for scene in data["data"]["allScenes"]:
        rating = scene.get("rating100")
        if rating is not None and rating > 60:
            file_paths = [f["path"] for f in scene.get("files", [])]
            for f in file_paths:
                symlink_path = os.path.join(SYMLINK_DIR , str(scene['id']).zfill(9) + "_" + os.path.basename(f))
                relative_path = os.path.relpath(f, SRC_DIR)
                relative_path = os.path.join("..", relative_path)
                if not os.path.exists(symlink_path):
                    try:
                        os.symlink(relative_path, symlink_path)
                        print(f"Symlinked {relative_path} -> {symlink_path}")
                    except Exception as e:
                        print(f"Error linking {f}: {e}")

    print("sleep", UPDATE_INTERVAL, "seconds")
    time.sleep(UPDATE_INTERVAL)
