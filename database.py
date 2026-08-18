import sqlite3
from flask import g
import os

DATABASE = 'schemes.db'

def get_db():
    if 'db' not in g._get_current_object().__dict__:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    if os.path.exists(DATABASE):
        return
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT,
        age INTEGER,
        income REAL,
        caste TEXT,
        gender TEXT,
        state TEXT,
        occupation TEXT,
        mobile TEXT,
        email TEXT,
        role TEXT DEFAULT 'user'
    );

    CREATE TABLE IF NOT EXISTS schemes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        benefits TEXT,
        documents TEXT,
        category TEXT,
        state TEXT
    );

    CREATE TABLE IF NOT EXISTS eligibility_criteria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scheme_id INTEGER,
        field TEXT,
        label TEXT,
        operator TEXT,
        value TEXT,
        FOREIGN KEY (scheme_id) REFERENCES schemes(id)
    );

    CREATE TABLE IF NOT EXISTS eligibility_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        scheme_id INTEGER,
        result TEXT,
        reason TEXT,
        checked_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (scheme_id) REFERENCES schemes(id)
    );

    CREATE TABLE IF NOT EXISTS user_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        timestamp TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    ''')

    import hashlib
    admin_pass = hashlib.sha256('admin123'.encode()).hexdigest()
    c.execute('''INSERT OR IGNORE INTO users (username, password, full_name, age, income, caste, gender, state, occupation, mobile, email, role)
                 VALUES ('admin', ?, 'Administrator', 30, 0, 'General', 'Male', 'Maharashtra', 'Government', '9999999999', 'admin@gov.in', 'admin')''',
              (admin_pass,))

    seed_schemes(c)
    conn.commit()
    conn.close()

def seed_schemes(c):
    schemes = [
        # Central - Healthcare
        ("Ayushman Bharat (PM-JAY)", "Health insurance scheme providing coverage up to ₹5 lakh per family per year for secondary and tertiary care hospitalization.", "Health cover up to ₹5 lakh/year for hospitalization. Cashless treatment at empanelled hospitals.", "Aadhaar Card, Ration Card, Income Certificate", "Healthcare & Insurance", "Central"),
        ("Pradhan Mantri Suraksha Bima Yojana (PMSBY)", "Accidental death and disability insurance scheme with annual premium of ₹20.", "₹2 lakh for accidental death/permanent disability, ₹1 lakh for partial disability.", "Aadhaar Card, Bank Account", "Healthcare & Insurance", "Central"),
        ("Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)", "Life insurance scheme with annual premium of ₹436.", "₹2 lakh life insurance cover.", "Aadhaar Card, Bank Account", "Healthcare & Insurance", "Central"),
        # Central - Agriculture
        ("PM Kisan Samman Nidhi (PM-KISAN)", "Income support of ₹6000/year to farmer families.", "₹6000 per year in 3 equal installments directly to bank account.", "Aadhaar Card, Land Records, Bank Account", "Agriculture & Rural Livelihood", "Central"),
        ("Jal Jeevan Mission (Har Ghar Jal)", "Provides tap water connection to every rural household.", "Functional household tap connection with safe drinking water.", "Aadhaar Card, Residence Proof", "Agriculture & Rural Livelihood", "Central"),
        ("Pradhan Mantri Fasal Bima Yojana (PMFBY)", "Crop insurance scheme for farmers.", "Insurance coverage for crop loss due to natural calamities.", "Aadhaar Card, Land Records, Bank Account", "Agriculture & Rural Livelihood", "Central"),
        ("Lakhpati Didi Scheme", "Empowers women SHG members to earn ₹1 lakh+ annually.", "Skill training, livelihood support, and financial assistance.", "Aadhaar Card, SHG Membership Proof", "Agriculture & Rural Livelihood", "Central"),
        # Central - Housing
        ("Pradhan Mantri Awas Yojana (PMAY)", "Affordable housing scheme for urban and rural poor.", "Subsidy on home loans and financial assistance for house construction.", "Aadhaar Card, Income Certificate, Land Documents", "Housing & Infrastructure", "Central"),
        ("PM Surya Ghar", "Free electricity up to 300 units/month through rooftop solar.", "Free solar panel installation and electricity subsidy.", "Aadhaar Card, Electricity Bill, Bank Account", "Housing & Infrastructure", "Central"),
        # Central - Financial
        ("Pradhan Mantri Jan Dhan Yojana (PMJDY)", "Financial inclusion scheme for unbanked population.", "Zero balance bank account, RuPay debit card, ₹2 lakh accident insurance.", "Aadhaar Card, Address Proof", "Financial Inclusion & Entrepreneurship", "Central"),
        ("Pradhan Mantri Mudra Yojana (PMMY)", "Loans up to ₹10 lakh for non-corporate small businesses.", "Collateral-free loans: Shishu (₹50K), Kishore (₹5L), Tarun (₹10L).", "Aadhaar Card, Business Plan, Bank Statement", "Financial Inclusion & Entrepreneurship", "Central"),
        ("PM SVANidhi", "Micro-credit for street vendors.", "Working capital loan of ₹10,000 to ₹50,000.", "Aadhaar Card, Vending Certificate", "Financial Inclusion & Entrepreneurship", "Central"),
        ("PM Vishwakarma", "Support for traditional artisans and craftspeople.", "Skill training, toolkit support, credit up to ₹3 lakh.", "Aadhaar Card, Caste Certificate (if applicable)", "Financial Inclusion & Entrepreneurship", "Central"),
        # Central - Savings
        ("Sukanya Samriddhi Yojana (SSY)", "Savings scheme for girl child education and marriage.", "High interest rate savings account for girl child below 10 years.", "Birth Certificate of Girl Child, Aadhaar, Bank Account", "Savings & Pensions", "Central"),
        ("Atal Pension Yojana (APY)", "Pension scheme for unorganized sector workers.", "Guaranteed pension of ₹1000-₹5000/month after age 60.", "Aadhaar Card, Bank Account, Mobile Number", "Savings & Pensions", "Central"),
        ("Mahila Samman Savings Certificate", "Savings scheme for women with 7.5% interest.", "Fixed deposit at 7.5% interest for 2 years up to ₹2 lakh.", "Aadhaar Card, PAN Card, Bank Account", "Savings & Pensions", "Central"),
        # Maharashtra - Women
        ("Mukhyamantri – Majhi Ladki Bahin Yojana", "Financial assistance of ₹1500/month to women.", "Monthly financial assistance of ₹1500 to eligible women.", "Aadhaar Card, Income Certificate, Bank Account", "Women & Family Welfare", "Maharashtra"),
        ("Lek Ladki Yojana", "Financial support for girl child from birth to education.", "Financial assistance at various stages from birth to graduation.", "Birth Certificate, Aadhaar, Income Certificate", "Women & Family Welfare", "Maharashtra"),
        ("Mukhya Mantri Annapurna Yojana", "Free food grains to poor families.", "3 free LPG cylinders per year and food grain support.", "Ration Card, Aadhaar Card", "Women & Family Welfare", "Maharashtra"),
        ("Majhi Kanya Bhagyashree Yojana", "Financial support for girl child education.", "₹50,000 fixed deposit for girl child education.", "Birth Certificate, Aadhaar, Income Certificate", "Women & Family Welfare", "Maharashtra"),
        ("Mahila Samridhi Yojana", "Micro-finance for women entrepreneurs.", "Low interest loans for women self-help groups.", "Aadhaar Card, SHG Certificate, Bank Account", "Women & Family Welfare", "Maharashtra"),
        ("Indira Gandhi National Widow Pension Scheme", "Pension for widows below poverty line.", "₹300/month pension for widows aged 40-79.", "Aadhaar Card, Death Certificate of Husband, BPL Card", "Women & Family Welfare", "Maharashtra"),
        # Maharashtra - Agriculture
        ("Namo Shetkari Mahasanman Nidhi (NSMN)", "Additional ₹6000/year to farmers supplementing PM-KISAN.", "₹6000/year in addition to PM-KISAN benefit.", "Aadhaar Card, Land Records, Bank Account", "Agriculture & Farmers", "Maharashtra"),
        ("Mukhya Mantri Baliraja Vij Savlat Yojana", "Subsidized electricity for farmers.", "Subsidized electricity for agricultural pump sets.", "Aadhaar Card, Land Records, Electricity Connection", "Agriculture & Farmers", "Maharashtra"),
        ("Krishi Samruddhi Yojana", "Comprehensive agricultural development scheme.", "Financial assistance for farm inputs and equipment.", "Aadhaar Card, Land Records, Bank Account", "Agriculture & Farmers", "Maharashtra"),
        ("Peek Veema Yojana (Crop Insurance)", "State crop insurance for Maharashtra farmers.", "Crop loss compensation due to natural calamities.", "Aadhaar Card, Land Records, Bank Account", "Agriculture & Farmers", "Maharashtra"),
        ("Maa Gele Tyala Solar Pump Yojana", "Solar pump for farmers.", "Free/subsidized solar water pump for irrigation.", "Aadhaar Card, Land Records, Electricity Bill", "Agriculture & Farmers", "Maharashtra"),
        ("Mukhyamantri Solar Krishi Vahini Yojana", "Solar energy for agricultural feeders.", "Daytime electricity supply to farmers via solar.", "Aadhaar Card, Land Records", "Agriculture & Farmers", "Maharashtra"),
        # Maharashtra - Youth
        ("Mukhyamantri Yuva Karya Prashikshan Yojana", "Skill training stipend for unemployed youth.", "₹10,000/month stipend during apprenticeship training.", "Aadhaar Card, Educational Certificate, Bank Account", "Youth & Employment", "Maharashtra"),
        ("Chief Minister's Employment Generation Program (CMEGP)", "Self-employment loans for youth.", "Loans up to ₹50 lakh for manufacturing, ₹10 lakh for services.", "Aadhaar Card, Project Report, Bank Account", "Youth & Employment", "Maharashtra"),
        ("Seed Money Scheme (SMS)", "Seed capital for entrepreneurs.", "15% seed money assistance for new enterprises.", "Aadhaar Card, Business Plan, Bank Account", "Youth & Employment", "Maharashtra"),
        ("Maharashtra Apprenticeship Promotion Scheme (MAPS)", "Apprenticeship for youth in industries.", "Stipend support and skill development.", "Aadhaar Card, Educational Certificate", "Youth & Employment", "Maharashtra"),
        # Maharashtra - Education
        ("Rajarshri Chhatrapati Shahu Maharaj Merit Scholarship", "Merit scholarship for OBC students.", "Scholarship for meritorious OBC students in higher education.", "Aadhaar Card, Caste Certificate, Mark Sheet", "Education & Scholarships", "Maharashtra"),
        ("Post-Matric Scholarship for VJNT Students", "Scholarship for VJNT students after 10th.", "Full tuition fee and maintenance allowance.", "Aadhaar Card, Caste Certificate, Mark Sheet", "Education & Scholarships", "Maharashtra"),
        ("Scholarships for Higher Education Abroad", "Scholarship for studying abroad.", "Financial support for higher education in foreign universities.", "Aadhaar Card, Admission Letter, Income Certificate", "Education & Scholarships", "Maharashtra"),
        ("Swadhar Yojana", "Accommodation and food for SC students.", "Free hostel and food for SC students in cities.", "Aadhaar Card, Caste Certificate, Income Certificate", "Education & Scholarships", "Maharashtra"),
        # Maharashtra - Senior Citizens
        ("Shravanbal Seva State Pension Scheme", "Pension for senior citizens.", "₹600/month pension for senior citizens above 65.", "Aadhaar Card, Age Proof, Income Certificate", "Senior Citizens & Social Assistance", "Maharashtra"),
        ("Mukhyamantri Vayoshri Yojana", "Assistive devices for senior citizens.", "Free assistive devices like spectacles, hearing aids.", "Aadhaar Card, Age Proof, BPL Card", "Senior Citizens & Social Assistance", "Maharashtra"),
        ("Sanjay Gandhi Niradhar Anudan Yojana", "Financial assistance for destitute persons.", "₹600/month for destitute, disabled, orphans.", "Aadhaar Card, Income Certificate, Disability Certificate", "Senior Citizens & Social Assistance", "Maharashtra"),
        ("Indira Gandhi National Old Age Pension Scheme", "Central pension for BPL elderly.", "₹200-₹500/month pension for BPL elderly.", "Aadhaar Card, Age Proof, BPL Card", "Senior Citizens & Social Assistance", "Maharashtra"),
        # Maharashtra - Housing
        ("Ramai Awas Yojana", "Housing for SC/NT/OBC communities.", "Financial assistance for house construction.", "Aadhaar Card, Caste Certificate, Land Documents", "Housing & Infrastructure", "Maharashtra"),
        ("Pradhan Mantri Awas Yojana - Urban 2.0", "Urban housing for EWS/LIG.", "Subsidy on home loans for urban poor.", "Aadhaar Card, Income Certificate, Land Documents", "Housing & Infrastructure", "Maharashtra"),
        ("Mukhya Mantri Gram Sadak Yojana (MMGSY)", "Rural road connectivity.", "All-weather road connectivity to rural habitations.", "Village Panchayat Resolution", "Housing & Infrastructure", "Maharashtra"),
        ("Shabri Awas Yojana", "Housing for tribal communities.", "Financial assistance for tribal house construction.", "Aadhaar Card, Tribal Certificate, Land Documents", "Housing & Infrastructure", "Maharashtra"),
    ]

    criteria_map = {
        "Ayushman Bharat (PM-JAY)": [("income", "Annual Income", "lte", "500000"), ("age", "Age", "gte", "0")],
        "Pradhan Mantri Suraksha Bima Yojana (PMSBY)": [("age", "Age", "gte", "18"), ("age", "Age", "lte", "70")],
        "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)": [("age", "Age", "gte", "18"), ("age", "Age", "lte", "50")],
        "PM Kisan Samman Nidhi (PM-KISAN)": [("occupation", "Occupation", "eq", "Farmer")],
        "Jal Jeevan Mission (Har Ghar Jal)": [("state", "State", "in", "All States")],
        "Pradhan Mantri Fasal Bima Yojana (PMFBY)": [("occupation", "Occupation", "eq", "Farmer")],
        "Lakhpati Didi Scheme": [("gender", "Gender", "eq", "Female")],
        "Pradhan Mantri Awas Yojana (PMAY)": [("income", "Annual Income", "lte", "1800000")],
        "PM Surya Ghar": [("income", "Annual Income", "lte", "1500000")],
        "Pradhan Mantri Jan Dhan Yojana (PMJDY)": [("age", "Age", "gte", "10")],
        "Pradhan Mantri Mudra Yojana (PMMY)": [("age", "Age", "gte", "18")],
        "PM SVANidhi": [("occupation", "Occupation", "eq", "Street Vendor")],
        "PM Vishwakarma": [("occupation", "Occupation", "in", "Carpenter,Blacksmith,Potter,Weaver,Goldsmith,Barber,Washerman,Tailor,Mason,Cobbler")],
        "Sukanya Samriddhi Yojana (SSY)": [("gender", "Gender", "eq", "Female"), ("age", "Age", "lte", "10")],
        "Atal Pension Yojana (APY)": [("age", "Age", "gte", "18"), ("age", "Age", "lte", "40")],
        "Mahila Samman Savings Certificate": [("gender", "Gender", "eq", "Female")],
        "Mukhyamantri – Majhi Ladki Bahin Yojana": [("gender", "Gender", "eq", "Female"), ("age", "Age", "gte", "21"), ("age", "Age", "lte", "65"), ("income", "Annual Income", "lte", "250000"), ("state", "State", "eq", "Maharashtra")],
        "Lek Ladki Yojana": [("gender", "Gender", "eq", "Female"), ("income", "Annual Income", "lte", "100000"), ("state", "State", "eq", "Maharashtra")],
        "Mukhya Mantri Annapurna Yojana": [("income", "Annual Income", "lte", "100000"), ("state", "State", "eq", "Maharashtra")],
        "Majhi Kanya Bhagyashree Yojana": [("gender", "Gender", "eq", "Female"), ("income", "Annual Income", "lte", "750000"), ("state", "State", "eq", "Maharashtra")],
        "Mahila Samridhi Yojana": [("gender", "Gender", "eq", "Female"), ("state", "State", "eq", "Maharashtra")],
        "Indira Gandhi National Widow Pension Scheme": [("gender", "Gender", "eq", "Female"), ("age", "Age", "gte", "40"), ("age", "Age", "lte", "79"), ("income", "Annual Income", "lte", "100000"), ("state", "State", "eq", "Maharashtra")],
        "Namo Shetkari Mahasanman Nidhi (NSMN)": [("occupation", "Occupation", "eq", "Farmer"), ("state", "State", "eq", "Maharashtra")],
        "Mukhya Mantri Baliraja Vij Savlat Yojana": [("occupation", "Occupation", "eq", "Farmer"), ("state", "State", "eq", "Maharashtra")],
        "Krishi Samruddhi Yojana": [("occupation", "Occupation", "eq", "Farmer"), ("state", "State", "eq", "Maharashtra")],
        "Peek Veema Yojana (Crop Insurance)": [("occupation", "Occupation", "eq", "Farmer"), ("state", "State", "eq", "Maharashtra")],
        "Maa Gele Tyala Solar Pump Yojana": [("occupation", "Occupation", "eq", "Farmer"), ("state", "State", "eq", "Maharashtra")],
        "Mukhyamantri Solar Krishi Vahini Yojana": [("occupation", "Occupation", "eq", "Farmer"), ("state", "State", "eq", "Maharashtra")],
        "Mukhyamantri Yuva Karya Prashikshan Yojana": [("age", "Age", "gte", "18"), ("age", "Age", "lte", "35"), ("state", "State", "eq", "Maharashtra")],
        "Chief Minister's Employment Generation Program (CMEGP)": [("age", "Age", "gte", "18"), ("state", "State", "eq", "Maharashtra")],
        "Seed Money Scheme (SMS)": [("age", "Age", "gte", "18"), ("state", "State", "eq", "Maharashtra")],
        "Maharashtra Apprenticeship Promotion Scheme (MAPS)": [("age", "Age", "gte", "14"), ("age", "Age", "lte", "25"), ("state", "State", "eq", "Maharashtra")],
        "Rajarshri Chhatrapati Shahu Maharaj Merit Scholarship": [("caste", "Caste", "eq", "OBC"), ("state", "State", "eq", "Maharashtra")],
        "Post-Matric Scholarship for VJNT Students": [("caste", "Caste", "in", "VJNT,NT"), ("state", "State", "eq", "Maharashtra")],
        "Scholarships for Higher Education Abroad": [("income", "Annual Income", "lte", "600000"), ("state", "State", "eq", "Maharashtra")],
        "Swadhar Yojana": [("caste", "Caste", "eq", "SC"), ("state", "State", "eq", "Maharashtra")],
        "Shravanbal Seva State Pension Scheme": [("age", "Age", "gte", "65"), ("income", "Annual Income", "lte", "21000"), ("state", "State", "eq", "Maharashtra")],
        "Mukhyamantri Vayoshri Yojana": [("age", "Age", "gte", "65"), ("state", "State", "eq", "Maharashtra")],
        "Sanjay Gandhi Niradhar Anudan Yojana": [("income", "Annual Income", "lte", "21000"), ("state", "State", "eq", "Maharashtra")],
        "Indira Gandhi National Old Age Pension Scheme": [("age", "Age", "gte", "60"), ("income", "Annual Income", "lte", "100000"), ("state", "State", "eq", "Maharashtra")],
        "Ramai Awas Yojana": [("caste", "Caste", "in", "SC,NT,OBC"), ("state", "State", "eq", "Maharashtra")],
        "Pradhan Mantri Awas Yojana - Urban 2.0": [("income", "Annual Income", "lte", "900000"), ("state", "State", "eq", "Maharashtra")],
        "Mukhya Mantri Gram Sadak Yojana (MMGSY)": [("state", "State", "eq", "Maharashtra")],
        "Shabri Awas Yojana": [("caste", "Caste", "eq", "ST"), ("state", "State", "eq", "Maharashtra")],
    }

    for s in schemes:
        c.execute('INSERT INTO schemes (name, description, benefits, documents, category, state) VALUES (?,?,?,?,?,?)', s)
        scheme_id = c.lastrowid
        name = s[0]
        if name in criteria_map:
            for field, label, operator, value in criteria_map[name]:
                c.execute('INSERT INTO eligibility_criteria (scheme_id, field, label, operator, value) VALUES (?,?,?,?,?)',
                          (scheme_id, field, label, operator, value))
