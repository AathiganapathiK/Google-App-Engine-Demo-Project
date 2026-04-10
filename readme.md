# Flask + MySQL — GAE Starter

A clean Flask signup/login app backed by MySQL, ready to deploy on **Google App Engine (Standard)**.

---

## Project Structure

```
flask-gae-app/
├── app.py              # Flask application
├── app.yaml            # GAE configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Local env template
├── .gcloudignore
└── templates/
    ├── base.html
    ├── login.html
    ├── signup.html
    └── dashboard.html
```

---

## Local Development

### 1. Prerequisites
- Python 3.11+
- MySQL server running locally
- `pip` + `virtualenv`

### 2. Setup

```bash
# Clone / unzip project, then:
cd flask-gae-app

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your local MySQL credentials
```

### 3. Create the database

```sql
CREATE DATABASE flaskapp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
The `users` table is auto-created on first run via `init_db()`.

### 4. Run

```bash
# Load .env automatically (requires python-dotenv, or export vars manually)
export $(grep -v '^#' .env | xargs)
python app.py
```

Visit → http://localhost:8080

---

## Deploy to Google App Engine

### Option A — Cloud SQL (recommended)

1. **Create a Cloud SQL (MySQL 8) instance** in your GCP project.
2. **Create a database and user**:
   ```sql
   CREATE DATABASE flaskapp;
   CREATE USER 'flaskapp_user'@'%' IDENTIFIED BY 'strong_password';
   GRANT ALL ON flaskapp.* TO 'flaskapp_user'@'%';
   ```
3. **Edit `app.yaml`** — uncomment the Cloud SQL block and fill in:
   - `DB_HOST`: `/cloudsql/PROJECT:REGION:INSTANCE`
   - `DB_USER`, `DB_PASS`, `DB_NAME`
   - `beta_settings.cloud_sql_instances`
4. **Deploy**:
   ```bash
   gcloud app deploy
   ```

### Option B — External MySQL

Fill in the `DB_HOST`, `DB_USER`, `DB_PASS`, `DB_NAME` env vars in `app.yaml` directly and deploy.

> ⚠️ For production, store secrets in **Google Secret Manager** and reference them via the Secret Manager API instead of hardcoding in `app.yaml`.

---

## Environment Variables

| Variable     | Description                        | Default       |
|--------------|------------------------------------|---------------|
| `SECRET_KEY` | Flask session signing key          | (must set)    |
| `DB_HOST`    | MySQL host / Cloud SQL socket path | `127.0.0.1`   |
| `DB_USER`    | MySQL username                     | `root`        |
| `DB_PASS`    | MySQL password                     | *(empty)*     |
| `DB_NAME`    | Database name                      | `flaskapp`    |

---

## Security Notes

- Passwords are hashed with **Werkzeug's PBKDF2-SHA256**.
- Sessions are signed with `SECRET_KEY` — use a long random string in production.
- HTTPS is enforced in GAE via `secure: always` in `app.yaml`.
- Never commit `.env` or real credentials to version control.