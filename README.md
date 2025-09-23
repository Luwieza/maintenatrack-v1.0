# MaintenaTrack

MaintenaTrack is a Django web application for **logging and tracking equipment maintenance activities**.  
It supports user authentication, structured logging, and filtering to make maintenance operations traceable and efficient.

---

## 🚀 Features
- User authentication (signup, login, logout)
- Create, view, and update maintenance logs
- Filter logs by difficulty level
- Responsive templates using Django’s built-in admin and custom pages
- Dockerized for consistent deployment
- Sphinx documentation included under `docs/`

---

## 📦 Setup Instructions

### 1. Run Locally with Virtual Environment
Clone this repo and set up a virtual environment:

```bash
git clone https://github.com/hyperiondev-bootcamps/LG24030015633.git
cd "2 – Introduction to Software Engineering/L2T23 - Capstone Project - Django/maintenatrack"

python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver



