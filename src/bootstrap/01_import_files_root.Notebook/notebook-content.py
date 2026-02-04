# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

# ---------------------------------------------
# Fabric Quickstart (workspace-agnostic, ABFS-based)
# - Create (or reuse) Lakehouse in the *current* workspace
# - Import ALL text assets from GitHub BRANCH ROOT into ABFS .../Files/quickstart
# - Preserve subfolders; exclude 'bootstrap' by default
# ---------------------------------------------

# ---------------------------------------------
# Imports
# ---------------------------------------------
import notebookutils as nb
import urllib.request, json, os, time, traceback
from datetime import datetime
import requests

# ---------------------------------------------
# 1) Configure your repo & lakehouse
# ---------------------------------------------
# ---- GitHub source ----
GITHUB_OWNER  = "bcgov"
GITHUB_REPO   = "nr-dap-fabric-quickstart"  # Update if needed
GITHUB_BRANCH = "main"

# Optional: GitHub token to avoid rate limits (fine-grained or classic, read-only)
GITHUB_TOKEN = None  # e.g., "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# ---- Lakehouse settings ----
LAKEHOUSE_NAME = "quickstart_lh_test"
LAKEHOUSE_DESC = "Lakehouse for Fabric Medallion Quickstart"

# ---- File handling & exclusions ----
TEXT_EXTS = {".csv", ".tsv", ".json", ".md", ".txt", ".py", ".sql", ".yml", ".yaml"}

# Exclude these directories at ANY depth (path segment match)
EXCLUDE_DIRS = {"bootstrap", ".github"}

# Exclude these basenames (any path), case-insensitive
EXCLUDE_FILES = {"license", "contributing.md", ".gitignore", "code_of_conduct.md", "code-of-conduct.md"}

# Strip a leading "src/" from repo paths when copying to Lakehouse
STRIP_PREFIX = "src/"

# Whether to copy binaries via nb.fs.cp (HTTP -> ABFS)
COPY_BINARIES = False

DEBUG = False  # flip to True only when troubleshooting

# ---------------------------------------------
# 2) Helper functions
# ---------------------------------------------
def log(msg: str):
    print(f"[{datetime.utcnow().isoformat()}Z] {msg}")

def debug_exception(prefix: str, ex: Exception):
    if DEBUG:
        log(f"{prefix}: {repr(ex)}")
        traceback.print_exc()
    else:
        log(f"{prefix}: {ex.__class__.__name__}: {ex}")

def _headers():
    return {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

def _http_json(url: str):
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req) as resp:
        if resp.status != 200:
            raise RuntimeError(f"GET {url} -> HTTP {resp.status}")
        return json.loads(resp.read().decode("utf-8"))

def _http_text(url: str) -> str:
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req) as resp:
        if resp.status != 200:
            raise RuntimeError(f"GET {url} -> HTTP {resp.status}")
        return resp.read().decode("utf-8")

