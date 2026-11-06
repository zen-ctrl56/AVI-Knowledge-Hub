# AVI Knowledge Hub V1.2

Offline-capable single-file dashboard for personal AVI troubleshooting knowledge.

## Production installation
1. Download this repository as a ZIP from GitHub (Code > Download ZIP).
2. Extract to your approved personal directory on the production network.
3. Open index.html in Chrome.
4. Choose Connect CSV and select database/AVI_Database.csv.
5. Add/edit entries and click Save Database. Confirm the success status.
6. If Chrome blocks direct writes from a network file URL, Save Database downloads a replacement CSV. Copy it to the database folder manually.

## Important
- Chrome file:// network access does not guarantee File System Access API availability. Direct saving may require HTTPS or localhost and browser permissions.
- Never assume data saved until success is shown or the replacement CSV has been copied.
- Only one editor should write at a time. CSV has no transaction locking.
- No factory data, machine credentials, internal paths, or real logs belong in this GitHub repository.
- GitHub is for the app, not the production database.
