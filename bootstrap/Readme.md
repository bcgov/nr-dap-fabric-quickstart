# Fabric Bootstrap

Use this one-time bootstrap to pull the notebook into a **new, empty** Microsoft Fabric workspace, import files into your Lakehouse, and start exploring.

## Quickstart (≈ 5 minutes)

1. **Create** a new empty Fabric workspace.
2. **Connect** the workspace to GitHub  
   - **Workspace settings → Git integration**  
   - Provider: **GitHub**  
   - Repo: `bcgov/nr-dap-fabric-quickstart`  
   - Branch: `main`  
   - Folder: `bootstrap`
3. **Initial sync**: choose **Git → Workspace** (the workspace is empty).
4. **Run the notebook** `01_import_files_root` → **Run all**  
   - Creates/attaches Lakehouse **`quickstart_lh`**  
   - Copies branch‑root **text files** into **Lakehouse → Files → `quickstart`**
5. **Disconnect Git**: **Workspace settings → Git integration → Disconnect**  
   - Prevents commits back to the repo; your items remain in the workspace.

## Notes
- Lakehouse **Tables** and **Files** aren’t tracked by Git; the notebook places assets locally for you.
- If outbound access is restricted, allow `api.github.com` and `raw.githubusercontent.com` for the one‑time import.

## Where to look
- Open **Lakehouse → Files → `quickstart`** to browse imported files.
