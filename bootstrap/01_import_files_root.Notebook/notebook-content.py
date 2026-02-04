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

import notebookutils as nb
import urllib.request, json, os

# ---- Configure your repo ----
GITHUB_OWNER  = "bcgov"
GITHUB_REPO   = "nr-dap-azure"
GITHUB_BRANCH = "fabric-lakehouse-medallion-quickstart"  # branch whose *root* you want to copy

# Optional: GitHub token to avoid rate limits (fine-grained or classic, read-only)
GITHUB_TOKEN = None  # e.g., "ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# ---- Lakehouse settings ----
LAKEHOUSE_NAME = "lh_sales_core"
LAKEHOUSE_DESC = "Lakehouse for Fabric Medallion Quickstart"

# ---- File filters ----
# Treat these extensions as TEXT (copied via nb.fs.put). Others are skipped unless COPY_BINARIES=True.
TEXT_EXTS = {".csv", ".tsv", ".json", ".md", ".txt", ".py", ".sql", ".yml", ".yaml"}

# ✅ Exclude the committed notebook folder by default
EXCLUDE_DIRS = {"bootstrap"}  # add more top-level folders here if needed

# Toggle if you also want to bring binaries (images, zip, parquet parts) via fs.cp
COPY_BINARIES = False

# ---------------------------------------------
# Helpers
# ---------------------------------------------
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
    # GitHub Trees API: recursive listing of files at branch tip
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    data = _http_json(url)
    return [item for item in data.get("tree", []) if item.get("type") == "blob"]

