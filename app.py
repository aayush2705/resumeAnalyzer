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
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Image as RLImage, PageBreak
from reportlab.lib.styles import ParagraphStyle
from models import Course
import json


# ---------------- ROADMAP DATA ----------------
ROADMAPS = {
    'Data Science': {
        'title': 'Data Science Roadmap',
        'steps': [
            'Learn Python and Statistics Fundamentals',
            'Master Data Wrangling and Visualization with Pandas & Matplotlib',
            'Understand Machine Learning Algorithms',
            'Practice with Real-World Datasets (Kaggle)',
            'Build and Deploy End-to-End Data Science Projects'
        ],
        'image': 'static/roadmaps/data_science_roadmap.png'
    },
    'Web Development': {
        'title': 'Web Development Roadmap',
        'steps': [
            'Learn HTML, CSS, and JavaScript Basics',
            'Understand Frontend Frameworks like React or Angular',
            'Master Backend with Node.js, Django, or Flask',
            'Work with Databases like MySQL or MongoDB',
            'Deploy Full Stack Applications on Cloud Platforms'
        ],
        'image': 'static/roadmaps/web_development_roadmap.png'
    },
    'Android Development': {
        'title': 'Android Development Roadmap',
        'steps': [
            'Learn Java or Kotlin for Android',
            'Understand Android Studio and XML Layouts',
            'Learn Android Jetpack Components and APIs',
            'Integrate SQLite and Firebase for Data Management',
            'Publish Your First App on Google Play Store'
        ],
        'image': 'static/roadmaps/android_development_roadmap.png'
    },
    'iOS Development': {
        'title': 'iOS Development Roadmap',
        'steps': [
            'Learn Swift and Xcode IDE',
            'Understand UIKit and SwiftUI Frameworks',
            'Implement Core Data and API Networking',
            'Build UI/UX for iOS Devices',
            'Publish Your First App on Apple App Store'
        ],
        'image': 'static/roadmaps/ios_development_roadmap.png'
    },
    'UI/UX Design': {
        'title': 'UI/UX Design Roadmap',
        'steps': [
            'Understand Design Thinking Process',
            'Learn Wireframing and Prototyping with Figma/Adobe XD',
            'Master Visual Design Principles',
            'Test and Iterate User Experience Flows',
            'Build a Professional UI/UX Design Portfolio'
        ],
        'image': 'static/roadmaps/ui_ux_design_roadmap.png'
    },
    'Data Analyst': {
        'title': 'Data Analyst Roadmap',
        'steps': [
            'Learn Excel, SQL, and Power BI/Tableau',
            'Understand Data Cleaning and Transformation',
            'Master Data Visualization Tools',
            'Learn Statistics and Basic Python Analysis',
            'Work on Business-Oriented Dashboards and Reports'
        ],
        'image': 'static/roadmaps/data_analyst_roadmap.png'
    },
    'Cloud & DevOps': {
        'title': 'Cloud & DevOps Roadmap',
        'steps': [
            'Learn Linux, Networking, and Shell Scripting',
            'Understand Cloud Platforms (AWS, Azure, GCP)',
            'Work with Docker and Kubernetes',
            'Implement CI/CD Pipelines and Infrastructure as Code',
            'Monitor and Optimize Deployments'
        ],
        'image': 'static/roadmaps/cloud_devops_roadmap.png'
    },
    'Cybersecurity': {
        'title': 'Cybersecurity Roadmap',
        'steps': [
            'Understand Networking and Operating Systems',
            'Learn Ethical Hacking Tools (Nmap, Burp Suite)',
            'Master Security Concepts: Firewalls, Encryption, SIEM',
            'Explore Vulnerability Management and Incident Response',
            'Pursue CEH or CompTIA Security+ Certification'
        ],
        'image': 'static/roadmaps/cybersecurity_roadmap.png'
    },
    'Quality Assurance': {
        'title': 'Quality Assurance Roadmap',
        'steps': [
            'Understand Software Testing Fundamentals',
            'Learn Manual and Automated Testing (Selenium/Postman)',
            'Master API and UI Testing Frameworks',
            'Integrate Testing into CI/CD Pipelines',
            'Explore QA Tools like JIRA and TestNG'
        ],
        'image': 'static/roadmaps/qa_roadmap.png'
    },
    'Business Analyst': {
        'title': 'Business Analyst Roadmap',
        'steps': [
            'Learn Requirement Gathering and Documentation',
            'Understand Agile and Scrum Methodologies',
            'Develop Analytical Thinking and Communication Skills',
            'Use Tools like Excel, JIRA, Power BI',
            'Collaborate on Project Reports and Stakeholder Analysis'
        ],
        'image': 'static/roadmaps/business_analyst_roadmap.png'
    },
    'Database Administrator': {
        'title': 'Database Administrator Roadmap',
        'steps': [
            'Learn SQL Fundamentals and Normalization',
            'Understand Database Design and Modeling',
            'Manage Backups, Recovery, and Performance Tuning',
            'Work with Oracle, PostgreSQL, or MySQL',
            'Secure and Monitor Database Systems'
        ],
        'image': 'static/roadmaps/database_admin_roadmap.png'
    },
    'AI / NLP Engineer': {
        'title': 'AI / NLP Engineer Roadmap',
        'steps': [
            'Understand NLP Fundamentals and Text Processing',
            'Learn Machine Learning and Deep Learning Basics',
            'Work with Transformers, BERT, and GPT Models',
            'Use Libraries like Hugging Face and SpaCy',
            'Deploy NLP Models into Production Environments'
        ],
        'image': 'static/roadmaps/nlp_engineer_roadmap.png'
    },
    'Product Manager': {
        'title': 'Product Manager Roadmap',
        'steps': [
            'Understand Product Lifecycle and Market Research',
            'Develop Communication and Leadership Skills',
            'Learn Agile and Scrum Frameworks',
            'Use Tools like JIRA, Notion, and Trello',
            'Work on Real Product Strategy and Launch Projects'
        ],
        'image': 'static/roadmaps/product_manager_roadmap.png'
    }
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

# # ---------------- HELPER KEYWORDS ---------------- #
# DS_KEYWORD = {'tensorflow', 'keras', 'pytorch', 'machine learning', 'deep learning', 'flask', 'streamlit', 'scikit-learn'}
# WEB_KEYWORD = {'react', 'django', 'node js', 'node', 'php', 'laravel', 'magento', 'wordpress', 'javascript', 'angular js', 'c#', 'asp.net'}
# ANDROID_KEYWORD = {'android', 'flutter', 'kotlin', 'xml', 'kivy', 'java'}
# IOS_KEYWORD = {'ios', 'swift', 'cocoa', 'xcode', 'objective-c'}
# UIUX_KEYWORD = {'ux', 'adobe xd', 'figma', 'balsamiq', 'ui', 'prototyping', 'wireframes'}
# ---------------- EXISTING ROLES ----------------
DS_KEYWORD = {
    'tensorflow', 'keras', 'pytorch', 'machine learning', 'deep learning',
    'flask', 'streamlit', 'scikit-learn', 'pandas', 'numpy', 'matplotlib',
    'seaborn', 'data analysis', 'data visualization', 'ai', 'nlp', 'opencv'
}

WEB_KEYWORD = {
    'react', 'django', 'node js', 'node', 'php', 'laravel', 'magento', 'wordpress',
    'javascript', 'angular js', 'angular', 'typescript', 'html', 'css', 'bootstrap',
    'express', 'mongodb', 'mysql', 'nextjs', 'rest api', 'frontend', 'backend'
}

ANDROID_KEYWORD = {
    'android', 'flutter', 'kotlin', 'xml', 'kivy', 'java', 'jetpack compose',
    'firebase', 'android studio'
}

IOS_KEYWORD = {
    'ios', 'swift', 'cocoa', 'xcode', 'objective-c', 'swiftui', 'uikit'
}

UIUX_KEYWORD = {
    'ux', 'adobe xd', 'figma', 'balsamiq', 'ui', 'prototyping', 'wireframes',
    'user experience', 'user interface', 'mockups', 'usability testing'
}

# ---------------- NEWLY ADDED ROLES ----------------

DATA_ANALYST_KEYWORD = {
    'excel', 'power bi', 'tableau', 'sql', 'data cleaning', 'data visualization',
    'pandas', 'numpy', 'statistics', 'analytics', 'matplotlib', 'seaborn'
}

CLOUD_DEVOPS_KEYWORD = {
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins',
    'ci/cd', 'linux', 'bash', 'ansible', 'devops', 'cloud', 'infrastructure'
}

CYBER_KEYWORD = {
    'cybersecurity', 'ethical hacking', 'penetration testing', 'network security',
    'firewall', 'siem', 'nmap', 'burp suite', 'kali linux', 'cryptography',
    'vulnerability assessment'
}

QA_KEYWORD = {
    'manual testing', 'automation testing', 'selenium', 'cypress', 'postman',
    'api testing', 'jira', 'test cases', 'bug tracking', 'pytest', 'quality assurance'
}

BA_KEYWORD = {
    'business analysis', 'requirement gathering', 'documentation', 'excel',
    'communication', 'agile', 'scrum', 'jira', 'project management', 'stakeholder'
}

DBA_KEYWORD = {
    'sql', 'pl/sql', 'oracle', 'mysql', 'postgresql', 'database', 'normalization',
    'backup', 'recovery', 'performance tuning', 'rds'
}

AI_NLP_KEYWORD = {
    'nlp', 'transformers', 'huggingface', 'bert', 'gpt', 'text classification',
    'chatbot', 'speech recognition', 'language model', 'ai', 'deep learning'
}

PRODUCT_MANAGER_KEYWORD = {
    'product management', 'roadmap', 'market research', 'communication',
    'analytics', 'data-driven', 'leadership', 'jira', 'notion', 'scrum'
}

# ---------------- COMBINED JOB KEYWORDS ----------------
JOB_KEYWORDS = {
    'Data Science': DS_KEYWORD,
    'Web Development': WEB_KEYWORD,
    'Android Development': ANDROID_KEYWORD,
    'iOS Development': IOS_KEYWORD,
    'UI/UX Design': UIUX_KEYWORD,
    'Data Analyst': DATA_ANALYST_KEYWORD,
    'Cloud & DevOps': CLOUD_DEVOPS_KEYWORD,
    'Cybersecurity': CYBER_KEYWORD,
    'Quality Assurance': QA_KEYWORD,
    'Business Analyst': BA_KEYWORD,
    'Database Administrator': DBA_KEYWORD,
    'AI / NLP Engineer': AI_NLP_KEYWORD,
    'Product Manager': PRODUCT_MANAGER_KEYWORD
}


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

    # ---------- SECURITY CHECK ----------
    # Candidate: can ONLY view their own resume
    if session.get('role') == 'candidate' and resume.user_id != session.get('user_id'):
        flash("You do not have permission to view this resume.", "danger")
        return redirect(url_for('candidate_dashboard'))

    # Admin: can view any resume — NO restriction needed

    # ---------- FETCH RESUME OWNER ----------
    candidate = User.query.get(resume.user_id)

        # ---------- EXTRACT NAME FROM RESUME ----------
    def extract_candidate_name(text):
        lines = text.strip().split("\n")

        # check top lines for full name
        for line in lines[:7]:
            clean = line.strip()

            # skip long or empty lines
            if not clean or len(clean.split()) > 4:
                continue

            # If all words are alphabetic → likely a name
            if all(w.replace(".", "").isalpha() for w in clean.split()):
                return clean

        return None

    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], resume.file_name)
        text = extract_text(filepath)

        extracted_name = extract_candidate_name(text)

        # 🔥 SAVE EXTRACTED NAME TO DATABASE
        if extracted_name:
            resume.candidate_name = extracted_name
        else:
            resume.candidate_name = candidate.name if candidate else "Unknown"

        db.session.commit()   # SAVE NAME

    except Exception as e:
        print("Name extraction error:", e)
        resume.candidate_name = candidate.name if candidate else "Unknown"
        db.session.commit()

    try:
        # -------- Extract Resume Text -------- #
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], resume.file_name)
        text = extract_text(filepath)
        analysis = analyze_resume(text)

        rt_lower = text.lower()

        # -------- Candidate Level -------- #
        cand_level = "Fresher"
        if "internship" in rt_lower:
            cand_level = "Intermediate"
        elif "experience" in rt_lower:
            cand_level = "Experienced"

        # -------- Extract Skills Found -------- #
        skills_list = analysis.get("skills_found", [])

        # ----------------------------------------------------
        # 🔥 FINAL ROLE PREDICTION — ONLY BEST MATCHING ROLE
        # ----------------------------------------------------
        role_scores = {}
        for role, keywords in JOB_KEYWORDS.items():
            score = sum(1 for skill in skills_list if skill.lower() in keywords)
            role_scores[role] = score

        predicted_role = max(role_scores, key=role_scores.get) if max(role_scores.values()) > 0 else None

        # ----------------------------------------------------
        # ROLE DATA — Courses + Skills (ALL ROLES)
        # ----------------------------------------------------
        ROLE_DATA = {

            "Data Science": {
                "skills": ['Pandas', 'NumPy', 'Matplotlib', 'Flask', 'Streamlit'],
                "courses": [
                    ("Machine Learning Crash Course (Google)", "https://developers.google.com/machine-learning/crash-course"),
                    ("Deep Learning Specialization", "https://www.coursera.org/specializations/deep-learning"),
                    ("Python for Data Science", "https://www.coursera.org/learn/python-for-data-science"),
                    ("Data Scientist with Python", "https://www.datacamp.com/tracks/data-scientist-with-python"),
                    ("Applied Data Science Specialization", "https://www.coursera.org/specializations/applied-data-science")
                ]
            },

            "Web Development": {
                "skills": ['React', 'Node.js', 'Django', 'Flask', 'MySQL'],
                "courses": [
                    ("Web Developer Bootcamp", "https://www.udemy.com/course/the-complete-web-developer-course-2/"),
                    ("JavaScript Algorithms (freeCodeCamp)", "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/"),
                    ("React Frontend Course", "https://www.coursera.org/learn/react"),
                    ("Django for Beginners", "https://www.udemy.com/course/django-for-beginners/"),
                    ("Full Stack Open", "https://fullstackopen.com/en/")
                ]
            },

            "Android Development": {
                "skills": ['Kotlin', 'Flutter', 'XML', 'SQLite', 'Firebase'],
                "courses": [
                    ("Android App Development (Google)", "https://developer.android.com/courses"),
                    ("Flutter Bootcamp", "https://www.udemy.com/course/flutter-bootcamp-with-dart/"),
                    ("Android for Beginners", "https://youtu.be/fis26HvvDII"),
                    ("Kotlin for Android", "https://www.coursera.org/learn/kotlin-for-java-developers"),
                    ("Flutter Specialization", "https://www.coursera.org/specializations/app-development-with-flutter")
                ]
            },

            "iOS Development": {
                "skills": ['Swift', 'Xcode', 'UIKit', 'Core Data', 'SwiftUI'],
                "courses": [
                    ("iOS App Development Bootcamp", "https://www.udemy.com/course/ios-13-app-development-bootcamp/"),
                    ("SwiftUI Essentials", "https://developer.apple.com/tutorials/swiftui"),
                    ("iOS Basics", "https://www.coursera.org/learn/ios-app-development-basics"),
                    ("Swift Developer Program", "https://www.edx.org/professional-certificate/curtinx-mobile-app-development-with-swift"),
                    ("Swift Programming", "https://www.codecademy.com/learn/learn-swift")
                ]
            },

            "UI/UX Design": {
                "skills": ['Figma', 'Adobe XD', 'Prototyping', 'Wireframes', 'Usability Testing'],
                "courses": [
                    ("Google UX Design Certificate", "https://www.coursera.org/professional-certificates/google-ux-design"),
                    ("UI/UX Design Essentials", "https://www.udemy.com/course/ui-ux-web-design-using-adobe-xd/"),
                    ("Design Thinking Course", "https://www.coursera.org/learn/uva-darden-design-thinking-innovation"),
                    ("Figma for UX", "https://www.linkedin.com/learning/figma-for-ux-design"),
                    ("UX Fundamentals (Skillshare)", "https://www.skillshare.com/en/classes/user-experience-design-fundamentals/87920879")
                ]
            },

            "Data Analyst": {
                "skills": ['Excel', 'Power BI', 'SQL', 'Pandas', 'Visualization'],
                "courses": [
                    ("Google Data Analytics Certificate", "https://www.coursera.org/professional-certificates/google-data-analytics"),
                    ("Data Analyst with Python", "https://www.datacamp.com/tracks/data-analyst-with-python"),
                    ("Excel to MySQL", "https://www.coursera.org/specializations/excel-mysql"),
                    ("Tableau Beginner Course", "https://www.udemy.com/course/tableau10/"),
                    ("Power BI Fundamentals", "https://learn.microsoft.com/en-us/training/paths/get-started-power-bi/")
                ]
            },

            "Cloud & DevOps": {
                "skills": ['AWS', 'Docker', 'Kubernetes', 'Terraform', 'CI/CD'],
                "courses": [
                    ("AWS Cloud Practitioner", "https://www.aws.training/Details/eLearning?id=60697"),
                    ("Docker & Kubernetes", "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/"),
                    ("DevOps Foundations", "https://www.linkedin.com/learning/devops-foundations"),
                    ("Azure DevOps Training", "https://learn.microsoft.com/en-us/training/modules/intro-to-azure-devops/"),
                    ("Terraform Beginner Track", "https://learn.hashicorp.com/collections/terraform/aws-get-started")
                ]
            },

            "Cybersecurity": {
                "skills": ['Network Security', 'Ethical Hacking', 'SIEM', 'Firewalls', 'Vulnerability Assessment'],
                "courses": [
                    ("Cybersecurity Fundamentals", "https://www.coursera.org/specializations/ibm-cybersecurity-analyst"),
                    ("Certified Ethical Hacker", "https://www.eccouncil.org/train-certify/certified-ethical-hacker-ceh/"),
                    ("Intro to Cybersecurity (Cisco)", "https://www.netacad.com/courses/cybersecurity/introduction-cybersecurity"),
                    ("Network Security Basics", "https://www.udemy.com/course/network-security-fundamentals/"),
                    ("Google Cybersecurity Certificate", "https://www.coursera.org/professional-certificates/google-cybersecurity")
                ]
            },

            "Quality Assurance": {
                "skills": ['Manual Testing', 'Automation', 'Selenium', 'Postman', 'Bug Tracking'],
                "courses": [
                    ("Software Testing Fundamentals", "https://www.coursera.org/learn/software-testing"),
                    ("Selenium with Python", "https://www.udemy.com/course/selenium-webdriver-with-python/"),
                    ("Postman API Testing", "https://www.udemy.com/course/postman-the-complete-guide/"),
                    ("Test Automation University", "https://testautomationu.applitools.com/"),
                    ("Agile Testing Foundations", "https://www.linkedin.com/learning/agile-testing-foundations")
                ]
            },

            "Business Analyst": {
                "skills": ['Excel', 'Agile', 'Documentation', 'JIRA', 'Communication'],
                "courses": [
                    ("Business Analysis Fundamentals", "https://www.udemy.com/course/business-analysis-fundamentals/"),
                    ("Agile Business Analyst", "https://www.coursera.org/learn/agile-business-analyst"),
                    ("Excel for Business", "https://www.coursera.org/specializations/excel"),
                    ("Project Management Foundations", "https://www.linkedin.com/learning/project-management-foundations"),
                    ("Business Analytics Specialization", "https://www.coursera.org/specializations/business-analytics")
                ]
            },

            "Database Administrator": {
                "skills": ['SQL', 'Backup', 'Performance Tuning', 'PostgreSQL', 'Oracle'],
                "courses": [
                    ("Oracle SQL Admin", "https://www.udemy.com/course/oracle-sql-database-administration/"),
                    ("PostgreSQL Specialization", "https://www.coursera.org/specializations/postgresql-for-everybody"),
                    ("Database Management Essentials", "https://www.coursera.org/learn/database-management"),
                    ("SQL Server Essentials", "https://www.linkedin.com/learning/sql-server-essential-training"),
                    ("MySQL for Data Analytics", "https://www.udemy.com/course/mysql-for-data-analytics-and-business-intelligence/")
                ]
            },

            "AI / NLP Engineer": {
                "skills": ['NLP', 'Transformers', 'Hugging Face', 'BERT', 'GPT'],
                "courses": [
                    ("NLP (Coursera)", "https://www.coursera.org/learn/language-processing"),
                    ("Hugging Face NLP Course", "https://huggingface.co/learn/nlp-course"),
                    ("Deep Learning for NLP", "https://www.udemy.com/course/nlp-natural-language-processing-with-python/"),
                    ("Applied Text Mining", "https://www.coursera.org/learn/python-text-mining"),
                    ("Transformers & BERT Video", "https://youtu.be/kCc8FmEb1nY")
                ]
            },

            "Product Manager": {
                "skills": ['Leadership', 'Agile', 'Market Research', 'Analytics', 'Roadmapping'],
                "courses": [
                    ("Digital Product Management", "https://www.coursera.org/learn/uva-darden-digital-product-management"),
                    ("Product Management 101", "https://www.udemy.com/course/product-management-101/"),
                    ("Agile Product Owner Role", "https://www.linkedin.com/learning/agile-product-owner-role"),
                    ("Product Strategy (Northwestern)", "https://www.coursera.org/learn/product-strategy"),
                    ("Business Strategy (edX)", "https://www.edx.org/course/business-strategy")
                ]
            }
        }

        # -------- Build Recommendations -------- #
        recommended_skills = []
        courses = []

        if predicted_role in ROLE_DATA:
            recommended_skills = ROLE_DATA[predicted_role]["skills"]
            courses = [{"name": n, "link": l} for n, l in ROLE_DATA[predicted_role]["courses"]]

        # ----------------------------------------------------
        # RESUME SCORING
        # ----------------------------------------------------
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

        resume_score = 0
        tips = []

        for key, (words, points) in sections.items():
            if any(w in rt_lower for w in words):
                resume_score += points
                tips.append(f"[+] Great! You included your {key} section.")
            else:
                tips.append(f"[-] Please add your {key} section to improve your resume.")

        resume_score = min(resume_score, 100)

        # ----------------------------------------------------
        # UPDATE DATABASE
        # ----------------------------------------------------
        resume.predicted_role = predicted_role
        resume.resume_score = resume_score
        resume.tips = "\n".join(tips)
        resume.recommended_skills = ", ".join(recommended_skills)
        resume.courses = json.dumps([c["name"] for c in courses])
        resume.course_links = json.dumps([c["link"] for c in courses])

        db.session.commit()

        
        resume.candidate_level = cand_level

    except Exception as e:
        traceback.print_exc()
        flash(f"Error analyzing resume: {str(e)}", "danger")

    # -------- Load Courses from DB -------- #
    courses = []
    if resume.courses and resume.course_links:
        try:
            names = json.loads(resume.courses)
            links = json.loads(resume.course_links)
            courses = [{"name": n, "link": l} for n, l in zip(names, links)]
        except:
            pass

    # -------- Load Recommended Skills -------- #
    recommended_skills = []
    if resume.recommended_skills:
        recommended_skills = [s.strip() for s in resume.recommended_skills.split(",")]

    tips = resume.tips.split("\n") if resume.tips else []

    # -------- Roadmap -------- #
    roadmap = ROADMAPS.get(resume.predicted_role)

    # -------- Render Template -------- #
    return render_template(
        "view_resume.html",
        resume={
            "id": resume.id,
            "candidate_name": resume.candidate_name,
            "candidate_level": resume.candidate_level,
            "parsed_text": getattr(resume, "parsed_text", ""),
            "skills": getattr(resume, "skills", ""),
            "predicted_role": resume.predicted_role,
            "recommended_skills": recommended_skills,
            "tips": tips,
            "score": resume.resume_score,
            "courses": courses,
            "roadmap": roadmap
        }
    )



