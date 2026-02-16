# Local Docker Development Guide

This guide details how to build, run, and manage the Music Cover Generator application locally using Docker. This setup mirrors the production environment while providing developer-friendly features like hot-reloading.

## 📋 Prerequisites

- **Docker Desktop**: Installed and running ([Download](https://www.docker.com/products/docker-desktop/)).
- **Make** (Optional but recommended):
    - **Windows**: Install via Chocolatey (`choco install make`) or use the provided commands directly.
    - **Mac/Linux**: Usually pre-installed or available via package managers.

---

## 🚀 Quick Start (Using Makefile)

If you have `make` installed, use these shortcuts:

### 1. Start the Environment
Builds the images (if needed) and starts the services in the background.
```bash
make up
```
*The app will be available at [http://localhost:3001](http://localhost:3001)*

### 2. View Logs
Follow the logs of all services to monitor activity.
```bash
make logs
```

### 3. Stop the Environment
Stops and removes the containers (preserves database data).
```bash
make down
```

### 4. Reset (Clean Slate)
**Warning**: This deletes the database volume and rebuilds everything.
```bash
make reset
```

---

## 🛠️ Manual Commands (Docker Compose)

If you cannot use `make`, run these standard Docker Compose commands from the project root:
| ## run migrations: docker compose exec app alembic upgrade head
| Action | Command |
| :--- | :--- |
| **Start** | `docker compose up -d` |
| **Build & Start** | `docker compose up --build -d` |
| **Stop** | `docker compose down` |
| **View Logs** | `docker compose logs -f` |
| **Open Shell** | `docker compose exec app /bin/bash` |

---

## ⚙️ Configuration

### Environment Variables
The setup uses a `.env` file. On the first run of `make up`, the system will automatically copy `.env.example` to `.env` if it doesn't exist.

To customize your local environment:
1.  Open `.env`.
2.  Modify variables as needed (e.g., `FLASK_DEBUG`, `KIE_API_KEY`).
3.  Restart the container: `make down` then `make up`.

### Database
- **Engine**: PostgreSQL 15
- **Internal Host**: `db`
- **Internal Port**: `5432`
- **Exposed Port**: `5432` (accessible from host machine via `localhost:5432`)
- **Default User/Pass**: `postgres` / `postgres`
- **Database Name**: `music_craft_db`

**Connecting externally**: You can connect to the database using a tool like DBeaver or pgAdmin using the credentials above.

---

## 🏗️ Architecture

### Services
1.  **`app`**: The Flask application.
    -   **Dockerfile**: Uses `Dockerfile.api` (target `development`).
    -   **Port**: Maps host `3000` to container `8000`.
    -   **Mounts**: The current directory `.` is mounted to `/app`, enabling **hot-reloading** of code changes without restarting the container.
    -   **Command**: Runs `flask run`.

2.  **`db`**: The PostgreSQL database.
    -   **Persistence**: Data is stored in the `postgres_data` Docker volume.

### Networking
-   Services communicate on the `app-network` bridge network.
-   The app connects to the database using the hostname `db` (as defined in `docker-compose.yml`).

---

## ❓ Troubleshooting

### 1. "Port is already allocated"
**Error**: `Bind for 0.0.0.0:3001 failed: port is already allocated`
**Solution**: Another service is using port 3001.
-   Stop the other service.
-   OR change the port mapping in `docker-compose.yml` (e.g., `"3002:8000"`).

### 2. New Python Dependencies
If you add a package to `requirements.txt`:
1.  Stop the app: `make down`
2.  Rebuild: `docker compose build` (or `make reset` if you want a full clean)
3.  Start: `make up`

### 3. Database Connection Errors
**Error**: `psycopg2.OperationalError: could not translate host name "db"`
**Solution**: Ensure the `db` service is healthy.
-   Check logs: `docker compose logs db`
-   Wait a few seconds for Postgres to initialize on the first run.
