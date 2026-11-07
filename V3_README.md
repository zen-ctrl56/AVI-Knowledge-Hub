# AVI Knowledge Hub V3 — AEGIS
Windows desktop troubleshooting knowledge base. Dark amber dashboard, 26-machine registry, guided troubleshooting wizard, and searchable CSV knowledge editor. No live monitoring.
## Build on GitHub
Go to **Actions → Build AVI Knowledge Hub Windows EXE → Run workflow**. Download the build artifact after success (GitHub login may be required). A version tag `v3.0.0` triggers a Release ZIP accessible publicly if the repository is public.
## Production deployment
Use an IT-approved Windows PC and approved network folder. Extract the compiled EXE. Place your existing populated database at `Database/AVI_Database.csv` beside the EXE. Double-click the EXE. **Do not overwrite the existing populated database** with the empty template.
No Python, CMD, or PowerShell needed on production PCs. The EXE must be allowed by your organization's execution policy. The database is auto-discovered relative to the executable, including UNC network paths.
## Data and concurrency
CSV columns: `id,title,category,machine,symptoms,solution`. Save makes a timestamped backup and a short-lived lock file, but concurrent editors can still overwrite each other's changes; designate a single editor. The application is not connected to AVI machines.
## Security
Keep all production records, customer information, logs, credentials, and network paths off public GitHub. GitHub-hosted build runners and public EXE distribution require organizational approval.