def raw_url(owner: str, repo: str, branch: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"

def is_text_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in TEXT_EXTS

# ---------------------------------------------
# 1) Resolve current workspace + ensure schema-enabled Lakehouse
# ---------------------------------------------

import requests, time, traceback
from datetime import datetime

DEBUG = False  # flip to True only when troubleshooting

def log(msg: str):
    print(f"[{datetime.utcnow().isoformat()}Z] {msg}")

def debug_exception(prefix: str, ex: Exception):
    """
    Print full stack traces only when DEBUG=True.
    """
    if DEBUG:
        log(f"{prefix}: {repr(ex)}")
        traceback.print_exc()
    else:
        log(f"{prefix}: {ex.__class__.__name__}: {ex}")

def fabric_token() -> str:
    """
    Acquire an Entra token for Fabric REST API calls.
    """
    # Prefer notebookutils.credentials if available; otherwise fallback to mssparkutils
    try:
        return nb.credentials.getToken("https://api.fabric.microsoft.com/")
    except Exception:
        from notebookutils import mssparkutils
        return mssparkutils.credentials.getToken("https://api.fabric.microsoft.com/")

def wait_for_lakehouse_props(name: str, workspace_id: str, retries: int = 12, sleep_s: int = 5):
    """
    After create, metadata can take a short time to appear. This avoids timing flakiness.
    Create Lakehouse supports LRO (201/202) and provisioning can lag briefly. [2](https://blog.gbrueckl.at/2023/08/querying-power-bi-rest-api-using-fabric-spark-sql/)
    """
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
    """
    Create a schema-enabled lakehouse explicitly using Fabric REST API:
    creationPayload.enableSchemas=true [2](https://blog.gbrueckl.at/2023/08/querying-power-bi-rest-api-using-fabric-spark-sql/)
    """
    url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/lakehouses"
    headers = {
        "Authorization": f"Bearer {fabric_token()}",
        "Content-Type": "application/json"
    }
    payload = {
        "displayName": lakehouse_name,
        "description": description,
        "creationPayload": {"enableSchemas": True}  # <-- the key switch [2](https://blog.gbrueckl.at/2023/08/querying-power-bi-rest-api-using-fabric-spark-sql/)
    }

    r = requests.post(url, headers=headers, json=payload)

    # Create Lakehouse supports 201 (created) or 202 (accepted/LRO). [2](https://blog.gbrueckl.at/2023/08/querying-power-bi-rest-api-using-fabric-spark-sql/)
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
    """
    Create-or-reuse logic:
    - If lakehouse exists and is schema-enabled, proceed.
    - If not found, create schema-enabled.
    - If exists but NOT schema-enabled, fail fast with a clear message.
      (Enablement is done at creation time via creationPayload.enableSchemas). [2](https://blog.gbrueckl.at/2023/08/querying-power-bi-rest-api-using-fabric-spark-sql/)
    """
    try:
        props = nb.lakehouse.getWithProperties(name=lakehouse_name, workspaceId=workspace_id)

        # Signal: REST docs say defaultSchema is returned only for schema-enabled lakehouse. [2](https://blog.gbrueckl.at/2023/08/querying-power-bi-rest-api-using-fabric-spark-sql/)
        schema_enabled = "defaultSchema" in props.get("properties", {})
        log(f"Lakehouse exists. schemaEnabled={schema_enabled}")

        if not schema_enabled:
            raise RuntimeError(
                f"Lakehouse '{lakehouse_name}' exists but is NOT schema-enabled. "
                f"To allow manual 'New schema' in Lakehouse UI, recreate using "
                f"creationPayload.enableSchemas=true. [2](https://blog.gbrueckl.at/2023/08/querying-power-bi-rest-api-using-fabric-spark-sql/)[1](https://www.youtube.com/watch?v=PqPL9eT3kj8)"
            )

        return props

    except Exception as e:
        msg = str(e).lower()
        # Treat NOT FOUND as expected first-run case
        if "artifactnotfoundexception" in msg or "not found" in msg:
            log(f"Lakehouse '{lakehouse_name}' not found; creating schema-enabled via REST API...")
            if DEBUG:
                debug_exception("Details (expected on first run)", e)

            create_schema_enabled_lakehouse(workspace_id, lakehouse_name, description)
            # Wait until metadata is available for downstream ABFS path use
            return wait_for_lakehouse_props(lakehouse_name, workspace_id)

        # Unexpected error: surface
        debug_exception("Unexpected error while checking lakehouse", e)
        raise

# ---- Run it ----
WORKSPACE_ID = spark.conf.get("trident.workspace.id")
log(f"WorkspaceId: {WORKSPACE_ID}")
log(f"Lakehouse name: {LAKEHOUSE_NAME}")

lh_props = ensure_schema_enabled_lakehouse(WORKSPACE_ID, LAKEHOUSE_NAME, LAKEHOUSE_DESC)
log("✅ Lakehouse ready (schema-enabled).")


# 2) Resolve the ABFS path of *this* Lakehouse in *this* workspace
lh_props   = nb.lakehouse.getWithProperties(name=LAKEHOUSE_NAME, workspaceId=WORKSPACE_ID)
ABFS_ROOT  = lh_props["properties"]["abfsPath"]  # e.g., abfss://<ws>@onelake.dfs.fabric.microsoft.com/<lakehouse>
DEST_DIR   = f"{ABFS_ROOT}/Files/quickstart"
print("ABFS root:", ABFS_ROOT)
print("Destination (ABFS):", DEST_DIR)

# Ensure the top-level quickstart folder exists
nb.fs.mkdirs(DEST_DIR)  # ABFS-safe; no friendly-name resolution needed

# ---------------------------------------------
# 3) Copy branch-root files/folders into ABFS .../Files/quickstart
# ---------------------------------------------
print("\nListing branch tree (this may take a moment)...")
tree = list_branch_tree(GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH)

copied_text, copied_bin, skipped = 0, 0, 0
for item in tree:
    repo_path = item["path"]  # e.g., "docs/readme.md" or "users.tsv"

    # Skip excluded top-level directories
    top = repo_path.split("/", 1)[0]
    if top in EXCLUDE_DIRS:
        skipped += 1
        continue

    # Compute destination folder under ABFS (preserve repo subfolders)
    dest_dir = f"{DEST_DIR}/{os.path.dirname(repo_path)}" if "/" in repo_path else DEST_DIR
    try:
        nb.fs.mkdirs(dest_dir)
    except Exception as e:
        print(f"mkdirs({dest_dir}) -> {e}")

    # Decide copy method
    if is_text_file(repo_path):
        # Text: use nb.fs.put (writes UTF-8 text)
        try:
            text = _http_text(raw_url(GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH, repo_path))
            nb.fs.put(f"{dest_dir}/{os.path.basename(repo_path)}", text, overwrite=True)
            copied_text += 1
            print(f"Text copied: {repo_path}  ->  {dest_dir}/{os.path.basename(repo_path)}")
        except Exception as e:
            skipped += 1
            print(f"Skip text {repo_path}: {e}")
    else:
        # Binary: optionally copy via fs.cp (HTTP -> ABFS)
        if COPY_BINARIES:
            try:
                src = raw_url(GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH, repo_path)
                dst = f"{dest_dir}/{os.path.basename(repo_path)}"
                nb.fs.cp(src, dst, recurse=False)  # direct copy across filesystems
                copied_bin += 1
                print(f"Binary copied: {repo_path}  ->  {dst}")
            except Exception as e:
                skipped += 1
                print(f"Skip binary {repo_path}: {e}")
        else:
            skipped += 1

print(f"\n✅ Done. {copied_text} text file(s) and {copied_bin} binary file(s) imported into {DEST_DIR}. Skipped {skipped}.")
print("Explore them under Lakehouse → Files → quickstart in the left pane.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
