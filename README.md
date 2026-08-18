# Government Schemes Finder

A web application to help Indian citizens find and check eligibility for Central and Maharashtra State government schemes. 

---

## Features

- **45+ Schemes** across Central Government and Maharashtra State
- **Instant Eligibility Check** based on user profile
- **User Dashboard** with eligibility history
- **Admin Panel** to manage users, schemes, and view activity
- **Responsive Design** — works on mobile, tablet, and desktop

---

## Tech Stack

| Layer     | Technology        |
|-----------|-------------------|
| Frontend  | HTML, CSS, JavaScript |
| Backend   | Python (Flask)    |
| Database  | SQLite            |

---

## Project Structure

```
govt_schemes/
├── app.py                  # Main Flask application & routes
├── database.py             # DB init, schema, seed data
├── requirements.txt
├── schemes.db              # Auto-created on first run
├── static/
│   ├── css/style.css
│   └── js/main.js
└── templates/
    ├── base.html
    ├── home.html
    ├── login.html
    ├── signup.html
    ├── dashboard.html
    ├── schemes.html
    ├── scheme_detail.html
    ├── check_eligibility.html
    ├── eligibility_result.html
    └── admin/
        ├── dashboard.html
        ├── users.html
        ├── edit_user.html
        ├── schemes.html
        ├── scheme_form.html
        └── history.html
```

---

## Setup & Run

### 1. Install Python (3.8+)
Download from https://python.org

### 2. Install dependencies
```bash
cd govt_schemes
pip install -r requirements.txt
```

### 3. Run the application
```bash
python app.py
```

### 4. Open in browser
```
http://127.0.0.1:5000
```

The database (`schemes.db`) is created automatically on first run with all 45+ schemes pre-loaded.

---

## Default Admin Credentials

| Field    | Value      |
|----------|------------|
| Username | `admin`    |
| Password | `admin123` |

> Change the admin password after first login via Admin > Manage Users > Edit.

---

## User Roles

### User
- Register and login
- Browse schemes by category (Central / Maharashtra)
- Check eligibility instantly
- View eligibility history on dashboard

### Admin
- View dashboard stats (total users, schemes, checks)
- Manage users (edit, delete, promote to admin)
- Manage schemes (add, edit, delete)
- Update eligibility criteria per scheme
- View all user eligibility history and activity logs

---

## Scheme Categories

### Central Government
1. Healthcare & Insurance (3 schemes)
2. Agriculture & Rural Livelihood (4 schemes)
3. Housing & Infrastructure (2 schemes)
4. Financial Inclusion & Entrepreneurship (4 schemes)
5. Savings & Pensions (3 schemes)

### Maharashtra State Government
1. Women & Family Welfare (6 schemes)
2. Agriculture & Farmers (6 schemes)
3. Youth & Employment (4 schemes)
4. Education & Scholarships (4 schemes)
5. Senior Citizens & Social Assistance (4 schemes)
6. Housing & Infrastructure (4 schemes)

---

## Eligibility Engine

The system compares user profile data against scheme criteria using operators:

| Operator | Meaning              |
|----------|----------------------|
| `eq`     | Equal to             |
| `lte`    | Less than or equal   |
| `gte`    | Greater than or equal|
| `lt`     | Less than            |
| `gt`     | Greater than         |
| `in`     | One of (comma list)  |

If profile data is missing for a scheme's criteria, the system dynamically asks for the additional input before checking.

---

## Disclaimer

This is an informational platform. Actual eligibility may vary. Always verify with official government sources:  
https://www.india.gov.in/my-government/schemes
