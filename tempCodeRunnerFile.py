from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from models import db, User, Resume
import os

# ---------------- APP SETUP ---------------- #
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change to a strong secret key
bcrypt = Bcrypt(app)

# ---------------- DATABASE CONFIG (MySQL) ---------------- #
DB_USER = 'flask_user'
DB_PASSWORD = 'ashwin'
DB_HOST = 'localhost'
DB_NAME = 'resume_analyzer'

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# ---------------- UPLOAD CONFIG ---------------- #
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------------- ROUTES ---------------- #

@app.route('/')
def home():
    return render_template('home.html')


# ---------------- REGISTER ---------------- #
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(url_for('register'))

        if role == "admin":
            admin_key = request.form.get('adminKey')
            if admin_key != "ADMIN123":
                flash("Incorrect Admin Secret Key!", "danger")
                return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# ---------------- LOGIN ---------------- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        user = User.query.filter_by(email=email, role=role).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['name'] = user.name
            flash(f"Welcome, {user.name}!", "success")

            return redirect(url_for('candidate_dashboard') if role == "candidate" else url_for('admin_dashboard'))
        else:
            flash("Invalid credentials!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')


# ---------------- CANDIDATE DASHBOARD ---------------- #
@app.route('/candidate')
def candidate_dashboard():
    if 'user_id' not in session or session.get('role') != 'candidate':
        flash("Please login as Candidate to access this page.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    resumes = Resume.query.filter_by(user_id=user.id).all()
    return render_template('candidate.html', user=user, resumes=resumes)


# ---------------- RESUME UPLOAD ---------------- #
@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'user_id' not in session or session.get('role') != 'candidate':
        flash("Please login as Candidate to upload a resume.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    file = request.files.get('resume')
    if file and file.filename:
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Save resume record in DB
        new_resume = Resume(user_id=user.id, file_name=filename, parsed_text="")
        db.session.add(new_resume)
        db.session.commit()
        flash("Resume uploaded successfully!", "success")
    else:
        flash("Please select a valid file!", "warning")

    return redirect(url_for('candidate_dashboard'))


# ---------------- VIEW RESUME ---------------- #
@app.route('/view_resume/<int:resume_id>')
def view_resume(resume_id):
    if 'user_id' not in session:
        flash("Please login to view resumes.", "warning")
        return redirect(url_for('login'))

    resume = Resume.query.get_or_404(resume_id)

    # Check permission: candidates can only view their own resumes
    if session.get('role') == 'candidate' and resume.user_id != session.get('user_id'):
        flash("You do not have permission to view this resume.", "danger")
        return redirect(url_for('candidate_dashboard'))

    return render_template('view_resume.html', resume=resume)


# ---------------- ADMIN DASHBOARD ---------------- #
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please login as Admin to access this page.", "warning")
        return redirect(url_for('login'))

    resumes = Resume.query.join(User).all()
    return render_template('admin.html', resumes=resumes)


# ---------------- LOGOUT ---------------- #
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
