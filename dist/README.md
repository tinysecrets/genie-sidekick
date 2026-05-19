# Genie Dist Kit

This folder gives the repo one clear startup path.

## Linux / Mac / Ubuntu

```bash
bash dist/genie-start.sh
```

## Check setup only

```bash
bash dist/genie-doctor.sh
```

## Windows PowerShell

```powershell
powershell -File dist/genie-start.ps1
```

## Purpose

The scripts check the repo, install needed frontend/backend packages when possible, start the backend, start the frontend, and print the local URL.

They are meant to avoid repeated path confusion and missing-command confusion.
