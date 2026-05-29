# Backend

Run from the repository root.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m backend.seed_mock_data --reset
uvicorn backend.app.main:app --reload
```
