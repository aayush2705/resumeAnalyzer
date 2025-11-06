from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_bcrypt import Bcrypt
from models import db, User, Resume, Feedback
from werkzeug.utils import secure_filename
from modules.parser import extract_text, analyze_resume
from io import BytesIO
from openpyxl import Workbook
import os
import traceback
from datetime import datetime
from sqlalchemy import func
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from models import Course
import json

# ---------------- ROADMAP DATA ----------------
ROADMAPS = {
   'Android Development': {
    'title': 'Android Development Roadmap',
    'steps': [
        'Learn Java or Kotlin',
        'Understand Android Studio and XML Layouts',
        'Learn Android Jetpack Components',
        'Work with APIs and Databases',
        'Publish Your First App on Play Store'
    ],
    'image': 'static/roadmaps/android_development_roadmap.png'
},
'iOS Development': {
    'title': 'iOS Development Roadmap',
    'steps': [
        'Learn Swift Programming Language',
        'Understand Xcode and Storyboards',
        'Learn UIKit and SwiftUI',
        'Implement Core Data and Networking',
        'Publish App on App Store'
    ],
    'image': 'static/roadmaps/ios_development_roadmap.png'
},

}

# ---------------- APP SETUP ---------------- #
app = Flask(__name__)
app.secret_key = "your_secret_key"
bcrypt = Bcrypt(app)

# ---------------- DATABASE CONFIG ---------------- #
# ✅ Local fallback (for testing locally)
LOCAL_DB_URI = "sqlite:///resume_analyzer.db"

# ✅ Use Render PostgreSQL connection in production
DATABASE_URL = os.environ.get("DATABASE_URL", LOCAL_DB_URI)

# 🛠️ SQLAlchemy requires the prefix "postgresql+psycopg2://" instead of "postgres://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

@app.route('/add_courses')
def add_courses():
    from models import Course

    # Define your course data
    courses_data = {
        'Data Science': [
            ['Machine Learning Crash Course by Google [Free]', 'https://developers.google.com/machine-learning/crash-course'],
            ['Machine Learning A-Z by Udemy','https://www.udemy.com/course/machinelearning/'],
            ['Machine Learning by Andrew NG','https://www.coursera.org/learn/machine-learning'],
            ['Data Scientist Master Program of Simplilearn (IBM)','https://www.simplilearn.com/big-data-and-analytics/senior-data-scientist-masters-program-training'],
            ['Data Science Foundations: Fundamentals by LinkedIn','https://www.linkedin.com/learning/data-science-foundations-fundamentals-5'],
            ['Data Scientist with Python','https://www.datacamp.com/tracks/data-scientist-with-python'],
            ['Programming for Data Science with Python','https://www.udacity.com/course/programming-for-data-science-nanodegree--nd104'],
            ['Programming for Data Science with R','https://www.udacity.com/course/programming-for-data-science-nanodegree-with-R--nd118'],
            ['Introduction to Data Science','https://www.udacity.com/course/introduction-to-data-science--cd0017'],
            ['Intro to Machine Learning with TensorFlow','https://www.udacity.com/course/intro-to-machine-learning-with-tensorflow-nanodegree--nd230']
        ],
        'Web Development': [
            ['Django Crash course [Free]','https://youtu.be/e1IyzVyrLSU'],
            ['Python and Django Full Stack Web Developer Bootcamp','https://www.udemy.com/course/python-and-django-full-stack-web-developer-bootcamp'],
            ['React Crash Course [Free]','https://youtu.be/Dorf8i6lCuk'],
            ['ReactJS Project Development Training','https://www.dotnettricks.com/training/masters-program/reactjs-certification-training'],
            ['Full Stack Web Developer - MEAN Stack','https://www.simplilearn.com/full-stack-web-developer-mean-stack-certification-training'],
            ['Node.js and Express.js [Free]','https://youtu.be/Oe421EPjeBE'],
            ['Flask: Develop Web Applications in Python','https://www.educative.io/courses/flask-develop-web-applications-in-python'],
            ['Full Stack Web Developer by Udacity','https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd0044'],
            ['Front End Web Developer by Udacity','https://www.udacity.com/course/front-end-web-developer-nanodegree--nd0011'],
            ['Become a React Developer by Udacity','https://www.udacity.com/course/react-nanodegree--nd019']
        ],
        'Android Development': [
            ['Android Development for Beginners [Free]','https://youtu.be/fis26HvvDII'],
            ['Android App Development Specialization','https://www.coursera.org/specializations/android-app-development'],
            ['Associate Android Developer Certification','https://grow.google/androiddev/#?modal_active=none'],
            ['Become an Android Kotlin Developer by Udacity','https://www.udacity.com/course/android-kotlin-developer-nanodegree--nd940'],
            ['Android Basics by Google','https://www.udacity.com/course/android-basics-nanodegree-by-google--nd803'],
            ['The Complete Android Developer Course','https://www.udemy.com/course/complete-android-n-developer-course/'],
            ['Building an Android App with Architecture Components','https://www.linkedin.com/learning/building-an-android-app-with-architecture-components'],
            ['Android App Development Masterclass using Kotlin','https://www.udemy.com/course/android-oreo-kotlin-app-masterclass/'],
            ['Flutter & Dart - The Complete Flutter App Development Course','https://www.udemy.com/course/flutter-dart-the-complete-flutter-app-development-course/'],
            ['Flutter App Development Course [Free]','https://youtu.be/rZLR5olMR64']
        ],
        'iOS Development': [
            ['IOS App Development by LinkedIn','https://www.linkedin.com/learning/subscription/topics/ios'],
            ['iOS & Swift - The Complete iOS App Development Bootcamp','https://www.udemy.com/course/ios-13-app-development-bootcamp/'],
            ['Become an iOS Developer','https://www.udacity.com/course/ios-developer-nanodegree--nd003'],
            ['iOS App Development with Swift Specialization','https://www.coursera.org/specializations/app-development'],
            ['Mobile App Development with Swift','https://www.edx.org/professional-certificate/curtinx-mobile-app-development-with-swift'],
            ['Swift Course by LinkedIn','https://www.linkedin.com/learning/subscription/topics/swift-2'],
            ['Objective-C Crash Course for Swift Developers','https://www.udemy.com/course/objectivec/'],
            ['Learn Swift by Codecademy','https://www.codecademy.com/learn/learn-swift'],
            ['Swift Tutorial - Full Course for Beginners [Free]','https://youtu.be/comQ1-x2a1Q'],
            ['Learn Swift Fast - [Free]','https://youtu.be/FcsY1YPBwzQ']
        ],
        'UI/UX Design': [
            ['Google UX Design Professional Certificate','https://www.coursera.org/professional-certificates/google-ux-design'],
            ['UI / UX Design Specialization','https://www.coursera.org/specializations/ui-ux-design'],
            ['The Complete App Design Course - UX, UI and Design Thinking','https://www.udemy.com/course/the-complete-app-design-course-ux-and-ui-design/'],
            ['UX & Web Design Master Course: Strategy, Design, Development','https://www.udemy.com/course/ux-web-design-master-course-strategy-design-development/'],
            ['DESIGN RULES: Principles + Practices for Great UI Design','https://www.udemy.com/course/design-rules/'],
            ['Become a UX Designer by Udacity','https://www.udacity.com/course/ux-designer-nanodegree--nd578'],
            ['Adobe XD Tutorial: User Experience Design Course [Free]','https://youtu.be/68w2VwalD5w'],
            ['Adobe XD for Beginners [Free]','https://youtu.be/WEljsc2jorI'],
            ['Adobe XD in Simple Way','https://learnux.io/course/adobe-xd']
        ]
    }

    # Insert into DB
    for category, course_list in courses_data.items():
        for course_name, course_url in course_list:
            if not Course.query.filter_by(name=course_name).first():
                db.session.add(Course(category=category, name=course_name, url=course_url))

    db.session.commit()
    return "✅ Courses added successfully!"





# ---------------- UPLOAD CONFIG ---------------- #
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------------- HELPER KEYWORDS ---------------- #
DS_KEYWORD = {'tensorflow', 'keras', 'pytorch', 'machine learning', 'deep learning', 'flask', 'streamlit', 'scikit-learn'}
WEB_KEYWORD = {'react', 'django', 'node js', 'node', 'php', 'laravel', 'magento', 'wordpress', 'javascript', 'angular js', 'c#', 'asp.net'}
ANDROID_KEYWORD = {'android', 'flutter', 'kotlin', 'xml', 'kivy', 'java'}
IOS_KEYWORD = {'ios', 'swift', 'cocoa', 'xcode', 'objective-c'}
UIUX_KEYWORD = {'ux', 'adobe xd', 'figma', 'balsamiq', 'ui', 'prototyping', 'wireframes'}

# ---------------- HOME ---------------- #
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

    file = request.files.get('resume')
    if not file or file.filename == '':
        flash("Please select a valid file!", "warning")
        return redirect(url_for('candidate_dashboard'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    user = User.query.get(session['user_id'])

    try:
        text = extract_text(filepath)
        analysis = analyze_resume(text)

        new_resume = Resume(
            user_id=user.id,
            file_name=filename,
            parsed_text=analysis.get('summary', ''),
            skills=', '.join(analysis.get('skills_found', [])),
            experience=str(analysis.get('experience', '')),
            suggested_roles=analysis.get('suggested_roles', '')
        )
        db.session.add(new_resume)
        db.session.commit()

        flash("Resume analyzed successfully!", "success")
        return redirect(url_for('view_resume', resume_id=new_resume.id))

    except Exception as e:
        traceback.print_exc()
        flash(f"Error analyzing resume: {str(e)}", "danger")
        return redirect(url_for('candidate_dashboard'))
    
# ---------------- VIEW RESUME ---------------- #
@app.route('/view_resume/<int:resume_id>')
def view_resume(resume_id):
    if 'user_id' not in session:
        flash("Please login to view resumes.", "warning")
        return redirect(url_for('login'))

    resume = Resume.query.get_or_404(resume_id)
    if session.get('role') == 'candidate' and resume.user_id != session.get('user_id'):
        flash("You do not have permission to view this resume.", "danger")
        return redirect(url_for('candidate_dashboard'))

    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], resume.file_name)
        text = extract_text(filepath)
        analysis = analyze_resume(text)

        rt_lower = text.lower()
        cand_level = "Fresher"
        if 'internship' in rt_lower:
            cand_level = "Intermediate"
        elif 'experience' in rt_lower:
            cand_level = "Experienced"

        skills_list = analysis.get('skills_found', [])
        predicted_role, recommended_skills, courses = None, [], []

        # ---------- ROLE PREDICTION ----------
        if any(skill.lower() in DS_KEYWORD for skill in skills_list):
            predicted_role = 'Data Science'
            recommended_skills = ['Tensorflow', 'Keras', 'Pytorch', 'Flask', 'Streamlit']
            courses = [
                {"name": "Machine Learning Crash Course (Google)", "link": "https://developers.google.com/machine-learning/crash-course"},
                {"name": "Deep Learning Specialization (Coursera)", "link": "https://www.coursera.org/specializations/deep-learning"}
            ]

        elif any(skill.lower() in WEB_KEYWORD for skill in skills_list):
            predicted_role = 'Web Development'
            recommended_skills = ['React', 'Node JS', 'Django', 'PHP', 'Laravel']
            courses = [
                {"name": "Full-Stack Web Dev (Udemy)", "link": "https://www.udemy.com/course/the-complete-web-developer-course-2/"},
                {"name": "JavaScript Essentials (freeCodeCamp)", "link": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/"}
            ]

        elif any(skill.lower() in ANDROID_KEYWORD for skill in skills_list):
            predicted_role = 'Android Development'
            recommended_skills = ['Kotlin', 'Flutter', 'XML', 'SQLite', 'Firebase']
            courses = [
                {"name": "Android App Development (Google)", "link": "https://developer.android.com/courses"},
                {"name": "Flutter Bootcamp (Udemy)", "link": "https://www.udemy.com/course/flutter-bootcamp-with-dart/"}
            ]

        elif any(skill.lower() in IOS_KEYWORD for skill in skills_list):
            predicted_role = 'iOS Development'
            recommended_skills = ['Swift', 'Xcode', 'Cocoa Touch', 'Auto Layout']
            courses = [
                {"name": "iOS Development with Swift (Udemy)", "link": "https://www.udemy.com/course/ios-13-app-development-bootcamp/"}
            ]

        elif any(skill.lower() in UIUX_KEYWORD for skill in skills_list):
            predicted_role = 'UI/UX Design'
            recommended_skills = ['Figma', 'Adobe XD', 'Wireframes', 'Prototyping']
            courses = [
                {"name": "UI/UX Design Essentials (Udemy)", "link": "https://www.udemy.com/course/ui-ux-web-design-using-adobe-xd/"},
                {"name": "Design Thinking (Coursera)", "link": "https://www.coursera.org/learn/uva-darden-design-thinking-innovation"}
            ]
            

        # ---------- RESUME SCORING ----------
        sections = {
            "objective": (['objective', 'summary'], 6),
            "education": (['education', 'degree', 'college'], 12),
            "experience": (['experience', 'internship'], 16),
            "skills": (['skills'], 7),
            "projects": (['project'], 19),
            "certifications": (['certificate'], 12),
            "achievements": (['achievement'], 13),
            "hobbies": (['hobbies'], 4),
            "interests": (['interests'], 5),
        }

        resume_score, tips = 0, []
        for key, (words, points) in sections.items():
            if any(w in rt_lower for w in words):
                resume_score += points
                tips.append(f"[+] Great! You included your {key} section.")
            else:
                tips.append(f"[-] Please add your {key} section to improve your resume.")

        resume_score = min(resume_score, 100)

        # ---------- UPDATE DATABASE ----------
        resume.predicted_role = predicted_role
        resume.resume_score = resume_score
        resume.tips = '\n'.join(tips)
        resume.recommended_skills = ', '.join(recommended_skills)
        resume.courses = json.dumps([c['name'] for c in courses])
        resume.course_links = json.dumps([c['link'] for c in courses])
        db.session.commit()

        # ---------- TEMPORARY DISPLAY ----------
        resume.candidate_name = User.query.get(resume.user_id).name
        resume.candidate_level = cand_level

    except Exception as e:
        traceback.print_exc()
        flash(f"Error analyzing resume: {str(e)}", "danger")

    # ---------- SAFELY PARSE COURSES ----------
    courses = []
    if resume.courses and resume.course_links:
        try:
            course_names = json.loads(resume.courses)
            course_links = json.loads(resume.course_links)
            courses = [{"name": n, "link": l} for n, l in zip(course_names, course_links)]
        except Exception:
            pass

    # ---------- SAFELY PARSE SKILLS & TIPS ----------
    if resume.recommended_skills:
        if isinstance(resume.recommended_skills, list):
            recommended_skills = [s.strip() for s in resume.recommended_skills]
        else:
            recommended_skills = [s.strip() for s in resume.recommended_skills.split(",") if s.strip()]
    else:
        recommended_skills = []

    tips = resume.tips.split("\n") if resume.tips else []
    
      # ---------- ADD ROADMAP ----------
    roadmap = ROADMAPS.get(resume.predicted_role)
    # ---------- RENDER TEMPLATE ----------
    return render_template(
        "view_resume.html",
        resume={
            "id": resume.id,
            "candidate_name": resume.candidate_name or "Unknown",
            "candidate_level": resume.candidate_level or "N/A",
            "parsed_text": getattr(resume, "parsed_text", ""),
            "skills": getattr(resume, "skills", ""),
            "predicted_role": resume.predicted_role,
            "recommended_skills": recommended_skills,
            "tips": tips,
            "score": resume.resume_score or 0,
            "courses": courses,
            "roadmap": roadmap  # 👈 Added roadmap
        }
    )

@app.route('/download_resume_pdf/<int:resume_id>')
def download_resume_pdf(resume_id):
    # Fetch resume details from database
    resume = Resume.query.get_or_404(resume_id)

    # Create an in-memory PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    content = []

    # ------------------- TITLE -------------------
    title_style = styles['Title']
    title_style.alignment = TA_CENTER
    content.append(Paragraph("Resume Analysis Report", title_style))
    content.append(Spacer(1, 0.3 * inch))

    # ------------------- CANDIDATE INFO -------------------
    user = resume.user  # via relationship
    content.append(Paragraph(f"<b>Candidate Name:</b> {user.name}", styles["Normal"]))
    content.append(Paragraph(f"<b>Candidate Email:</b> {user.email}", styles["Normal"]))
    content.append(Spacer(1, 0.2 * inch))

    # ------------------- SUMMARY -------------------
    content.append(Paragraph("<b>Analysis Summary:</b>", styles["Heading3"]))
    content.append(Paragraph(resume.parsed_text or "No summary available.", styles["Normal"]))
    content.append(Spacer(1, 0.2 * inch))

    # ------------------- SKILLS -------------------
    content.append(Paragraph("<b>Current Skills:</b>", styles["Heading3"]))
    if resume.skills:
        if isinstance(resume.skills, str):
            skills_text = resume.skills
        else:
            # if stored as list in JSON form
            skills_text = ", ".join(json.loads(resume.skills))
        content.append(Paragraph(skills_text, styles["Normal"]))
    else:
        content.append(Paragraph("No skills found.", styles["Normal"]))
    content.append(Spacer(1, 0.2 * inch))

    # ------------------- PREDICTED ROLE -------------------
    content.append(Paragraph("<b>Predicted Job Role:</b>", styles["Heading3"]))
    content.append(Paragraph(resume.predicted_role or "Not available.", styles["Normal"]))
    content.append(Spacer(1, 0.2 * inch))

    # ------------------- RECOMMENDED SKILLS -------------------
    content.append(Paragraph("<b>Recommended Skills:</b>", styles["Heading3"]))
    if resume.recommended_skills:
        if isinstance(resume.recommended_skills, str):
            recommended_skills = [s.strip() for s in resume.recommended_skills.split(",")]
        else:
            recommended_skills = resume.recommended_skills
        for skill in recommended_skills:
            content.append(Paragraph(f"- {skill}", styles["Normal"]))
    else:
        content.append(Paragraph("No recommendations available.", styles["Normal"]))
    content.append(Spacer(1, 0.2 * inch))

    # ------------------- COURSES -------------------
    content.append(Paragraph("<b>Courses & Certifications:</b>", styles["Heading3"]))
    if resume.courses:
        try:
            course_names = json.loads(resume.courses)
            course_links = json.loads(resume.course_links or "[]")
            for name, link in zip(course_names, course_links):
                content.append(Paragraph(f"- <a href='{link}'>{name}</a>", styles["Normal"]))
        except Exception:
            # fallback if data not JSON encoded
            content.append(Paragraph(resume.courses, styles["Normal"]))
    else:
        content.append(Paragraph("No course recommendations available.", styles["Normal"]))
    content.append(Spacer(1, 0.2 * inch))

    # ------------------- TIPS -------------------
    content.append(Paragraph("<b>Resume Tips:</b>", styles["Heading3"]))
    if resume.tips:
        tips_list = [t.strip() for t in resume.tips.split("\n")]
        for tip in tips_list:
            color = "green" if tip.startswith("[+]") else "red"
            content.append(Paragraph(f'<font color="{color}">{tip}</font>', styles["Normal"]))
    else:
        content.append(Paragraph("No tips available.", styles["Normal"]))
    content.append(Spacer(1, 0.2 * inch))

    # ------------------- SCORE -------------------
    content.append(Paragraph("<b>Overall Resume Score:</b>", styles["Heading3"]))
    content.append(Paragraph(f"{resume.resume_score or 'N/A'} / 100", styles["Normal"]))

    # ------------------- BUILD PDF -------------------
    doc.build(content)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{user.name}_Resume_Analysis.pdf",
        mimetype="application/pdf"
    )

