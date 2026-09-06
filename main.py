import requests
import os
import sys
import time
import argparse

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
RATING_THRESHOLD = get_optional_int_env("RATING_THRESHOLD", 60)

parser = argparse.ArgumentParser(description="Stash Backup Helper")
parser.add_argument('--sync', default=None, help='Sync destination')
args = parser.parse_args()

os.makedirs(SYMLINK_DIR , exist_ok=True)

def dir_non_empty(path: str) -> bool:
    with os.scandir(path) as it:
        return next(it, None) is not None

def check_sync_valid() -> str:
    if not os.path.isdir(args.sync):
        return f"sync destination unavailable: {args.sync}"
    if not dir_non_empty(args.sync):
        return f"sync destination empty: {args.sync}"
    if not dir_non_empty(SYMLINK_DIR):
        return f"source dir empty/invalid: {SYMLINK_DIR}"
    return ""

def run_sync():
    rsync = [
        "rsync", "-avL", "--no-o", "--no-g", "--no-perms",
        "--size-only", "--stats", "--delete",
        os.path.join(SYMLINK_DIR, ""), os.path.join(args.sync, ""),
    ]
    os.system(" ".join(f'"{a}"' for a in rsync))

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
        if rating is not None and rating > RATING_THRESHOLD:
            file_paths = [f["path"] for f in scene.get("files", [])]
            for f in file_paths:
                if SYMLINK_DIR in f:
                    print("Skip Symlink dir in", f)
                    continue
                symlink_path = os.path.join(SYMLINK_DIR , str(scene['id']).zfill(9) + "_" + os.path.basename(f))
                relative_path = os.path.relpath(f, SRC_DIR)
                relative_path = os.path.join("..", relative_path)
                if not os.path.exists(symlink_path):
                    try:
                        os.symlink(relative_path, symlink_path)
                        print(f"Symlinked {relative_path} -> {symlink_path}")
                    except Exception as e:
                        print(f"Error linking {f}: {e}")

    os.system(f"du -sh -L \"{SYMLINK_DIR}\"")

    if args.sync:
        reason = check_sync_valid()
        if reason:
            print("ERROR: skipping sync:", reason)
        else:
            run_sync()

    print("sleep", UPDATE_INTERVAL, "seconds")
    time.sleep(UPDATE_INTERVAL)
