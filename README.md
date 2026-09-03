# BudgetFlow Backend

## Setup

1. Create a virtual environment:
   ```powershell
   python -m venv .venv
   ```
2. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`.
5. Configure Oracle values in `.env`: `ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_HOST`, `ORACLE_PORT`, and `ORACLE_SERVICE_NAME` or `ORACLE_NAME`.
6. Run checks:
   ```powershell
   python manage.py check
   ```
7. Run the development server:
   ```powershell
   python manage.py runserver
   ```
8. Test the health endpoint:
   ```powershell
   Invoke-WebRequest http://127.0.0.1:8000/api/health/
   ```