def list_branch_tree(owner: str, repo: str, branch: str):
    """GitHub Trees API: recursive listing of files at branch tip
    Returns only blobs (files).
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    data = _http_json(url)
    return [item for item in data.get("tree", []) if item.get("type") == "blob"]

def raw_url(owner: str, repo: str, branch: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"

def is_text_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in TEXT_EXTS

def fabric_token() -> str:
    """Acquire an Entra token for Fabric REST API calls.
    Prefer notebookutils.credentials; fallback to mssparkutils.
    """
    try:
        return nb.credentials.getToken("https://api.fabric.microsoft.com/")
    except Exception:
        from notebookutils import mssparkutils
        return mssparkutils.credentials.getToken("https://api.fabric.microsoft.com/")

def wait_for_lakehouse_props(name: str, workspace_id: str, retries: int = 12, sleep_s: int = 5):
    last = None
    for i in range(retries):
        try:
            return nb.lakehouse.getWithProperties(name=name, workspaceId=workspace_id)
        except Exception as e:
            last = e
            if DEBUG:
                debug_exception(f"Waiting for lakehouse properties (attempt {i+1}/{retries})", e)
            time.sleep(sleep_s)
    raise RuntimeError(f"Lakehouse exists but properties not readable after retries. Last error: {last}")

def create_schema_enabled_lakehouse(workspace_id: str, lakehouse_name: str, description: str):
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/lakehouses"
    headers = {
        "Authorization": f"Bearer {fabric_token()}",
        "Content-Type": "application/json"
    }
    payload = {
        "displayName": lakehouse_name,
        "description": description,
        "creationPayload": {"enableSchemas": True}
    }
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code == 201:
        log("Created lakehouse (201).")
        return
    if r.status_code == 202:
        op_url = r.headers.get("Location")
        retry_after = int(r.headers.get("Retry-After", "5"))
        log(f"Provisioning started (202). Polling operation: {op_url}")
        if not op_url:
            raise RuntimeError("Create returned 202 but no Location header was provided.")
        while True:
            op = requests.get(op_url, headers=headers)
            op.raise_for_status()
            data = op.json()
            status = (data.get("status") or data.get("operationStatus") or "").lower()
            if status in ("succeeded", "success", "completed"):
                log("Provisioning succeeded.")
                return
            if status in ("failed", "error"):
                raise RuntimeError(f"Provisioning failed: {data}")
            time.sleep(retry_after)
    raise RuntimeError(f"Create lakehouse failed: HTTP {r.status_code} - {r.text}")

def ensure_schema_enabled_lakehouse(workspace_id: str, lakehouse_name: str, description: str):
    try:
        props = nb.lakehouse.getWithProperties(name=lakehouse_name, workspaceId=workspace_id)
        schema_enabled = "defaultSchema" in props.get("properties", {})
        log(f"Lakehouse exists. schemaEnabled={schema_enabled}")
        if not schema_enabled:
            raise RuntimeError(
                f"Lakehouse '{lakehouse_name}' exists but is NOT schema-enabled. "
                "Recreate using creationPayload.enableSchemas=true."
            )
        return props
    except Exception as e:
        msg = str(e).lower()
        if "artifactnotfoundexception" in msg or "not found" in msg:
            log(f"Lakehouse '{lakehouse_name}' not found; creating schema-enabled via REST API...")
            if DEBUG:
                debug_exception("Details (expected on first run)", e)
            create_schema_enabled_lakehouse(workspace_id, lakehouse_name, description)
            return wait_for_lakehouse_props(lakehouse_name, workspace_id)
        debug_exception("Unexpected error while checking lakehouse", e)
        raise

# ---------------------------------------------
# 3) Ensure Lakehouse exists and is schema-enabled
# ---------------------------------------------
WORKSPACE_ID = spark.conf.get("trident.workspace.id")
log(f"WorkspaceId: {WORKSPACE_ID}")
log(f"Lakehouse name: {LAKEHOUSE_NAME}")

lh_props = ensure_schema_enabled_lakehouse(WORKSPACE_ID, LAKEHOUSE_NAME, LAKEHOUSE_DESC)
log("✅ Lakehouse ready (schema-enabled).")

# Resolve ABFS path for this Lakehouse
lh_props = nb.lakehouse.getWithProperties(name=LAKEHOUSE_NAME, workspaceId=WORKSPACE_ID)
ABFS_ROOT = lh_props["properties"]["abfsPath"]  # e.g., abfss://<ws>@onelake.dfs.fabric.microsoft.com/<lakehouse>
DEST_DIR  = f"{ABFS_ROOT}/Files/quickstart"
print("ABFS root:", ABFS_ROOT)
print("Destination (ABFS):", DEST_DIR)

# Ensure destination root exists
nb.fs.mkdirs(DEST_DIR)

# ---------------------------------------------
# 4) List branch tree and copy to Lakehouse (with exclusions & src stripping)
# ---------------------------------------------
print("Listing branch tree (this may take a moment)...")
tree = list_branch_tree(GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH)

copied_text, copied_bin, skipped = 0, 0, 0
for item in tree:
    repo_path = item["path"]                 # e.g., 'src/utils/helpers.py'
    parts = repo_path.split("/")             # ['src', 'utils', 'helpers.py']
    base = parts[-1].lower()                      # 'helpers.py'

    # Exclude directories at ANY depth (check only folder segments)
    if any(part in EXCLUDE_DIRS for part in parts[:-1]):
        skipped += 1
        continue

    # Exclude specific filenames anywhere
    if base in EXCLUDE_FILES:
        skipped += 1
        continue

    # Normalize path by stripping leading 'src/' if present
    if repo_path.startswith(STRIP_PREFIX):
        norm_path = repo_path[len(STRIP_PREFIX):]
    else:
        norm_path = repo_path

    # Compute destination folder (preserve subfolders after normalization)
    dest_dir = f"{DEST_DIR}/{os.path.dirname(norm_path)}" if "/" in norm_path else DEST_DIR
    try:
        nb.fs.mkdirs(dest_dir)
    except Exception as e:
        print(f"mkdirs({dest_dir}) -> {e}")

    if is_text_file(repo_path):
        try:
            text = _http_text(raw_url(GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH, repo_path))
            nb.fs.put(f"{dest_dir}/{os.path.basename(norm_path)}", text, overwrite=True)
            copied_text += 1
            print(f"Text copied: {repo_path}  ->  {dest_dir}/{os.path.basename(norm_path)}")
        except Exception as e:
            skipped += 1
            print(f"Skip text {repo_path}: {e}")
    else:
        if COPY_BINARIES:
            try:
                src = raw_url(GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH, repo_path)
                dst = f"{dest_dir}/{os.path.basename(norm_path)}"
                nb.fs.cp(src, dst, recurse=False)  # direct copy across filesystems
                copied_bin += 1
                print(f"Binary copied: {repo_path}  ->  {dst}")
            except Exception as e:
                skipped += 1
                print(f"Skip binary {repo_path}: {e}")
        else:
            skipped += 1

print(f"✅ Done. {copied_text} text file(s) and {copied_bin} binary file(s) imported into {DEST_DIR}. Skipped {skipped}.")
print("Explore them under Lakehouse → Files → quickstart in the left pane.")