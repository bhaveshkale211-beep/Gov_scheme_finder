from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from database import init_db, get_db
import hashlib
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user(username):
    db = get_db()
    return db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

def is_admin():
    return session.get('role') == 'admin'

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or not is_admin():
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def home():
    db = get_db()
    categories = db.execute('SELECT DISTINCT category, state FROM schemes ORDER BY state, category').fetchall()
    return render_template('home.html', categories=categories)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        db = get_db()
        existing = db.execute('SELECT id FROM users WHERE username = ?', (data['username'],)).fetchone()
        if existing:
            flash('Username already exists.', 'danger')
            return render_template('signup.html')
        db.execute('''INSERT INTO users (username, password, full_name, age, income, caste, gender, state, occupation, mobile, email, role)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'user')''',
                   (data['username'], hash_password(data['password']), data['full_name'],
                    int(data['age']), float(data['income']), data['caste'], data['gender'],
                    data['state'], data['occupation'], data['mobile'], data['email']))
        db.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            db.execute('INSERT INTO user_activity (user_id, action, timestamp) VALUES (?, ?, ?)',
                       (user['id'], 'login', datetime.now().isoformat()))
            db.commit()
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user_id' in session:
        db = get_db()
        db.execute('INSERT INTO user_activity (user_id, action, timestamp) VALUES (?, ?, ?)',
                   (session['user_id'], 'logout', datetime.now().isoformat()))
        db.commit()
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    history = db.execute('''SELECT h.*, s.name as scheme_name, s.category, s.state 
                            FROM eligibility_history h JOIN schemes s ON h.scheme_id = s.id
                            WHERE h.user_id = ? ORDER BY h.checked_at DESC LIMIT 10''',
                         (session['user_id'],)).fetchall()
    categories = db.execute('SELECT DISTINCT category, state FROM schemes ORDER BY state, category').fetchall()
    return render_template('dashboard.html', user=user, history=history, categories=categories)

@app.route('/schemes')
@login_required
def schemes():
    db = get_db()
    state_filter = request.args.get('state', '')
    category_filter = request.args.get('category', '')
    query = 'SELECT * FROM schemes WHERE 1=1'
    params = []
    if state_filter:
        query += ' AND state = ?'
        params.append(state_filter)
    if category_filter:
        query += ' AND category = ?'
        params.append(category_filter)
    schemes_list = db.execute(query, params).fetchall()
    categories = db.execute('SELECT DISTINCT category, state FROM schemes ORDER BY state, category').fetchall()
    return render_template('schemes.html', schemes=schemes_list, categories=categories,
                           state_filter=state_filter, category_filter=category_filter)

@app.route('/scheme/<int:scheme_id>')
@login_required
def scheme_detail(scheme_id):
    db = get_db()
    scheme = db.execute('SELECT * FROM schemes WHERE id = ?', (scheme_id,)).fetchone()
    if not scheme:
        flash('Scheme not found.', 'danger')
        return redirect(url_for('schemes'))
    criteria = db.execute('SELECT * FROM eligibility_criteria WHERE scheme_id = ?', (scheme_id,)).fetchall()
    return render_template('scheme_detail.html', scheme=scheme, criteria=criteria)

@app.route('/check_eligibility/<int:scheme_id>', methods=['GET', 'POST'])
@login_required
def check_eligibility(scheme_id):
    db = get_db()
    scheme = db.execute('SELECT * FROM schemes WHERE id = ?', (scheme_id,)).fetchone()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    criteria = db.execute('SELECT * FROM eligibility_criteria WHERE scheme_id = ?', (scheme_id,)).fetchall()

    if request.method == 'POST':
        extra = request.form.to_dict()
        result, reasons = evaluate_eligibility(user, criteria, extra)
        db.execute('INSERT INTO eligibility_history (user_id, scheme_id, result, reason, checked_at) VALUES (?, ?, ?, ?, ?)',
                   (session['user_id'], scheme_id, result, '; '.join(reasons), datetime.now().isoformat()))
        db.execute('INSERT INTO user_activity (user_id, action, timestamp) VALUES (?, ?, ?)',
                   (session['user_id'], f'checked eligibility for scheme {scheme_id}', datetime.now().isoformat()))
        db.commit()
        return render_template('eligibility_result.html', scheme=scheme, result=result, reasons=reasons)

    missing_fields = get_missing_fields(user, criteria)
    return render_template('check_eligibility.html', scheme=scheme, criteria=criteria, missing_fields=missing_fields)

def evaluate_eligibility(user, criteria, extra={}):
    reasons = []
    eligible = True
    user_data = dict(user)
    user_data.update(extra)

    for c in criteria:
        field = c['field']
        operator = c['operator']
        value = c['value']
        user_val = user_data.get(field)

        if user_val is None:
            reasons.append(f"Missing information: {field}")
            eligible = False
            continue

        try:
            if operator == 'eq':
                if str(user_val).lower() != str(value).lower():
                    reasons.append(f"{c['label']}: Required '{value}', you have '{user_val}'")
                    eligible = False
            elif operator == 'lte':
                if float(user_val) > float(value):
                    reasons.append(f"{c['label']}: Must be ≤ {value}, yours is {user_val}")
                    eligible = False
            elif operator == 'gte':
                if float(user_val) < float(value):
                    reasons.append(f"{c['label']}: Must be ≥ {value}, yours is {user_val}")
                    eligible = False
            elif operator == 'lt':
                if float(user_val) >= float(value):
                    reasons.append(f"{c['label']}: Must be < {value}, yours is {user_val}")
                    eligible = False
            elif operator == 'gt':
                if float(user_val) <= float(value):
                    reasons.append(f"{c['label']}: Must be > {value}, yours is {user_val}")
                    eligible = False
            elif operator == 'in':
                allowed = [v.strip().lower() for v in value.split(',')]
                if str(user_val).lower() not in allowed:
                    reasons.append(f"{c['label']}: Must be one of [{value}], yours is '{user_val}'")
                    eligible = False
        except Exception:
            pass

    return ('eligible' if eligible else 'not_eligible'), reasons

