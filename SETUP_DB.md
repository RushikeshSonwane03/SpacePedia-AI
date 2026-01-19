# PostgreSQL Setup Guide for Windows

Since you don't have Docker installed, you'll need to install PostgreSQL directly.

## 1. Download and Install
1.  Visit the [EnterpriseDB Download Page](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
2.  Download the **Windows x86-64** installer for **version 16** (or 15).
3.  Run the installer.
    *   **Password**: When asked for a password for the `postgres` superuser, enter **`password`** (or change it, but update `.env`!).
    *   **Port**: Keep default **5432**.
    *   **Stack Builder**: You can uncheck/skip this at the end.

## 2. Verify Installation
Open a terminal (PowerShell or CMD) and type:
```powershell
psql -U postgres
```
(You might need to add `C:\Program Files\PostgreSQL\16\bin` to your System PATH if command not found).

If prompted for password, enter the one you set.

## 3. Create Database
Inside the `psql` shell (or using the installer's created DB which usually is just `postgres`):

```sql
CREATE DATABASE spacepedia;
```

## 4. Update Configuration
Ensure your `.env` file matches your setup:

```ini
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password  # <--- Update this if you chose differently
POSTGRES_DB=spacepedia
POSTGRES_PORT=5432
```
