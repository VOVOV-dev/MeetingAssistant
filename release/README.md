# Release Package

This folder is the portable release layout for Windows.

## Structure

- `build.ps1` - one-click packaging script
- `run.bat` - double-click launcher for end users
- `run.ps1` - PowerShell launcher for end users
- `dist/` - generated packaged app output
- `.env` - local configuration copied from `.env.example`

## Build

Run inside the project root or directly from this folder:

```powershell
.\release\build.ps1
```

To generate a single exe:

```powershell
.\release\build.ps1 -OneFile
```

## Run

After packaging, place your real `.env` in `release/.env`, then either double-click `release/run.bat` or run:

```powershell
.\release\run.ps1
```

## Notes

- The packaged app still needs API keys in `release/.env`.
- The launcher copies that file into the packaged exe directory before starting.
- Keep `.env` outside git.
- The build output is self-contained and does not require Python on the target machine.