# ---------------- ADMIN DASHBOARD ---------------- #
@app.route('/admin')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Please login as Admin to access this page.", "warning")
        return redirect(url_for('login'))

    total_users = User.query.count()

    # Build a safe list of resume rows for template (dictionary objects)
    resumes_rows = []
    all_resumes = Resume.query.order_by(Resume.id.desc()).all()
    for r in all_resumes:
        user = User.query.get(r.user_id) if r.user_id else None
        # handle possible timestamp fields
        uploaded_ts = None
        for attr in ('created_at', 'uploaded_at', 'timestamp'):
            if hasattr(r, attr):
                uploaded_ts = getattr(r, attr)
                break
        # format timestamp if datetime-like
        uploaded_str = uploaded_ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(uploaded_ts, datetime) else (str(uploaded_ts) if uploaded_ts else "-")

        resumes_rows.append({
            'id': getattr(r, 'id', None),
            'user_name': user.name if user else getattr(r, 'candidate_name', '-') or '-',
            'email': user.email if user else '-',
            'role': user.role if user else '-',
            'file_name': getattr(r, 'file_name', '-') or '-',
            'predicted_role': getattr(r, 'predicted_role', None) or "Not Analyzed",
            'uploaded_at': uploaded_str,
        })

    # Fetch feedback list for template
    feedback_rows = []
    all_feedbacks = Feedback.query.order_by(getattr(Feedback, 'id', Feedback.__table__.c.keys()[0]).desc()).all() if Feedback.query.count() > 0 else []
    for f in all_feedbacks:
        # handle possible timestamp fields
        fb_ts = None
        for attr in ('created_at', 'submitted_at', 'timestamp'):
            if hasattr(f, attr):
                fb_ts = getattr(f, attr)
                break
        fb_str = fb_ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(fb_ts, datetime) else (str(fb_ts) if fb_ts else "-")
        feedback_rows.append({
            'id': getattr(f, 'id', None),
            'name': getattr(f, 'name', '') or '',
            'email': getattr(f, 'email', '') or '',
            'rating': getattr(f, 'rating', '') or '',
            'comments': getattr(f, 'comments', '') or '',
            'created_at': fb_str
        })

    # -----------------------
  # Ratings chart
    rating_counts_query = db.session.query(Feedback.rating, func.count(Feedback.id)).group_by(Feedback.rating).all()
    rating_labels = [str(rating or "No Rating") for rating, _ in rating_counts_query]
    rating_counts = [cnt for _, cnt in rating_counts_query]

    if not rating_labels:
        rating_labels, rating_counts = ['No Rating'], [0]

    # Predicted roles chart
    predicted_query = db.session.query(Resume.predicted_role, func.count(Resume.id)).group_by(Resume.predicted_role).all()
    predicted_labels = [role or 'Not Analyzed' for role, _ in predicted_query]
    predicted_counts = [cnt for _, cnt in predicted_query]
    if not predicted_labels:
        predicted_labels, predicted_counts = ['Not Analyzed'], [0]

    # Score distribution
    score_buckets = {'0-40': 0, '41-60': 0, '61-80': 0, '81-100': 0}
    for (score,) in db.session.query(Resume.resume_score).all():
        if score is None:
            continue
        if score <= 40:
            score_buckets['0-40'] += 1
        elif score <= 60:
            score_buckets['41-60'] += 1
        elif score <= 80:
            score_buckets['61-80'] += 1
        else:
            score_buckets['81-100'] += 1

    score_labels = list(score_buckets.keys())
    score_counts = list(score_buckets.values())

    return render_template(
        'admin.html',
        total_users=total_users,
        resumes=resumes_rows,
        feedbacks=feedback_rows,
        rating_labels=rating_labels,
        rating_counts=rating_counts,
        predicted_labels=predicted_labels,
        predicted_counts=predicted_counts,
        score_labels=score_labels,
        score_counts=score_counts
    )