@app.route('/download_resume_pdf/<int:resume_id>')
def download_resume_pdf(resume_id):
    resume = Resume.query.get_or_404(resume_id)

    # Create an in-memory PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=40,
        bottomMargin=40
    )
    styles = getSampleStyleSheet()
    content = []

    # ------------------- CANDIDATE NAME (Extracted or fallback) -------------------
    candidate_name = resume.candidate_name or "Unknown"


    # ------------------- UPDATED TITLE -------------------
    title_style = styles['Title']
    title_style.alignment = TA_CENTER
    content.append(Paragraph(f"{candidate_name} - Resume Analysis Report", title_style))
    content.append(Spacer(1, 0.2 * inch))

    # ------------------- ONLY SHOW CANDIDATE NAME -------------------
    info_style = ParagraphStyle('info', parent=styles["Normal"], spaceAfter=3)
    content.append(Paragraph(f"<b>Candidate Name:</b> {candidate_name}", info_style))
    content.append(Spacer(1, 0.15 * inch))

    # ------------------- ANALYSIS SUMMARY -------------------
    content.append(Paragraph("<b>Analysis Summary:</b>", styles["Heading3"]))
    summary_text = resume.parsed_text or "No summary available."
    content.append(Paragraph(summary_text, styles["Normal"]))
    content.append(Spacer(1, 0.15 * inch))

    # ------------------- CURRENT SKILLS -------------------
    content.append(Paragraph("<b>Current Skills:</b>", styles["Heading3"]))
    if resume.skills:
        if isinstance(resume.skills, str):
            skills_text = resume.skills
        else:
            skills_text = ", ".join(json.loads(resume.skills))
        content.append(Paragraph(skills_text, styles["Normal"]))
    else:
        content.append(Paragraph("No skills found.", styles["Normal"]))
    content.append(Spacer(1, 0.15 * inch))

    # ------------------- PREDICTED ROLE -------------------
    content.append(Paragraph("<b>Predicted Job Role:</b>", styles["Heading3"]))
    content.append(Paragraph(resume.predicted_role or "Not available.", styles["Normal"]))
    content.append(Spacer(1, 0.15 * inch))

    # ------------------- RECOMMENDED SKILLS -------------------
    content.append(Paragraph("<b>Recommended Skills:</b>", styles["Heading3"]))
    if resume.recommended_skills:
        if isinstance(resume.recommended_skills, str):
            recommended_skills = [s.strip() for s in resume.recommended_skills.split(",")]
        else:
            recommended_skills = resume.recommended_skills
        for skill in recommended_skills:
            content.append(Paragraph(f"• {skill}", styles["Normal"]))
    else:
        content.append(Paragraph("No recommendations available.", styles["Normal"]))
    content.append(Spacer(1, 0.15 * inch))

    # ------------------- COURSES -------------------
    content.append(Paragraph("<b>Courses & Certifications:</b>", styles["Heading3"]))
    if resume.courses:
        try:
            course_names = json.loads(resume.courses)
            course_links = json.loads(resume.course_links or "[]")
            for name, link in zip(course_names, course_links):
                content.append(Paragraph(f"• <a href='{link}'>{name}</a>", styles["Normal"]))
        except:
            content.append(Paragraph(resume.courses, styles["Normal"]))
    else:
        content.append(Paragraph("No course recommendations available.", styles["Normal"]))
    content.append(Spacer(1, 0.2 * inch))

    # ------------------- ROADMAP IMAGE (IF AVAILABLE) -------------------
    if resume.predicted_role and resume.predicted_role in ROADMAPS:
        roadmap_info = ROADMAPS[resume.predicted_role]
        roadmap_title = roadmap_info.get('title', '')
        roadmap_image = roadmap_info.get('image', '')

        if roadmap_image and os.path.exists(roadmap_image):
            try:
                roadmap_title_style = ParagraphStyle(
                    'roadmap_title',
                    parent=styles["Heading3"],
                    alignment=TA_CENTER,
                    spaceAfter=6,
                    fontSize=12,
                    textColor=colors.HexColor('#0d47a1')
                )
                content.append(Paragraph(roadmap_title, roadmap_title_style))
                content.append(Spacer(1, 0.1 * inch))

                img = RLImage(roadmap_image)
                max_width = 5.6 * inch
                if img.drawWidth > max_width:
                    scale = max_width / float(img.drawWidth)
                    img.drawWidth *= scale
                    img.drawHeight *= scale

                img.hAlign = 'CENTER'
                content.append(img)
                content.append(Spacer(1, 0.15 * inch))
            except:
                content.append(Paragraph("⚠️ Roadmap image error", styles["Normal"]))
        else:
            content.append(Paragraph("Roadmap image not found.", styles["Normal"]))
    else:
        content.append(Paragraph("No roadmap available for this role.", styles["Normal"]))

    content.append(Spacer(1, 0.15 * inch))

    # ------------------- TIPS -------------------
    content.append(Paragraph("<b>Resume Tips:</b>", styles["Heading3"]))
    if resume.tips:
        tips_list = [t.strip() for t in resume.tips.split("\n")]
        for tip in tips_list:
            color = "green" if tip.startswith("[+]") else "red"
            content.append(Paragraph(f'<font color="{color}">{tip}</font>', styles["Normal"]))
    else:
        content.append(Paragraph("No tips available.", styles["Normal"]))
    content.append(Spacer(1, 0.15 * inch))

    # ------------------- SCORE -------------------
    content.append(Paragraph("<b>Overall Resume Score:</b>", styles["Heading3"]))
    content.append(Paragraph(f"<b>{resume.resume_score or 'N/A'} / 100</b>", styles["Normal"]))

    # ------------------- FOOTER -------------------
    footer_style = ParagraphStyle(
        'footer',
        parent=styles["Normal"],
        alignment=TA_CENTER,
        textColor=colors.grey,
        fontSize=8,
        spaceBefore=15
    )

    content.append(Spacer(1, 0.1 * inch))
    content.append(Paragraph("Generated by AI Resume Analyzer", footer_style))

    doc.build(content)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{candidate_name.replace(' ', '_')}_Resume_Analysis.pdf",
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
        {"name": "Data Analyst", "image": "roadmaps/data_analyst_roadmap.png"},
        {"name": "Cloud & DevOps", "image": "roadmaps/cloud_devops_roadmap.png"},
        {"name": "Cybersecurity", "image": "roadmaps/cybersecurity_roadmap.png"},
        {"name": "Quality Assurance", "image": "roadmaps/quality_assurance_roadmap.png"},
        {"name": "Business Analyst", "image": "roadmaps/business_analyst_roadmap.png"},
        {"name": "Database Administrator", "image": "roadmaps/database_administrator_roadmap.png"},
        {"name": "AI / NLP Engineer", "image": "roadmaps/ai___nlp_engineer_roadmap.png"},
        {"name": "Product Manager", "image": "roadmaps/product_manager_roadmap.png"}
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