# ZENTREK V4.2.5 — Avalonia Desktop Migration

This directory is a **new native Windows application** using C# / .NET 8 and Avalonia 11. The previous Python/Tkinter application remains available under `source/`.

## Build

From a Windows machine with .NET 8 SDK:

```powershell
dotnet restore avalonia/Zentrek.csproj
dotnet publish avalonia/Zentrek.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true -p:IncludeNativeLibrariesForSelfExtract=true -o release
```

Or use the GitHub Actions **Build ZENTREK Avalonia V4.2.5** workflow. The Windows build artifact contains the EXE and an **empty** CSV template.

## Existing factory data

Place your approved `AVI_Database.csv` in `Database/` beside the published EXE. Optionally place `ZENTREK_Floorplan.json` there too. **Do not commit factory CSV, floor-plan files, notes or telemetry to this public repository.**

## Migration scope

Implemented: premium dark Avalonia desktop shell, Dashboard, read-only machine registry, read-only pinboard, CSV knowledge search, symptom search, 2026 shift calendar, and local data reload.

Not yet migrated: interactive floor-plan editing and coordinates, editor login/permissions, record editing and safe CSV saving, complete troubleshooting wizard flow engine, heartbeat overlay and machine monitoring. The calendar rotation was copied from the Python V4.2.4 logic and must be checked against the source shift cards.

The CSV reader in this initial version handles quoted commas but **not multi-line quoted CSV fields**. For such databases, continue using the Python version until the reader is upgraded. No live machine data is collected.

This is an initial migration build; validate compilation, runtime behavior and factory IT approval before deployment. The previous Python application is not removed or replaced.
