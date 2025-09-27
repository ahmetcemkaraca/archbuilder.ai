# ArchBuilder Cloud Server — Setup Notes

Create a `.env` file based on the following keys:

```
JWT_SECRET=change_me
DATABASE_URL=postgresql+asyncpg://your_user:your_password@localhost:5432/archbuilder
RAGFLOW_BASE_URL=http://localhost
RAGFLOW_API_KEY=
RAGFLOW_API_VERSION=v1
RAGFLOW_TIMEOUT_SECONDS=30
LOG_LEVEL=INFO
```

Notes:
- Default DB is SQLite; set `DATABASE_URL` for production.
- Never commit real secrets. Use secret stores for CI/CD.
- Replace `your_user` and `your_password` with actual credentials.  
