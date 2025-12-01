Unit Tests and Setup Instructions
Setup Instructions
Install Dependencies
pip install django djangorestframework pytest pytest django

Backend Setup
cd backend
python manage.py migrate
python manage.py runserver


Backend runs at:

http://127.0.0.1:8000/

Frontend Setup
(IMPORTANT: CHANGE THE script.js link at the top of the file to --> const API_BASE = "http://127.0.0.1:8000/api/tasks"; when running locally)
cd frontend
python -m http.server 5500


Frontend runs at:

http://127.0.0.1:5500/