# ---------------- EXPORT ALL USERS ---------------- #
@app.route('/export_excel')
def export_excel():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    resumes = Resume.query.order_by(Resume.id.desc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "All Users"
    ws.append(["ID", "User Name", "Email", "Role", "Resume File", "Predicted Role", "Uploaded On"])

    for r in resumes:
        user = User.query.get(r.user_id) if r.user_id else None
        uploaded_ts = None
        for attr in ('created_at', 'uploaded_at', 'timestamp'):
            if hasattr(r, attr):
                uploaded_ts = getattr(r, attr)
                break
        uploaded_str = uploaded_ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(uploaded_ts, datetime) else (str(uploaded_ts) if uploaded_ts else "-")

        ws.append([
            r.id,
            user.name if user else "-",
            user.email if user else "-",
            user.role if user else "-",
            getattr(r, 'file_name', '-') or '-',
            getattr(r, 'predicted_role', None) or "Not Analyzed",
            uploaded_str
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name='all_users_report.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# ---------------- EXPORT USER REPORT ---------------- #
@app.route('/export_user_excel/<email>')
def export_user_excel(email):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("No user found with that email.", "warning")
        return redirect(url_for('admin_dashboard'))

    resumes = Resume.query.filter_by(user_id=user.id).order_by(Resume.id.desc()).all()

    if not resumes:
        flash("No data found for this user.", "warning")
        return redirect(url_for('admin_dashboard'))

    wb = Workbook()
    ws = wb.active
    ws.title = "User Report"
    ws.append(["Resume ID", "Resume File", "Predicted Role", "Uploaded On"])

    for r in resumes:
        uploaded_ts = None
        for attr in ('created_at', 'uploaded_at', 'timestamp'):
            if hasattr(r, attr):
                uploaded_ts = getattr(r, attr)
                break
        uploaded_str = uploaded_ts.strftime("%Y-%m-%d %H:%M:%S") if isinstance(uploaded_ts, datetime) else (str(uploaded_ts) if uploaded_ts else "-")

        ws.append([
            r.id,
            getattr(r, 'file_name', '-') or '-',
            getattr(r, 'predicted_role', None) or "Not Analyzed",
            uploaded_str
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"{user.name or 'user'}_report.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# ---------------- FEEDBACK ---------------- #
@app.route('/feedback')
def feedback():
    name = session.get('name', '')
    email = User.query.get(session['user_id']).email if 'user_id' in session else ''
    return render_template('feedback.html', name=name, email=email)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        rating = request.form.get('rating')
        comments = request.form.get('comments')
        user_id = session.get('user_id')

        new_feedback = Feedback(
            user_id=user_id,
            name=name,
            email=email,
            rating=rating,
            comments=comments
        )
        db.session.add(new_feedback)
        db.session.commit()

        flash("Thank you for your feedback!", "success")
    except Exception as e:
        traceback.print_exc()
        flash(f"Error saving feedback: {str(e)}", "danger")

    return redirect(url_for('candidate_dashboard'))

@app.route("/roadmaps")
def show_roadmaps():
    roadmaps = [
        {"name": "Data Science", "image": "roadmaps/data_science_roadmap.png"},
        {"name": "Web Development", "image": "roadmaps/web_development_roadmap.png"},
        {"name": "Android Development", "image": "roadmaps/android_development_roadmap.png"},
        {"name": "iOS Development", "image": "roadmaps/ios_development_roadmap.png"},
        {"name": "UI/UX Design", "image": "roadmaps/ui_ux_design_roadmap.png"},
    ]
    return render_template("roadmap.html", roadmaps=roadmaps)

# ---------------- LOGOUT ---------------- #
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=port)