def get_missing_fields(user, criteria):
    missing = []
    user_data = dict(user)
    for c in criteria:
        if c['field'] not in user_data or user_data[c['field']] is None:
            missing.append({'field': c['field'], 'label': c['label']})
    return missing

# ─── Admin Routes ────────────────────────────────────────────────────────────

@app.route('/admin')
@admin_required
def admin_dashboard():
    db = get_db()
    total_users = db.execute('SELECT COUNT(*) FROM users WHERE role = "user"').fetchone()[0]
    total_schemes = db.execute('SELECT COUNT(*) FROM schemes').fetchone()[0]
    total_checks = db.execute('SELECT COUNT(*) FROM eligibility_history').fetchone()[0]
    recent_activity = db.execute('''SELECT a.*, u.username FROM user_activity a 
                                    JOIN users u ON a.user_id = u.id 
                                    ORDER BY a.timestamp DESC LIMIT 20''').fetchall()
    return render_template('admin/dashboard.html', total_users=total_users,
                           total_schemes=total_schemes, total_checks=total_checks,
                           recent_activity=recent_activity)

@app.route('/admin/users')
@admin_required
def admin_users():
    db = get_db()
    users = db.execute('SELECT * FROM users ORDER BY id DESC').fetchall()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_user(user_id):
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if request.method == 'POST':
        data = request.form
        db.execute('''UPDATE users SET full_name=?, age=?, income=?, caste=?, gender=?, state=?, occupation=?, mobile=?, email=?, role=?
                      WHERE id=?''',
                   (data['full_name'], data['age'], data['income'], data['caste'], data['gender'],
                    data['state'], data['occupation'], data['mobile'], data['email'], data['role'], user_id))
        db.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/users/delete/<int:user_id>')
@admin_required
def admin_delete_user(user_id):
    db = get_db()
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    flash('User deleted.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/schemes')
@admin_required
def admin_schemes():
    db = get_db()
    schemes_list = db.execute('SELECT * FROM schemes ORDER BY state, category').fetchall()
    return render_template('admin/schemes.html', schemes=schemes_list)

@app.route('/admin/schemes/add', methods=['GET', 'POST'])
@admin_required
def admin_add_scheme():
    if request.method == 'POST':
        data = request.form
        db = get_db()
        db.execute('''INSERT INTO schemes (name, description, benefits, documents, category, state)
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   (data['name'], data['description'], data['benefits'], data['documents'],
                    data['category'], data['state']))
        scheme_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        # Save criteria
        fields = request.form.getlist('crit_field')
        labels = request.form.getlist('crit_label')
        operators = request.form.getlist('crit_operator')
        values = request.form.getlist('crit_value')
        for f, l, o, v in zip(fields, labels, operators, values):
            if f and l and o and v:
                db.execute('INSERT INTO eligibility_criteria (scheme_id, field, label, operator, value) VALUES (?,?,?,?,?)',
                           (scheme_id, f, l, o, v))
        db.commit()
        flash('Scheme added.', 'success')
        return redirect(url_for('admin_schemes'))
    return render_template('admin/scheme_form.html', scheme=None, criteria=[])

@app.route('/admin/schemes/edit/<int:scheme_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_scheme(scheme_id):
    db = get_db()
    scheme = db.execute('SELECT * FROM schemes WHERE id = ?', (scheme_id,)).fetchone()
    criteria = db.execute('SELECT * FROM eligibility_criteria WHERE scheme_id = ?', (scheme_id,)).fetchall()
    if request.method == 'POST':
        data = request.form
        db.execute('''UPDATE schemes SET name=?, description=?, benefits=?, documents=?, category=?, state=? WHERE id=?''',
                   (data['name'], data['description'], data['benefits'], data['documents'],
                    data['category'], data['state'], scheme_id))
        db.execute('DELETE FROM eligibility_criteria WHERE scheme_id = ?', (scheme_id,))
        fields = request.form.getlist('crit_field')
        labels = request.form.getlist('crit_label')
        operators = request.form.getlist('crit_operator')
        values = request.form.getlist('crit_value')
        for f, l, o, v in zip(fields, labels, operators, values):
            if f and l and o and v:
                db.execute('INSERT INTO eligibility_criteria (scheme_id, field, label, operator, value) VALUES (?,?,?,?,?)',
                           (scheme_id, f, l, o, v))
        db.commit()
        flash('Scheme updated.', 'success')
        return redirect(url_for('admin_schemes'))
    return render_template('admin/scheme_form.html', scheme=scheme, criteria=criteria)

@app.route('/admin/schemes/delete/<int:scheme_id>')
@admin_required
def admin_delete_scheme(scheme_id):
    db = get_db()
    db.execute('DELETE FROM schemes WHERE id = ?', (scheme_id,))
    db.execute('DELETE FROM eligibility_criteria WHERE scheme_id = ?', (scheme_id,))
    db.commit()
    flash('Scheme deleted.', 'success')
    return redirect(url_for('admin_schemes'))

@app.route('/admin/history')
@admin_required
def admin_history():
    db = get_db()
    history = db.execute('''SELECT h.*, u.username, s.name as scheme_name 
                            FROM eligibility_history h 
                            JOIN users u ON h.user_id = u.id 
                            JOIN schemes s ON h.scheme_id = s.id 
                            ORDER BY h.checked_at DESC''').fetchall()
    return render_template('admin/history.html', history=history)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
