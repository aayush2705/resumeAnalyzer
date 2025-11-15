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
from modules.parser import extract_text_bytes
import re


app = Flask(__name__)

from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev_key")
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

bcrypt = Bcrypt(app)

# ---------------- ROADMAP DATA ----------------
ROADMAPS = {

    # ================= OLD ROLES =====================

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
        'image': 'static/roadmaps/cloud___devops_roadmap.png'
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
        'image': 'static/roadmaps/quality_assurance_roadmap.png'
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
        'image': 'static/roadmaps/database_administrator_roadmap.png'
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
        'image': 'static/roadmaps/ai__nlp_engineer_roadmap.png'
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
    },

    # ================= NEW ROLES =====================

    'Python Developer': {
        'title': 'Python Developer Roadmap',
        'steps': [
            'Learn Core Python and OOP',
            'Master Django or Flask Frameworks',
            'Work with REST APIs and Databases',
            'Learn Testing and Deployment',
            'Build Real-World Python Applications'
        ],
        'image': 'static/roadmaps/python_developer_roadmap.png'
    },

    'Java Developer': {
        'title': 'Java Developer Roadmap',
        'steps': [
            'Master Core Java and OOP',
            'Learn Spring and Spring Boot',
            'Work with Hibernate and Microservices',
            'Build Secure REST APIs',
            'Deploy Java Applications to Cloud'
        ],
        'image': 'static/roadmaps/java_developer_roadmap.png'
    },

    'C/C++ Developer': {
        'title': 'C/C++ Developer Roadmap',
        'steps': [
            'Learn C/C++ Fundamentals',
            'Master Memory Management and Pointers',
            'Understand STL and OOP Concepts',
            'Practice Linux & OS-Level Programming',
            'Build High-Performance Applications'
        ],
        'image': 'static/roadmaps/c_c___developer_roadmap.png'
    },

    '.NET Developer': {
        'title': '.NET Developer Roadmap',
        'steps': [
            'Learn C# and .NET Basics',
            'Master ASP.NET Core and MVC',
            'Work with Entity Framework and LINQ',
            'Build REST APIs with .NET',
            'Deploy .NET Applications to Cloud'
        ],
        'image': 'static/roadmaps/_net_developer_roadmap.png'
    },

    'PHP Developer': {
        'title': 'PHP Developer Roadmap',
        'steps': [
            'Learn Core PHP and OOP',
            'Master Laravel Framework',
            'Work with MySQL and REST APIs',
            'Learn Authentication & Security',
            'Deploy Scalable PHP Applications'
        ],
        'image': 'static/roadmaps/php_developer_roadmap.png'
    },

    'JavaScript Developer': {
        'title': 'JavaScript Developer Roadmap',
        'steps': [
            'Master Core JavaScript and DOM',
            'Understand Async JS and Event Loop',
            'Learn TypeScript and ES6+ Features',
            'Build Real Projects with JavaScript',
            'Deploy JS Applications'
        ],
        'image': 'static/roadmaps/javascript_developer_roadmap.png'
    },

    'Full Stack Developer': {
        'title': 'Full Stack Developer Roadmap',
        'steps': [
            'Learn Frontend (HTML, CSS, JS, React)',
            'Master Backend (Node.js, Django, PHP)',
            'Understand Databases (SQL/NoSQL)',
            'Learn Git, API Design, Testing',
            'Deploy Full Stack Applications'
        ],
        'image': 'static/roadmaps/full_stack_developer_roadmap.png'
    },

    'Backend Developer': {
        'title': 'Backend Developer Roadmap',
        'steps': [
            'Learn Server-Side Languages',
            'Build REST APIs and Microservices',
            'Use Databases (SQL + NoSQL)',
            'Master Authentication & Caching',
            'Deploy and Scale Backend Systems'
        ],
        'image': 'static/roadmaps/backend_developer_roadmap.png'
    },

    'Frontend Developer': {
        'title': 'Frontend Developer Roadmap',
        'steps': [
            'Master HTML, CSS, JavaScript',
            'Learn React, Vue, or Angular',
            'Build Responsive UI with Tailwind',
            'Understand Web Performance & Accessibility',
            'Deploy Frontend Apps'
        ],
        'image': 'static/roadmaps/frontend_developer_roadmap.png'
    }
}


# ---------------- APP SETUP ---------------- #


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

    courses_data = {

# ================================================================
# OLD ROLES (10 COURSES EACH)
# ================================================================

'Data Science': [
    ['Machine Learning Crash Course – Google (FREE)', 'https://developers.google.com/machine-learning/crash-course'],
    ['Machine Learning – Andrew Ng', 'https://www.coursera.org/learn/machine-learning'],
    ['Data Science Roadmap – freeCodeCamp (FREE)', 'https://youtu.be/X3paOmcrTjQ'],
    ['Deep Learning Specialization – Andrew Ng', 'https://www.coursera.org/specializations/deep-learning'],
    ['Python for Data Science – Coursera', 'https://www.coursera.org/learn/python-for-data-science'],
    ['Data Scientist with Python – DataCamp', 'https://www.datacamp.com/tracks/data-scientist-with-python'],
    ['Data Science Bootcamp – Udemy', 'https://www.udemy.com/course/data-science-and-machine-learning-bootcamp-with-python/'],
    ['Statistics for Data Science – Udemy', 'https://www.udemy.com/course/statistics-for-data-science-and-business-analysis/'],
    ['Intro to Machine Learning – Kaggle (FREE)', 'https://www.kaggle.com/learn/intro-to-machine-learning'],
    ['AI for Everyone – Andrew Ng', 'https://www.coursera.org/learn/ai-for-everyone']
],

'Web Development': [
    ['The Odin Project (FREE Full Stack)', 'https://www.theodinproject.com'],
    ['HTML & CSS Crash Course – freeCodeCamp (FREE)', 'https://www.freecodecamp.org/learn/responsive-web-design/'],
    ['JavaScript Full Course – freeCodeCamp (FREE)', 'https://youtu.be/jS4aFq5-91M'],
    ['React – Codecademy', 'https://www.codecademy.com/learn/react-101'],
    ['Node.js Crash Course – freeCodeCamp (FREE)', 'https://youtu.be/Oe421EPjeBE'],
    ['Full Stack Web Dev – Udacity', 'https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd0044'],
    ['Django for Everyone – Coursera', 'https://www.coursera.org/specializations/django'],
    ['Complete Web Dev Bootcamp – Udemy', 'https://www.udemy.com/course/the-complete-web-development-bootcamp/'],
    ['Next.js Full Tutorial – freeCodeCamp (FREE)', 'https://youtu.be/Y6KDk5iyrYE'],
    ['Frontend Developer Roadmap – Roadmap.sh (FREE)', 'https://roadmap.sh/frontend']
],

'Android Development': [
    ['Android Basics by Google (FREE)', 'https://www.udacity.com/course/android-basics--nd803'],
    ['Android Kotlin Developer – Udacity', 'https://www.udacity.com/course/android-kotlin-developer-nanodegree--nd940'],
    ['Android Studio Masterclass – Udemy', 'https://www.udemy.com/course/android-oreo-kotlin-app-masterclass/'],
    ['Kotlin Bootcamp – Google (FREE)', 'https://developer.android.com/courses/android-basics-kotlin/course'],
    ['Flutter Full Course – freeCodeCamp (FREE)', 'https://youtu.be/VPvVD8t02U8'],
    ['Jetpack Compose Tutorial – Google', 'https://developer.android.com/jetpack/compose'],
    ['Android App Development Specialization – Coursera', 'https://www.coursera.org/specializations/android-app-development'],
    ['Flutter & Dart Bootcamp – Udemy', 'https://www.udemy.com/course/flutter-dart-the-complete-flutter-app-development-course/'],
    ['Kotlin Essentials – JetBrains (FREE)', 'https://play.kotlinlang.org/koans/overview'],
    ['Android Clean Architecture Course', 'https://youtu.be/EOfCEhWq8sg']
],

'iOS Development': [
    ['Swift Full Course – freeCodeCamp (FREE)', 'https://youtu.be/comQ1-x2a1Q'],
    ['SwiftUI Essentials – Apple', 'https://developer.apple.com/tutorials/swiftui'],
    ['iOS & Swift Bootcamp – Udemy', 'https://www.udemy.com/course/ios-13-app-development-bootcamp/'],
    ['Become an iOS Developer – Udacity', 'https://www.udacity.com/course/ios-developer-nanodegree--nd003'],
    ['Swift Programming – Codecademy', 'https://www.codecademy.com/learn/learn-swift'],
    ['Swift Specialization – Coursera', 'https://www.coursera.org/specializations/app-development'],
    ['Objective-C Crash Course – Udemy', 'https://www.udemy.com/course/objectivec/'],
    ['iOS App Architecture – Udemy', 'https://www.udemy.com/course/ios-architecture/'],
    ['SwiftUI Masterclass', 'https://www.udemy.com/course/swiftui-masterclass-course-ios-development-with-swift/'],
    ['Intro to iOS App Development – LinkedIn', 'https://www.linkedin.com/learning/topics/ios']
],

'UI/UX Design': [
    ['Google UX Design Certificate', 'https://www.coursera.org/professional-certificates/google-ux-design'],
    ['Figma Full Course – FreeCodeCamp (FREE)', 'https://youtu.be/jwCt4DCa2Ek'],
    ['UI/UX Specialization – Coursera', 'https://www.coursera.org/specializations/ui-ux-design'],
    ['Adobe XD Full Course – Free (YouTube)', 'https://youtu.be/68w2VwalD5w'],
    ['UX Design for Beginners – Udemy', 'https://www.udemy.com/course/ux-design-fundamentals/'],
    ['Design Thinking – Coursera', 'https://www.coursera.org/learn/uva-darden-design-thinking-innovation'],
    ['UI Design Principles – Udemy', 'https://www.udemy.com/course/design-rules/'],
    ['UX Research at Scale – Coursera', 'https://www.coursera.org/learn/ux-research-at-scale'],
    ['Interaction Design Foundation Courses', 'https://www.interaction-design.org/courses'],
    ['Become a UX Designer – Udacity', 'https://www.udacity.com/course/ux-designer-nanodegree--nd578']
],

'Data Analyst': [
    ['Google Data Analytics Certificate', 'https://www.coursera.org/professional-certificates/google-data-analytics'],
    ['Excel to MySQL – Coursera', 'https://www.coursera.org/specializations/excel-mysql'],
    ['Data Analyst with Python – DataCamp', 'https://www.datacamp.com/tracks/data-analyst-with-python'],
    ['Power BI Full Course – freeCodeCamp (FREE)', 'https://youtu.be/0tAzpi3fXw4'],
    ['Tableau Training – Udemy', 'https://www.udemy.com/course/tableau10/'],
    ['Statistics for Data Analysis – Udemy', 'https://www.udemy.com/course/statistics-for-data-science-and-business-analysis/'],
    ['Pandas Tutorial – freeCodeCamp (FREE)', 'https://youtu.be/vmEHCJofslg'],
    ['SQL for Data Analysis – Coursera', 'https://www.coursera.org/specializations/data-analysis-sql'],
    ['Excel Essential Training – LinkedIn', 'https://www.linkedin.com/learning/excel-essential-training-2019'],
    ['Data Analytics Bootcamp – Udemy', 'https://www.udemy.com/course/data-analytics-real-world-projects/']
],

'Cloud & DevOps': [
    ['AWS Cloud Practitioner (FREE)', 'https://www.aws.training/Details/eLearning?id=60697'],
    ['Docker + Kubernetes – Udemy', 'https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/'],
    ['Terraform for Beginners', 'https://learn.hashicorp.com/collections/terraform/aws-get-started'],
    ['Azure DevOps Tutorial – Microsoft', 'https://learn.microsoft.com/en-us/training/modules/introduction-to-devops/'],
    ['DevOps Foundations – LinkedIn', 'https://www.linkedin.com/learning/devops-foundations'],
    ['Linux Administration – Udemy', 'https://www.udemy.com/course/linux-admin-bootcamp/'],
    ['GCP Associate Cloud Engineer – Coursera', 'https://www.coursera.org/professional-certificates/gcp-cloud-engineering'],
    ['Kubernetes Bootcamp – FreeCodeCamp (FREE)', 'https://youtu.be/X48VuDVv0do'],
    ['Jenkins Full Course – Udemy', 'https://www.udemy.com/course/jenkins-from-zero-to-hero/'],
    ['Ansible for Beginners – Udemy', 'https://www.udemy.com/course/ansible-for-the-absolute-beginner/']
],

'Cybersecurity': [
    ['Intro to Cybersecurity – Cisco', 'https://www.netacad.com/courses/cybersecurity/introduction-cybersecurity'],
    ['Google Cybersecurity Certificate', 'https://www.coursera.org/professional-certificates/google-cybersecurity'],
    ['Ethical Hacking – CEH Prep', 'https://www.eccouncil.org/train-certify/certified-ethical-hacker-ceh/'],
    ['Cybersecurity Full Course – FreeCodeCamp (FREE)', 'https://youtu.be/3Kq1MIfTWCE'],
    ['Kali Linux Beginner Course', 'https://www.udemy.com/course/ethical-hacking-beginners/'],
    ['Network Security – LinkedIn', 'https://www.linkedin.com/learning/topics/network-security'],
    ['Burp Suite Course – Udemy', 'https://www.udemy.com/course/burp-suite-mastering-bug-bounty/'],
    ['Pentesting with Nmap – Udemy', 'https://www.udemy.com/course/nmap-complete-guide/'],
    ['Intro to Cryptography – Coursera', 'https://www.coursera.org/learn/cryptography'],
    ['Malware Analysis – Udemy', 'https://www.udemy.com/course/malware-analysis/']
],

'Quality Assurance': [
    ['Manual Testing Complete Course – Udemy', 'https://www.udemy.com/course/manual-testing-with-tutorial/'],
    ['Selenium with Python – Udemy', 'https://www.udemy.com/course/selenium-webdriver-with-python/'],
    ['Cypress Automation Course – Udemy', 'https://www.udemy.com/course/cypress-tutorial/'],
    ['API Testing with Postman – Udemy', 'https://www.udemy.com/course/postman-the-complete-guide/'],
    ['QA Testing Full Course – freeCodeCamp (FREE)', 'https://youtu.be/XkW6OVv1kwA'],
    ['JIRA Crash Course – LinkedIn', 'https://www.linkedin.com/learning/jira-service-management'],
    ['Automation Testing Bootcamp – Coursera', 'https://www.coursera.org/specializations/automated-software-testing'],
    ['Unit Testing in Python – Udemy', 'https://www.udemy.com/course/python-unit-testing-automation/'],
    ['Test Automation University (FREE)', 'https://testautomationu.applitools.com/'],
    ['Bug Tracking & Reporting Course', 'https://www.udemy.com/course/bug-reporting/']
],

'Business Analyst': [
    ['BA Fundamentals – Udemy', 'https://www.udemy.com/course/business-analysis-fundamentals/'],
    ['Agile Business Analysis – Coursera', 'https://www.coursera.org/learn/agile-business-analyst'],
    ['Business Analytics Specialization – Coursera', 'https://www.coursera.org/specializations/business-analytics'],
    ['Excel for Business Analysts – Coursera', 'https://www.coursera.org/learn/excel-data-analysis'],
    ['JIRA for Business Analysts – Udemy', 'https://www.udemy.com/course/jira-agile-project-management/'],
    ['Project Management Essentials – LinkedIn', 'https://www.linkedin.com/learning/project-management-foundations'],
    ['Requirement Engineering – Udemy', 'https://www.udemy.com/course/requirements-engineering/'],
    ['Business Communication – Coursera', 'https://www.coursera.org/specializations/business-communication'],
    ['Data Analytics for Business – Udemy', 'https://www.udemy.com/course/business-data-science/'],
    ['SDLC Complete Guide – Udemy', 'https://www.udemy.com/course/software-development-life-cycle/']
],

'Database Administrator': [
    ['PostgreSQL Masterclass – Udemy', 'https://www.udemy.com/course/postgresql-database-administration/'],
    ['SQL for Data Engineering – Coursera', 'https://www.coursera.org/learn/data-eng-sql'],
    ['MySQL Complete Course – freeCodeCamp (FREE)', 'https://youtu.be/7S_tz1z_5bA'],
    ['Oracle SQL Admin – Udemy', 'https://www.udemy.com/course/oracle-sql-database-administration/'],
    ['DBMS Full Course – Gate Smashers (FREE)', 'https://youtu.be/4xCynWHbn8w'],
    ['PL/SQL Bootcamp – Udemy', 'https://www.udemy.com/course/oracle-plsql-programming/'],
    ['Database Design Course – Coursera', 'https://www.coursera.org/learn/database-design'],
    ['SQL Server Training – LinkedIn', 'https://www.linkedin.com/learning/learning-sql-server'],
    ['Normalization & DB Design – Udemy', 'https://www.udemy.com/course/database-design-and-management/'],
    ['NoSQL Essentials – Coursera', 'https://www.coursera.org/learn/nosql-databases']
],

'AI / NLP Engineer': [
    ['NLP Specialization – Coursera', 'https://www.coursera.org/specializations/nlp'],
    ['HuggingFace Transformers Course (FREE)', 'https://huggingface.co/course/chapter1'],
    ['Deep Learning for NLP – Udemy', 'https://www.udemy.com/course/nlp-natural-language-processing-with-python/'],
    ['BERT & GPT Hands-on – Udemy', 'https://www.udemy.com/course/bert-transformers-nlp/'],
    ['Speech Recognition – Coursera', 'https://www.coursera.org/learn/audio-processing'],
    ['Intro to NLP – freeCodeCamp (FREE)', 'https://youtu.be/fNxaJsNG3-s'],
    ['Natural Language Processing – Stanford', 'http://web.stanford.edu/class/cs224n/'],
    ['Transformers in Python – YouTube', 'https://youtu.be/tiuPHWB1gkA'],
    ['AI for Everyone – Coursera', 'https://www.coursera.org/learn/ai-for-everyone'],
    ['Neural Networks – Coursera', 'https://www.coursera.org/learn/neural-networks-deep-learning']
],

'Product Manager': [
    ['Digital Product Management – Coursera', 'https://www.coursera.org/learn/uva-darden-digital-product-management'],
    ['Product Management 101 – Udemy', 'https://www.udemy.com/course/product-management-101/'],
    ['Agile Product Owner Role – LinkedIn', 'https://www.linkedin.com/learning/agile-product-owner-role'],
    ['Product Strategy – Coursera', 'https://www.coursera.org/learn/product-strategy'],
    ['Product Management Crash Course (FREE)', 'https://youtu.be/sJ14cWjrNzs'],
    ['Roadmapping for PMs – Udemy', 'https://www.udemy.com/course/product-roadmaps/'],
    ['Business Strategy – Coursera', 'https://www.coursera.org/specializations/business-strategy'],
    ['User Story Writing – Udemy', 'https://www.udemy.com/course/user-story/'],
    ['Notion for Productivity – YouTube', 'https://youtu.be/pvJScuVF4TU'],
    ['PM Interview Prep – Udemy', 'https://www.udemy.com/course/product-management-interview-crash-course/']
],


# ================================================================
# NEW ROLES (10 COURSES EACH)
# ================================================================

'Python Developer': [
    ['Python for Everybody – Coursera', 'https://www.coursera.org/specializations/python'],
    ['Automate the Boring Stuff (FREE)', 'https://automatetheboringstuff.com/'],
    ['Django Full Course – freeCodeCamp (FREE)', 'https://youtu.be/F5mRW0jo-U4'],
    ['FastAPI Full Course (FREE)', 'https://youtu.be/0sOvCWFmrtA'],
    ['Python OOP – Udemy', 'https://www.udemy.com/course/python-object-oriented-programming/'],
    ['Python Bootcamp – Udemy', 'https://www.udemy.com/course/complete-python-bootcamp/'],
    ['Flask Web Development – Udemy', 'https://www.udemy.com/course/python-and-flask-bootcamp/'],
    ['Data Structures in Python – Udemy', 'https://www.udemy.com/course/python-data-structures-and-algorithms/'],
    ['Asyncio in Python – YouTube', 'https://youtu.be/3mbFky5M6dM'],
    ['Build APIs with Django – Coursera', 'https://www.coursera.org/projects/django-rest-framework']
],

'Java Developer': [
    ['Java Programming Masterclass – Udemy', 'https://www.udemy.com/course/java-the-complete-java-developer-course/'],
    ['Java Full Course – freeCodeCamp (FREE)', 'https://youtu.be/A74TOX803D0'],
    ['Spring Boot Full Course – Amigoscode (FREE)', 'https://youtu.be/9SGDpanrc8U'],
    ['Hibernate Tutorial – Udemy', 'https://www.udemy.com/course/hibernate-course/'],
    ['Java OOP Mastery – Udemy', 'https://www.udemy.com/course/java-object-oriented-programming/'],
    ['Spring Security – Udemy', 'https://www.udemy.com/course/spring-security-core-beginner-to-guru/'],
    ['Java Servlets & JSP – Udemy', 'https://www.udemy.com/course/jsp-servlet-free-course/'],
    ['Microservices with Spring – Udemy', 'https://www.udemy.com/course/microservices-with-spring-boot/'],
    ['DSA in Java – Coding Ninjas', 'https://www.codingninjas.com/courses/data-structures-and-algorithms-java'],
    ['Java Multithreading – YouTube', 'https://youtu.be/h-T7XmyIHDE']
],

'C/C++ Developer': [
    ['C Programming Full Course – freeCodeCamp (FREE)', 'https://youtu.be/KJgsSFOSQv0'],
    ['C++ Full Course – freeCodeCamp (FREE)', 'https://youtu.be/8jLOx1hD3_o'],
    ['Mastering Data Structures in C++ – Udemy', 'https://www.udemy.com/course/datastructurescncpp/'],
    ['Advanced C++ – Udemy', 'https://www.udemy.com/course/advanced-c-programming/'],
    ['Linux System Programming – Udemy', 'https://www.udemy.com/course/linux-system-programming-techniques/'],
    ['Pointers in C – Udemy', 'https://www.udemy.com/course/c-pointers/'],
    ['Competitive Programming in C++ – Codeforces', 'https://codeforces.com/edu'],
    ['STL in C++ – YouTube', 'https://youtu.be/PwS4LlQ2kZQ'],
    ['Operating Systems – Neso Academy (FREE)', 'https://youtu.be/_TpOHMCODXo'],
    ['C++ OOP Course – Udemy', 'https://www.udemy.com/course/cpp-classes/']
],

'.NET Developer': [
    ['C# Basics Tutorial – freeCodeCamp (FREE)', 'https://youtu.be/GhQdlIFylQ8'],
    ['ASP.NET Core MVC Full Course – YouTube', 'https://youtu.be/BfEjDD8mWYg'],
    ['Entity Framework Core – Pluralsight', 'https://www.pluralsight.com/courses/entity-framework-core-getting-started'],
    ['C# Masterclass – Udemy', 'https://www.udemy.com/course/csharp-tutorial-for-beginners/'],
    ['.NET API Development – Udemy', 'https://www.udemy.com/course/build-restful-apis-with-aspnet-core/'],
    ['LINQ Tutorial – Microsoft', 'https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/concepts/linq/'],
    ['Microservices with .NET – Udemy', 'https://www.udemy.com/course/microservices-architecture-and-implementation-on-dotnet/'],
    ['Blazor WebAssembly Course', 'https://learn.microsoft.com/en-us/aspnet/core/blazor'],
    ['ASP.NET Razor Pages – Udemy', 'https://www.udemy.com/course/aspnet-core-razor-pages/'],
    ['Clean Architecture in .NET – YouTube', 'https://youtu.be/fJjKQla-PgM']
],

'PHP Developer': [
    ['PHP Full Course – freeCodeCamp (FREE)', 'https://youtu.be/OK_JCtrrv-c'],
    ['Laravel From Scratch – Laracasts', 'https://laracasts.com/series/laravel-8-from-scratch'],
    ['PHP with MySQL – Udemy', 'https://www.udemy.com/course/php-for-complete-beginners-includes-msql-object-oriented/'],
    ['Object-Oriented PHP – Udemy', 'https://www.udemy.com/course/php-oop-object-oriented-programming/'],
    ['Laravel REST API Course – YouTube', 'https://youtu.be/MT-GJQIY3EU'],
    ['PHP Security Crash Course', 'https://www.udemy.com/course/php-security/'],
    ['PHP MVC Framework Course', 'https://youtu.be/6ERdu4k62wI'],
    ['PHP Deployment – Udemy', 'https://www.udemy.com/course/deploy-php-app/'],
    ['MySQL Masterclass – Udemy', 'https://www.udemy.com/course/the-complete-sql-bootcamp/'],
    ['Laravel Livewire Course', 'https://laravel-livewire.com/docs/2.x/quickstart']
],

'JavaScript Developer': [
    ['JavaScript Full Course – freeCodeCamp (FREE)', 'https://youtu.be/HD13eq_Pmp8'],
    ['Async JavaScript Mastery – Udemy', 'https://www.udemy.com/course/asynchronous-javascript/'],
    ['JavaScript DOM Mastery – YouTube', 'https://youtu.be/0ik6X4DJKCc'],
    ['JavaScript Algorithms – freeCodeCamp (FREE)', 'https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/'],
    ['TypeScript Full Course – freeCodeCamp (FREE)', 'https://youtu.be/30LWjhZzg50'],
    ['Modern JavaScript Bootcamp – Udemy', 'https://www.udemy.com/course/javascript-beginners-complete-tutorial/'],
    ['JavaScript Design Patterns – Udemy', 'https://www.udemy.com/course/learn-javascript-design-patterns/'],
    ['ES6+ Modern JavaScript – Udemy', 'https://www.udemy.com/course/understand-javascript/'],
    ['Event Loop & Async Deep Dive – YouTube', 'https://youtu.be/8aGhZQkoFbQ'],
    ['Promises & Async/Await – MDN', 'https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous']
],

'Full Stack Developer': [
    ['Full Stack Web Dev – Coursera', 'https://www.coursera.org/specializations/full-stack-mobile-app-development'],
    ['MERN Stack Full Course – freeCodeCamp (FREE)', 'https://youtu.be/7CqJlxBYj-M'],
    ['MEAN Stack Bootcamp – Udemy', 'https://www.udemy.com/course/full-stack-web-development-mega-pack/'],
    ['System Design for Beginners – YouTube', 'https://youtu.be/l5zn6mP5uY8'],
    ['Git & GitHub Bootcamp – Udemy', 'https://www.udemy.com/course/git-complete/'],
    ['Backend Roadmap – Roadmap.sh (FREE)', 'https://roadmap.sh/backend'],
    ['Frontend Roadmap – Roadmap.sh (FREE)', 'https://roadmap.sh/frontend'],
    ['Docker for Developers – Udemy', 'https://www.udemy.com/course/docker-mastery/'],
    ['APIs for Developers – LinkedIn', 'https://www.linkedin.com/learning/apis-for-developers'],
    ['Full Stack Project Bootcamp – Udemy', 'https://www.udemy.com/course/100-days-of-web-development/']
],

'Software Engineer': [
    ['DSA Specialization – Coursera', 'https://www.coursera.org/specializations/data-structures-algorithms'],
    ['Cracking the Coding Interview Prep – Udemy', 'https://www.udemy.com/course/cracking-the-coding-interview/'],
    ['Clean Code – Udemy', 'https://www.udemy.com/course/clean-code/'],
    ['System Design Primer – freeCodeCamp (FREE)', 'https://youtu.be/UzLMhqg3_Wc'],
    ['Object-Oriented Design – Coursera', 'https://www.coursera.org/learn/object-oriented-design'],
    ['Design Patterns – Udemy', 'https://www.udemy.com/course/design-patterns-python/'],
    ['Algorithms – MIT OpenCourseWare (FREE)', 'https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/'],
    ['Competitive Programming – CodeChef', 'https://www.codechef.com/learn/dsa'],
    ['Problem Solving – HackerRank (FREE)', 'https://www.hackerrank.com/domains/algorithms'],
    ['Software Engineering Essentials – Coursera', 'https://www.coursera.org/specializations/software-engineering']
],

'ML Engineer': [
    ['MLOps Specialization – Coursera', 'https://www.coursera.org/specializations/mlops'],
    ['TensorFlow in Practice – Coursera', 'https://www.coursera.org/specializations/tensorflow-in-practice'],
    ['Feature Engineering – Coursera', 'https://www.coursera.org/learn/feature-engineering'],
    ['ML Engineer Nanodegree – Udacity', 'https://www.udacity.com/course/machine-learning-engineer-nanodegree--nd009t'],
    ['MLOps Bootcamp – Udemy', 'https://www.udemy.com/course/mlops-bootcamp/'],
    ['Model Deployment Tutorial – YouTube', 'https://youtu.be/ay2C1hRPD00'],
    ['ML System Design – YouTube', 'https://youtu.be/bP7mB6X1RZk'],
    ['Kubeflow for MLOps – Coursera', 'https://www.coursera.org/projects/kubeflow-pipelines'],
    ['Machine Learning with TensorFlow – Udemy', 'https://www.udemy.com/course/machinelearning/'],
    ['Deep Learning Specialization', 'https://www.coursera.org/specializations/deep-learning']
],

'Backend Developer': [
    ['Backend Development Roadmap – Roadmap.sh (FREE)', 'https://roadmap.sh/backend'],
    ['REST API Crash Course – freeCodeCamp (FREE)', 'https://youtu.be/Q-BpqyOT3a8'],
    ['Redis Crash Course – YouTube', 'https://youtu.be/Hbt56gFj998'],
    ['Authentication & JWT – Net Ninja', 'https://youtu.be/7Q17ubqLfaM'],
    ['Microservices Architecture – Udemy', 'https://www.udemy.com/course/microservices-with-node-js-and-react/'],
    ['Node.js Backend Masterclass – Udemy', 'https://www.udemy.com/course/nodejs-the-complete-guide/'],
    ['PostgreSQL Full Course – freeCodeCamp (FREE)', 'https://youtu.be/qw--VYLpxG4'],
    ['API Rate Limiting & Caching – YouTube', 'https://youtu.be/jKdCmhVxD0E'],
    ['Backend System Design – YouTube', 'https://youtu.be/hhAo4ZD3ou8'],
    ['NGINX Essentials – Udemy', 'https://www.udemy.com/course/nginx-crash-course/']
],

'Frontend Developer': [
    ['Frontend Development Roadmap – Roadmap.sh (FREE)', 'https://roadmap.sh/frontend'],
    ['HTML/CSS Full Course – freeCodeCamp (FREE)', 'https://youtu.be/kUMe1FH4CHE'],
    ['JavaScript Full Course – freeCodeCamp (FREE)', 'https://youtu.be/HD13eq_Pmp8'],
    ['ReactJS Full Course – freeCodeCamp (FREE)', 'https://youtu.be/bMknfKXIFA8'],
    ['Tailwind CSS Mastery – YouTube', 'https://youtu.be/pfaSUYaSgRo'],
    ['CSS Flexbox & Grid – Scrimba (FREE)', 'https://scrimba.com/learn/flexbox'],
    ['Vue.js Crash Course – YouTube', 'https://youtu.be/FXpIoQ_rT_c'],
    ['Frontend Nanodegree – Udacity', 'https://www.udacity.com/course/front-end-web-developer-nanodegree--nd0011'],
    ['Web Accessibility Course – Udacity', 'https://www.udacity.com/course/web-accessibility--ud891'],
    ['UI Design for Developers – Udemy', 'https://www.udemy.com/course/ui-design-for-developers/']
]

}


    # Insert into DB
    for category, course_list in courses_data.items():
        for course_name, course_url in course_list:
            if not Course.query.filter_by(name=course_name).first():
                db.session.add(Course(category=category, name=course_name, url=course_url))

    db.session.commit()
    return "✅ Courses added successfully!"

@app.route("/download_sample_resume")
def download_sample_resume():
    sample_path = os.path.join(os.getcwd(), "Sample_Resume_Format.docx")  # or .docx
    return send_file(sample_path, as_attachment=True)


# ---------------- UPLOAD CONFIG ---------------- #
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ===============================================================
#                  🚀 FINAL UNIQUE JOB KEYWORDS
# ===============================================================

# ------------------- OLD ROLES (CLEANED) ----------------------
JOB_KEYWORDS = {
    "Data Science": {
        "python", "pandas", "numpy", "tensorflow", "keras", "pytorch",
        "scikit-learn", "machine learning", "deep learning", "nlp"
    },

    "Web Development": {
        "php", "wordpress", "magento", "laravel", "express", "mongodb",
        "frontend", "backend", "nodejs", "react", "html", "css", "javascript"
    },

    "Android Development": {
        "android", "kotlin", "jetpack compose", "android studio", "firebase"
    },

    "iOS Development": {
        "ios", "swift", "objective-c", "swiftui", "xcode", "uikit"
    },

    "UI/UX Design": {
        "figma", "adobe xd", "wireframes", "mockups", "prototyping"
    },

    "Data Analyst": {
        "excel", "power bi", "tableau", "sql", "analytics", "data cleaning"
    },

    "Cloud & DevOps": {
        "aws", "gcp", "docker", "kubernetes", "terraform",
        "jenkins", "ci/cd", "ansible"
    },

    "Cybersecurity": {
        "ethical hacking", "penetration testing", "burp suite",
        "kali linux", "firewall", "siem"
    },

    "Quality Assurance": {
        "selenium", "cypress", "pytest", "automation testing"
    },

    "Business Analyst": {
        "documentation", "requirement gathering", "stakeholder"
    },

    "Database Administrator": {
        "pl/sql", "oracle", "postgresql", "normalization", "backup",
        "performance tuning"
    },

    "AI / NLP Engineer": {
        "transformers", "huggingface", "bert", "gpt",
        "text classification", "language model"
    },

    "Product Manager": {
        "product management", "market research", "roadmap"
    },

    "Python Developer": {
        "python", "django", "fastapi", "flask", "automation"
    },

    "Java Developer": {
        "java", "j2ee", "spring", "spring boot", "hibernate", "microservices"
    },

    ".NET Developer": {
        "c#", "asp.net", "entity framework", "linq", ".net"
    },

    "PHP Developer": {
        "php developer", "php", "laravel"
    },

    "JavaScript Developer": {
        "javascript", "ecmascript", "callbacks", "promises", "async", "await"
    },

    "Full Stack Developer": {
        "full stack", "git", "system design", "html", "css",
        "javascript", "backend", "frontend"
    },

    "Backend Developer": {
        "redis", "authentication", "authorization", "nodejs", "django", "spring boot"
    },

    "Frontend Developer": {
        "responsive design", "ui design", "react", "html", "css"
    },

    # ⭐⭐⭐ NEW ROLE ADDED HERE ⭐⭐⭐
    "C/C++ Developer": {
        "c", "c++", "oops", "object oriented programming",
        "data structures", "dsa", "stl", "pointers",
        "memory management"
    }
}








# ---------------- HOME ---------------- #
@app.route('/')
def home():
    return render_template('home.html')

# ---------------- REGISTER ---------------- #
# @app.route('/register', methods=['GET', 'POST'])
# def register():

#     if request.method == 'POST':
#         session.pop('_flashes', None)
# @app.route('/register', methods=['GET', 'POST'])
# def register():

#     if request.method == 'GET':
#         session.pop('_flashes', None)

#     if request.method == 'POST':
#         session.pop('_flashes', None)
#         name = request.form['name']
#         email = request.form['email']
#         password = request.form['password']
#         confirm_password = request.form['confirm_password']
#         role = request.form['role']

#         # Match Passwords
#         if password != confirm_password:
#             flash("Passwords do not match!", "danger")
#             return redirect(url_for('register'))

#         # Password Strength Validation
#         password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'

#         if not re.match(password_pattern, password):
#             flash("Password must contain at least 1 uppercase, 1 lowercase, 1 number, 1 special character, and be at least 8 characters long.", "danger")
#             return redirect(url_for('register'))

#         # Existing User Validation
#         if User.query.filter_by(email=email).first():
#             flash("Email already registered!", "danger")
#             return redirect(url_for('register'))

#         # Admin Role Validation
#         if role == "admin":
#             admin_key = request.form.get('adminKey')
#             if admin_key != "ADMIN123":
#                 flash("Incorrect Admin Secret Key!", "danger")
#                 return redirect(url_for('register'))

#         # Save User
#         hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
#         new_user = User(name=name, email=email, password=hashed_password, role=role)
#         db.session.add(new_user)
#         db.session.commit()

#         flash("Registration successful! Please login.", "success")
#         return redirect(url_for('login'))

#     return render_template('register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        # Password match
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))

        # Email exists
        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(url_for('register'))

        # Admin key check
        if role == "admin":
            admin_key = request.form.get('adminKey')
            if admin_key != "ADMIN123":
                flash("Incorrect Admin Secret Key!", "danger")
                return redirect(url_for('register'))

        # Save user
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = User(name=name, email=email, password=hashed_pw, role=role)

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    # GET → show register page
    return render_template('register.html')




# ---------------- LOGIN ---------------- #
# @app.route('/login', methods=['GET', 'POST'])
# def login():

#     if request.method == 'GET':
#         session.pop('_flashes', None)

#     if request.method == 'POST':
#         email = request.form.get('email')
#         password = request.form.get('password')
#         role = request.form.get('role')

#         user = User.query.filter_by(email=email).first()

#         if not user:
#             flash("Email not found! Please register first.", "danger")
#             return redirect(url_for("login"))

#         if not bcrypt.check_password_hash(user.password, password):
#             flash("Incorrect password!", "danger")
#             return redirect(url_for("login"))

#         if user.role != role:
#             flash("Incorrect role selected!", "danger")
#             return redirect(url_for("login"))

#         # Success login
#         session['user_id'] = user.id
#         session['role'] = user.role
#         session['user_name'] = user.name   # <-- ADD THIS


#         flash(f"Welcome, {user.name}!", "success")

#         # FIXED REDIRECT
#         if user.role == "admin":
#             return redirect(url_for("admin_dashboard"))
#         else:
#             return redirect(url_for("candidate_dashboard"))

#     return render_template("login.html")

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')

        user = User.query.filter_by(email=email).first()

        # EMAIL CHECK
        if not user:
            flash("Email not found! Please register first.", "danger")
            return redirect(url_for("login"))

        # PASSWORD CHECK
        if not bcrypt.check_password_hash(user.password, password):
            flash("Incorrect password!", "danger")
            return redirect(url_for("login"))

        # ROLE CHECK
        if user.role != role:
            flash("Incorrect role selected!", "danger")
            return redirect(url_for("login"))

        # SUCCESS
        session['user_id'] = user.id
        session['role'] = user.role
        session['user_name'] = user.name
        flash(f"Welcome, {user.name}!", "success")

        if user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("candidate_dashboard"))

    # GET request → Just show login page
    return render_template("login.html")



# ---------------- CANDIDATE DASHBOARD ---------------- #
@app.route('/candidate')
def candidate_dashboard():

    # -----------------------------------
    # 1. Check Login + Role Validation
    # -----------------------------------
    if 'user_id' not in session or session.get('role') != 'candidate':
        flash("Please login as Candidate to access this page.", "warning")
        return redirect(url_for('login'))

    # -----------------------------------
    # 2. Fetch Logged-in User
    # -----------------------------------
    user_id = session.get('user_id')
    user = User.query.get(user_id)

    if not user:
        # User might be deleted by admin
        session.clear()
        flash("Your account no longer exists. Please contact support.", "danger")
        return redirect(url_for('login'))

    # -----------------------------------
    # 3. Fetch resumes uploaded by candidate
    # -----------------------------------
    resumes = (
        Resume.query
        .filter_by(user_id=user.id)
        .order_by(Resume.uploaded_at.desc())  # show newest first
        .all()
    )

    # -----------------------------------
    # 4. Render Dashboard
    # -----------------------------------
    return render_template(
        'candidate.html',
        user=user,
        resumes=resumes
    )

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
    file_bytes = file.read()   # Read file into memory

    # Detect MIME type for parser
    mime_type = file.mimetype  

    user = User.query.get(session['user_id'])

    try:
        # -------------------------------
        # Extract TEXT directly from BYTES
        # -------------------------------
        from modules.parser import extract_text_bytes
        text = extract_text_bytes(file_bytes, mime_type)

        analysis = analyze_resume(text)

        # Save resume in database
        new_resume = Resume(
            user_id=user.id,
            file_name=filename,
            file_data=file_bytes,          # Store binary file
            file_mime=mime_type,           # Store mime for parsing later
            parsed_text=analysis.get('summary', ''),
            skills=', '.join(analysis.get('skills_found', [])),
            experience=str(analysis.get('experience', '')),
            suggested_roles=analysis.get('suggested_roles', '')
        )

        db.session.add(new_resume)
        db.session.commit()

        flash("Resume uploaded & analyzed successfully!", "success")
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
    if session.get('role') == 'candidate' and resume.user_id != session.get('user_id'):
        flash("You do not have permission to view this resume.", "danger")
        return redirect(url_for('candidate_dashboard'))

    candidate = User.query.get(resume.user_id)

    # -----------------------------------
    # ALWAYS INITIALIZE skills_cleaned
    # -----------------------------------
    skills_cleaned = []

    try:
        # Read text from database-stored file bytes
        from modules.parser import extract_text_bytes, extract_name
        file_bytes = resume.file_data
        mime_type = resume.file_mime

        text = extract_text_bytes(file_bytes, mime_type)

        # ---------- Extract Candidate Name ----------
        extracted_name = extract_name(text)
        resume.candidate_name = extracted_name if extracted_name else (candidate.name if candidate else "Unknown")
        db.session.commit()

        # ---------- Analyze Resume ----------
        analysis = analyze_resume(text)

        # SKILLS
        skills_list = analysis.get("skills_found", [])
        skills_cleaned = [s.lower().strip() for s in skills_list]
        resume.skills = ", ".join(skills_cleaned)

        # ---------- Role Prediction ----------
        rt_lower = text.lower()
        role_scores = {}

        for role, keywords in JOB_KEYWORDS.items():
            score = sum(5 for kw in keywords if kw.lower() in skills_cleaned)
            role_scores[role] = score

        predicted_role = max(role_scores, key=role_scores.get)
        predicted_role = predicted_role if role_scores[predicted_role] > 0 else None
        resume.predicted_role = predicted_role



        # ---------- ROLE DATA ----------- #
        ROLE_DATA = {

    # =========================================================
    # 1) DATA SCIENCE
    # =========================================================
    "Data Science": {
        "skills": ['tensorflow', 'keras', 'pytorch', 'scikit-learn', 'machine learning',
                   'deep learning', 'streamlit', 'opencv', 'ai', 'nlp'],
        "courses": [
            ("Machine Learning Crash Course – Google (FREE)", "https://developers.google.com/machine-learning/crash-course"),
            ("Machine Learning – Andrew Ng", "https://www.coursera.org/learn/machine-learning"),
            ("Data Science Roadmap – freeCodeCamp (FREE)", "https://youtu.be/X3paOmcrTjQ"),
            ("Deep Learning Specialization – Andrew Ng", "https://www.coursera.org/specializations/deep-learning"),
            ("Python for Data Science – Coursera", "https://www.coursera.org/learn/python-for-data-science"),
            ("Data Scientist with Python – DataCamp", "https://www.datacamp.com/tracks/data-scientist-with-python"),
            ("Data Science Bootcamp – Udemy", "https://www.udemy.com/course/data-science-and-machine-learning-bootcamp-with-python/"),
            ("Statistics for Data Science – Udemy", "https://www.udemy.com/course/statistics-for-data-science-and-business-analysis/"),
            ("Intro to Machine Learning – Kaggle (FREE)", "https://www.kaggle.com/learn/intro-to-machine-learning"),
            ("AI for Everyone – Andrew Ng", "https://www.coursera.org/learn/ai-for-everyone")
        ]
    },

    # =========================================================
    # 2) WEB DEVELOPMENT
    # =========================================================
    "Web Development": {
        "skills": ['php', 'wordpress', 'magento', 'laravel', 'express',
                   'rest api', 'mongodb', 'frontend', 'backend'],
        "courses": [
            ("The Odin Project (FREE Full Stack)", "https://www.theodinproject.com"),
            ("HTML & CSS Crash Course – freeCodeCamp (FREE)", "https://www.freecodecamp.org/learn/responsive-web-design/"),
            ("JavaScript Full Course – freeCodeCamp (FREE)", "https://youtu.be/jS4aFq5-91M"),
            ("React – Codecademy", "https://www.codecademy.com/learn/react-101"),
            ("Node.js Crash Course – freeCodeCamp", "https://youtu.be/Oe421EPjeBE"),
            ("Full Stack Web Dev – Udacity", "https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd0044"),
            ("Django for Everyone – Coursera", "https://www.coursera.org/specializations/django"),
            ("Complete Web Dev Bootcamp – Udemy", "https://www.udemy.com/course/the-complete-web-development-bootcamp/"),
            ("Next.js Full Tutorial – freeCodeCamp", "https://youtu.be/Y6KDk5iyrYE"),
            ("Frontend Developer Roadmap – Roadmap.sh (FREE)", "https://roadmap.sh/frontend")
        ]
    },

    # =========================================================
    # 3) ANDROID DEVELOPMENT
    # =========================================================
    "Android Development": {
        "skills": ['android', 'kotlin', 'jetpack compose', 'android studio', 'firebase', 'kivy'],
        "courses": [
            ("Android Basics by Google (FREE)", "https://www.udacity.com/course/android-basics--nd803"),
            ("Android Kotlin Developer – Udacity", "https://www.udacity.com/course/android-kotlin-developer-nanodegree--nd940"),
            ("Android Studio Masterclass – Udemy", "https://www.udemy.com/course/android-oreo-kotlin-app-masterclass/"),
            ("Kotlin Bootcamp – Google", "https://developer.android.com/courses/android-basics-kotlin/course"),
            ("Flutter Full Course – freeCodeCamp", "https://youtu.be/VPvVD8t02U8"),
            ("Jetpack Compose Tutorial – Google", "https://developer.android.com/jetpack/compose"),
            ("Android Specialization – Coursera", "https://www.coursera.org/specializations/android-app-development"),
            ("Flutter & Dart Bootcamp – Udemy", "https://www.udemy.com/course/flutter-dart-the-complete-flutter-app-development-course/"),
            ("Kotlin Essentials – JetBrains", "https://play.kotlinlang.org/koans/overview"),
            ("Android Clean Architecture Course", "https://youtu.be/EOfCEhWq8sg")
        ]
    },

    # =========================================================
    # 4) iOS DEVELOPMENT
    # =========================================================
    "iOS Development": {
        "skills": ['ios', 'swift', 'swiftui', 'objective-c', 'xcode', 'uikit', 'cocoa'],
        "courses": [
            ("Swift Full Course – freeCodeCamp", "https://youtu.be/comQ1-x2a1Q"),
            ("SwiftUI Essentials – Apple", "https://developer.apple.com/tutorials/swiftui"),
            ("iOS & Swift Bootcamp – Udemy", "https://www.udemy.com/course/ios-13-app-development-bootcamp/"),
            ("Become an iOS Developer – Udacity", "https://www.udacity.com/course/ios-developer-nanodegree--nd003"),
            ("Swift Programming – Codecademy", "https://www.codecademy.com/learn/learn-swift"),
            ("iOS App Development Specialization – Coursera", "https://www.coursera.org/specializations/app-development"),
            ("Objective-C Crash Course – Udemy", "https://www.udemy.com/course/objectivec/"),
            ("iOS Architecture – Udemy", "https://www.udemy.com/course/ios-architecture/"),
            ("SwiftUI Masterclass – Udemy", "https://www.udemy.com/course/swiftui-masterclass-course-ios-development-with-swift/"),
            ("Intro to iOS – LinkedIn", "https://www.linkedin.com/learning/topics/ios")
        ]
    },

    # =========================================================
    # 5) UI/UX DESIGN
    # =========================================================
    "UI/UX Design": {
        "skills": ['figma', 'adobe xd', 'balsamiq', 'prototyping', 'wireframes',
                   'mockups', 'usability testing', 'user interface', 'user experience'],
        "courses": [
            ("Google UX Design Certificate", "https://www.coursera.org/professional-certificates/google-ux-design"),
            ("Figma Full Course – freeCodeCamp", "https://youtu.be/jwCt4DCa2Ek"),
            ("UI/UX Specialization – Coursera", "https://www.coursera.org/specializations/ui-ux-design"),
            ("Adobe XD Full Course – YouTube", "https://youtu.be/68w2VwalD5w"),
            ("UX Fundamentals – Udemy", "https://www.udemy.com/course/ux-design-fundamentals/"),
            ("Design Thinking – Coursera", "https://www.coursera.org/learn/uva-darden-design-thinking-innovation"),
            ("UI Design Principles – Udemy", "https://www.udemy.com/course/design-rules/"),
            ("UX Research at Scale – Coursera", "https://www.coursera.org/learn/ux-research-at-scale"),
            ("Interaction Design Foundation Courses", "https://www.interaction-design.org/courses"),
            ("Become a UX Designer – Udacity", "https://www.udacity.com/course/ux-designer-nanodegree--nd578")
        ]
    },

    # =========================================================
    # 6) DATA ANALYST
    # =========================================================
    "Data Analyst": {
        "skills": ['excel', 'power bi', 'tableau', 'data cleaning', 'analytics'],
        "courses": [
            ("Google Data Analytics Certificate", "https://www.coursera.org/professional-certificates/google-data-analytics"),
            ("Excel to MySQL – Coursera", "https://www.coursera.org/specializations/excel-mysql"),
            ("Data Analyst with Python – DataCamp", "https://www.datacamp.com/tracks/data-analyst-with-python"),
            ("Power BI Full Course – freeCodeCamp", "https://youtu.be/0tAzpi3fXw4"),
            ("Tableau Training – Udemy", "https://www.udemy.com/course/tableau10/"),
            ("Statistics for Data Analysis – Udemy", "https://www.udemy.com/course/statistics-for-data-science-and-business-analysis/"),
            ("Pandas Tutorial – freeCodeCamp", "https://youtu.be/vmEHCJofslg"),
            ("SQL for Data Analysis – Coursera", "https://www.coursera.org/specializations/data-analysis-sql"),
            ("Excel Essential Training – LinkedIn", "https://www.linkedin.com/learning/excel-essential-training-2019"),
            ("Data Analytics Bootcamp – Udemy", "https://www.udemy.com/course/data-analytics-real-world-projects/")
        ]
    },

    # =========================================================
    # 7) CLOUD & DEVOPS
    # =========================================================
    "Cloud & DevOps": {
        "skills": ['aws', 'gcp', 'docker', 'kubernetes', 'terraform',
                   'jenkins', 'ci/cd', 'ansible', 'infrastructure'],
        "courses": [
            ("AWS Cloud Practitioner", "https://www.aws.training/Details/eLearning?id=60697"),
            ("Docker + Kubernetes – Udemy", "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/"),
            ("Terraform for Beginners", "https://learn.hashicorp.com/collections/terraform/aws-get-started"),
            ("Azure DevOps Tutorial – Microsoft", "https://learn.microsoft.com/en-us/training/modules/introduction-to-devops/"),
            ("DevOps Foundations – LinkedIn", "https://www.linkedin.com/learning/devops-foundations"),
            ("Linux Administration – Udemy", "https://www.udemy.com/course/linux-admin-bootcamp/"),
            ("GCP Cloud Engineer – Coursera", "https://www.coursera.org/professional-certificates/gcp-cloud-engineering"),
            ("Kubernetes Bootcamp – freeCodeCamp", "https://youtu.be/X48VuDVv0do"),
            ("Jenkins From Zero to Hero – Udemy", "https://www.udemy.com/course/jenkins-from-zero-to-hero/"),
            ("Ansible for Beginners – Udemy", "https://www.udemy.com/course/ansible-for-the-absolute-beginner/")
        ]
    },

    # =========================================================
    # 8) CYBERSECURITY
    # =========================================================
    "Cybersecurity": {
        "skills": ['cybersecurity', 'ethical hacking', 'penetration testing',
                   'network security', 'firewall', 'siem', 'burp suite',
                   'kali linux', 'vulnerability assessment'],
        "courses": [
            ("Intro to Cybersecurity – Cisco", "https://www.netacad.com/courses/cybersecurity/introduction-cybersecurity"),
            ("Google Cybersecurity Certificate", "https://www.coursera.org/professional-certificates/google-cybersecurity"),
            ("Certified Ethical Hacker (CEH)", "https://www.eccouncil.org/train-certify/certified-ethical-hacker-ceh/"),
            ("Cybersecurity Full Course – freeCodeCamp", "https://youtu.be/3Kq1MIfTWCE"),
            ("Kali Linux for Hackers – Udemy", "https://www.udemy.com/course/ethical-hacking-beginners/"),
            ("Network Security – LinkedIn", "https://www.linkedin.com/learning/topics/network-security"),
            ("Burp Suite Masterclass – Udemy", "https://www.udemy.com/course/burp-suite-mastering-bug-bounty/"),
            ("Pentesting with Nmap – Udemy", "https://www.udemy.com/course/nmap-complete-guide/"),
            ("Cryptography – Coursera", "https://www.coursera.org/learn/cryptography"),
            ("Malware Analysis – Udemy", "https://www.udemy.com/course/malware-analysis/")
        ]
    },

    # =========================================================
    # 9) QUALITY ASSURANCE (QA)
    # =========================================================
    "Quality Assurance": {
        "skills": ['automation testing', 'selenium', 'cypress', 'api testing',
                   'bug tracking', 'pytest', 'quality assurance'],
        "courses": [
            ("Manual Testing – Udemy", "https://www.udemy.com/course/manual-testing-with-tutorial/"),
            ("Selenium with Python – Udemy", "https://www.udemy.com/course/selenium-webdriver-with-python/"),
            ("Cypress Automation – Udemy", "https://www.udemy.com/course/cypress-tutorial/"),
            ("API Testing with Postman – Udemy", "https://www.udemy.com/course/postman-the-complete-guide/"),
            ("QA Testing Full Course – freeCodeCamp", "https://youtu.be/XkW6OVv1kwA"),
            ("JIRA Crash Course – LinkedIn", "https://www.linkedin.com/learning/jira-service-management"),
            ("Automated Testing Specialization – Coursera", "https://www.coursera.org/specializations/automated-software-testing"),
            ("Unit Testing in Python – Udemy", "https://www.udemy.com/course/python-unit-testing-automation/"),
            ("Test Automation University (FREE)", "https://testautomationu.applitools.com/"),
            ("Bug Tracking & Reporting – Udemy", "https://www.udemy.com/course/bug-reporting/")
        ]
    },

    # =========================================================
    # 10) BUSINESS ANALYST
    # =========================================================
    "Business Analyst": {
        "skills": ['business analysis', 'requirement gathering', 'documentation',
                   'stakeholder', 'project management'],
        "courses": [
            ("BA Fundamentals – Udemy", "https://www.udemy.com/course/business-analysis-fundamentals/"),
            ("Agile Business Analyst – Coursera", "https://www.coursera.org/learn/agile-business-analyst"),
            ("Business Analytics – Coursera", "https://www.coursera.org/specializations/business-analytics"),
            ("Excel for Analysts – Coursera", "https://www.coursera.org/learn/excel-data-analysis"),
            ("JIRA for BA – Udemy", "https://www.udemy.com/course/jira-agile-project-management/"),
            ("Project Management Foundations – LinkedIn", "https://www.linkedin.com/learning/project-management-foundations"),
            ("Requirement Engineering – Udemy", "https://www.udemy.com/course/requirements-engineering/"),
            ("Business Communication – Coursera", "https://www.coursera.org/specializations/business-communication"),
            ("Business Data Analytics – Udemy", "https://www.udemy.com/course/business-data-science/"),
            ("SDLC Complete Guide – Udemy", "https://www.udemy.com/course/software-development-life-cycle/")
        ]
    },

    # =========================================================
    # 11) DATABASE ADMINISTRATOR (DBA)
    # =========================================================
    "Database Administrator": {
        "skills": ['pl/sql', 'oracle', 'postgresql', 'normalization',
                   'backup', 'performance tuning', 'rds'],
        "courses": [
            ("PostgreSQL Masterclass – Udemy", "https://www.udemy.com/course/postgresql-database-administration/"),
            ("SQL for Data Engineering – Coursera", "https://www.coursera.org/learn/data-eng-sql"),
            ("MySQL Full Course – freeCodeCamp", "https://youtu.be/7S_tz1z_5bA"),
            ("Oracle SQL Admin – Udemy", "https://www.udemy.com/course/oracle-sql-database-administration/"),
            ("DBMS Full Course – Gate Smashers", "https://youtu.be/4xCynWHbn8w"),
            ("PL/SQL Bootcamp – Udemy", "https://www.udemy.com/course/oracle-plsql-programming/"),
            ("Database Design – Coursera", "https://www.coursera.org/learn/database-design"),
            ("SQL Server – LinkedIn", "https://www.linkedin.com/learning/learning-sql-server"),
            ("Normalization & DB Design – Udemy", "https://www.udemy.com/course/database-design-and-management/"),
            ("NoSQL Essentials – Coursera", "https://www.coursera.org/learn/nosql-databases")
        ]
    },

    # =========================================================
    # 12) AI / NLP ENGINEER
    # =========================================================
    "AI / NLP Engineer": {
        "skills": ['transformers', 'huggingface', 'bert', 'gpt',
                   'text classification', 'language model', 'speech recognition'],
        "courses": [
            ("NLP Specialization – Coursera", "https://www.coursera.org/specializations/nlp"),
            ("HuggingFace Transformers Course – FREE", "https://huggingface.co/course/chapter1"),
            ("Deep Learning for NLP – Udemy", "https://www.udemy.com/course/nlp-natural-language-processing-with-python/"),
            ("BERT & GPT Hands-on – Udemy", "https://www.udemy.com/course/bert-transformers-nlp/"),
            ("Speech Recognition – Coursera", "https://www.coursera.org/learn/audio-processing"),
            ("Intro to NLP – freeCodeCamp", "https://youtu.be/fNxaJsNG3-s"),
            ("Stanford NLP – CS224N", "http://web.stanford.edu/class/cs224n/"),
            ("Transformers in Python – YouTube", "https://youtu.be/tiuPHWB1gkA"),
            ("AI for Everyone – Coursera", "https://www.coursera.org/learn/ai-for-everyone"),
            ("Neural Networks – Coursera", "https://www.coursera.org/learn/neural-networks-deep-learning")
        ]
    },

    # =========================================================
    # 13) PRODUCT MANAGER
    # =========================================================
    "Product Manager": {
        "skills": ['product management', 'roadmap', 'market research',
                   'data-driven', 'leadership', 'notion'],
        "courses": [
            ("Digital Product Management – Coursera", "https://www.coursera.org/learn/uva-darden-digital-product-management"),
            ("Product Management 101 – Udemy", "https://www.udemy.com/course/product-management-101/"),
            ("Agile Product Owner Role – LinkedIn", "https://www.linkedin.com/learning/agile-product-owner-role"),
            ("Product Strategy – Coursera", "https://www.coursera.org/learn/product-strategy"),
            ("Product Management Crash Course", "https://youtu.be/sJ14cWjrNzs"),
            ("Roadmapping for PMs – Udemy", "https://www.udemy.com/course/product-roadmaps/"),
            ("Business Strategy – Coursera", "https://www.coursera.org/specializations/business-strategy"),
            ("User Story Writing – Udemy", "https://www.udemy.com/course/user-story/"),
            ("Notion Productivity Course – YouTube", "https://youtu.be/pvJScuVF4TU"),
            ("PM Interview Prep – Udemy", "https://www.udemy.com/course/product-management-interview-crash-course/")
        ]
    },

    # =========================================================
    # 14) PYTHON DEVELOPER
    # =========================================================
    "Python Developer": {
        "skills": ['python', 'django', 'fastapi', 'tkinter', 'scripting',
                   'automation', 'flask'],
        "courses": [
            ("Python for Everybody – Coursera", "https://www.coursera.org/specializations/python"),
            ("Automate the Boring Stuff (FREE)", "https://automatetheboringstuff.com/"),
            ("Django Full Course – freeCodeCamp", "https://youtu.be/F5mRW0jo-U4"),
            ("FastAPI Full Course – YouTube", "https://youtu.be/0sOvCWFmrtA"),
            ("Python OOP – Udemy", "https://www.udemy.com/course/python-object-oriented-programming/"),
            ("Python Bootcamp – Udemy", "https://www.udemy.com/course/complete-python-bootcamp/"),
            ("Flask Web Development – Udemy", "https://www.udemy.com/course/python-and-flask-bootcamp/"),
            ("Python DSA – Udemy", "https://www.udemy.com/course/python-data-structures-and-algorithms/"),
            ("Asyncio in Python – YouTube", "https://youtu.be/3mbFky5M6dM"),
            ("Django REST API – Coursera", "https://www.coursera.org/projects/django-rest-framework")
        ]
    },

    # =========================================================
    # 15) JAVA DEVELOPER
    # =========================================================
    "Java Developer": {
        "skills": ['java', 'j2ee', 'spring', 'spring boot',
                   'hibernate', 'servlets', 'microservices'],
        "courses": [
            ("Java Masterclass – Udemy", "https://www.udemy.com/course/java-the-complete-java-developer-course/"),
            ("Java Full Course – freeCodeCamp", "https://youtu.be/A74TOX803D0"),
            ("Spring Boot Full Course – YouTube", "https://youtu.be/9SGDpanrc8U"),
            ("Hibernate Tutorial – Udemy", "https://www.udemy.com/course/hibernate-course/"),
            ("Java OOP – Udemy", "https://www.udemy.com/course/java-object-oriented-programming/"),
            ("Spring Security – Udemy", "https://www.udemy.com/course/spring-security-core-beginner-to-guru/"),
            ("Java Servlets & JSP – Udemy", "https://www.udemy.com/course/jsp-servlet-free-course/"),
            ("Spring Microservices – Udemy", "https://www.udemy.com/course/microservices-with-spring-boot/"),
            ("DSA in Java – Coding Ninjas", "https://www.codingninjas.com/courses/data-structures-and-algorithms-java"),
            ("Java Multithreading – YouTube", "https://youtu.be/h-T7XmyIHDE")
        ]
    },

    # =========================================================
    # 16) C/C++ DEVELOPER
    # =========================================================
    "C/C++ Developer": {
        "skills": ['c', 'c++', 'stl', 'memory management', 'linux programming'],
        "courses": [
            ("C Programming Full Course – freeCodeCamp", "https://youtu.be/KJgsSFOSQv0"),
            ("C++ Full Course – freeCodeCamp", "https://youtu.be/8jLOx1hD3_o"),
            ("DSA in C++ – Udemy", "https://www.udemy.com/course/datastructurescncpp/"),
            ("Advanced C++ – Udemy", "https://www.udemy.com/course/advanced-c-programming/"),
            ("Linux System Programming – Udemy", "https://www.udemy.com/course/linux-system-programming-techniques/"),
            ("Pointers in C – Udemy", "https://www.udemy.com/course/c-pointers/"),
            ("Competitive Programming – Codeforces", "https://codeforces.com/edu"),
            ("STL in C++ – YouTube", "https://youtu.be/PwS4LlQ2kZQ"),
            ("Operating Systems – Neso Academy", "https://youtu.be/_TpOHMCODXo"),
            ("C++ OOP Masterclass – Udemy", "https://www.udemy.com/course/cpp-classes/")
        ]
    },

    # =========================================================
    # 17) .NET DEVELOPER
    # =========================================================
    ".NET Developer": {
        "skills": ['c#', '.net', 'asp.net', 'entity framework', 'mvc', 'linq'],
        "courses": [
            ("C# Basics – freeCodeCamp", "https://youtu.be/GhQdlIFylQ8"),
            ("ASP.NET Core MVC – YouTube", "https://youtu.be/BfEjDD8mWYg"),
            ("Entity Framework Core – Pluralsight", "https://www.pluralsight.com/courses/entity-framework-core-getting-started"),
            ("C# Masterclass – Udemy", "https://www.udemy.com/course/csharp-tutorial-for-beginners/"),
            (".NET API Development – Udemy", "https://www.udemy.com/course/build-restful-apis-with-aspnet-core/"),
            ("LINQ Tutorial – Microsoft", "https://learn.microsoft.com/en-us/dotnet/csharp/programming-guide/concepts/linq/"),
            ("Microservices in .NET – Udemy", "https://www.udemy.com/course/microservices-architecture-and-implementation-on-dotnet/"),
            ("Blazor WebAssembly Course", "https://learn.microsoft.com/en-us/aspnet/core/blazor"),
            ("ASP.NET Razor Pages – Udemy", "https://www.udemy.com/course/aspnet-core-razor-pages/"),
            ("Clean Architecture in .NET – YouTube", "https://youtu.be/fJjKQla-PgM")
        ]
    },


    # =========================================================
    # 19) JAVASCRIPT DEVELOPER
    # =========================================================
    "JavaScript Developer": {
        "skills": ['ecmascript', 'dom', 'event loop', 'callbacks',
                   'promises', 'async', 'await'],
        "courses": [
            ("JavaScript Full Course – freeCodeCamp", "https://youtu.be/HD13eq_Pmp8"),
            ("Async JS Mastery – Udemy", "https://www.udemy.com/course/asynchronous-javascript/"),
            ("JavaScript DOM – YouTube", "https://youtu.be/0ik6X4DJKCc"),
            ("JavaScript Algorithms – freeCodeCamp", "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures/"),
            ("TypeScript Full Course – freeCodeCamp", "https://youtu.be/30LWjhZzg50"),
            ("Modern JS Bootcamp – Udemy", "https://www.udemy.com/course/javascript-beginners-complete-tutorial/"),
            ("JavaScript Design Patterns – Udemy", "https://www.udemy.com/course/learn-javascript-design-patterns/"),
            ("ES6+ Mastery – Udemy", "https://www.udemy.com/course/understand-javascript/"),
            ("Event Loop Deep Dive – YouTube", "https://youtu.be/8aGhZQkoFbQ"),
            ("Async/Await Guide – MDN", "https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous")
        ]
    },

    # =========================================================
    # 20) FULL STACK DEVELOPER
    # =========================================================
    "Full Stack Developer": {
        "skills": ['full stack', 'system design', 'version control', 'git'],
        "courses": [
            ("Full Stack Web Dev – Coursera", "https://www.coursera.org/specializations/full-stack-mobile-app-development"),
            ("MERN Stack Full Course – freeCodeCamp", "https://youtu.be/7CqJlxBYj-M"),
            ("MEAN Stack Bootcamp – Udemy", "https://www.udemy.com/course/full-stack-web-development-mega-pack/"),
            ("System Design for Beginners – YouTube", "https://youtu.be/l5zn6mP5uY8"),
            ("Git & GitHub Bootcamp – Udemy", "https://www.udemy.com/course/git-complete/"),
            ("Backend Roadmap – Roadmap.sh", "https://roadmap.sh/backend"),
            ("Frontend Roadmap – Roadmap.sh", "https://roadmap.sh/frontend"),
            ("Docker for Developers – Udemy", "https://www.udemy.com/course/docker-mastery/"),
            ("APIs for Developers – LinkedIn", "https://www.linkedin.com/learning/apis-for-developers"),
            ("Full Stack Project Bootcamp – Udemy", "https://www.udemy.com/course/100-days-of-web-development/")
        ]
    },

    # =========================================================
    # 21) BACKEND DEVELOPER
    # =========================================================
    "Backend Developer": {
        "skills": ['authentication', 'authorization', 'redis'],
        "courses": [
            ("Backend Roadmap – Roadmap.sh", "https://roadmap.sh/backend"),
            ("REST API Crash Course – freeCodeCamp", "https://youtu.be/Q-BpqyOT3a8"),
            ("Redis Crash Course – YouTube", "https://youtu.be/Hbt56gFj998"),
            ("JWT Authentication – Net Ninja", "https://youtu.be/7Q17ubqLfaM"),
            ("Microservices Architecture – Udemy", "https://www.udemy.com/course/microservices-with-node-js-and-react/"),
            ("Node.js Backend Masterclass – Udemy", "https://www.udemy.com/course/nodejs-the-complete-guide/"),
            ("PostgreSQL Full Course – freeCodeCamp", "https://youtu.be/qw--VYLpxG4"),
            ("API Rate Limiting & Caching – YouTube", "https://youtu.be/jKdCmhVxD0E"),
            ("Backend System Design – YouTube", "https://youtu.be/hhAo4ZD3ou8"),
            ("NGINX Essentials – Udemy", "https://www.udemy.com/course/nginx-crash-course/")
        ]
    },

    # =========================================================
    # 22) FRONTEND DEVELOPER
    # =========================================================
    "Frontend Developer": {
        "skills": ['responsive design', 'ui design'],
        "courses": [
            ("Frontend Roadmap – Roadmap.sh", "https://roadmap.sh/frontend"),
            ("HTML/CSS Full Course – freeCodeCamp", "https://youtu.be/kUMe1FH4CHE"),
            ("JavaScript Full Course – freeCodeCamp", "https://youtu.be/HD13eq_Pmp8"),
            ("React Full Course – freeCodeCamp", "https://youtu.be/bMknfKXIFA8"),
            ("Tailwind CSS Mastery – YouTube", "https://youtu.be/pfaSUYaSgRo"),
            ("CSS Flexbox & Grid – Scrimba", "https://scrimba.com/learn/flexbox"),
            ("Vue.js Crash Course – YouTube", "https://youtu.be/FXpIoQ_rT_c"),
            ("Frontend Nanodegree – Udacity", "https://www.udacity.com/course/front-end-web-developer-nanodegree--nd0011"),
            ("Web Accessibility – Udacity", "https://www.udacity.com/course/web-accessibility--ud891"),
            ("UI Design for Developers – Udemy", "https://www.udemy.com/course/ui-design-for-developers/")
        ]
    }
}


        # ---------- BUILD RECOMMENDATIONS ----------
        recommended_skills = []
        courses = []

        if predicted_role and predicted_role in ROLE_DATA:
            recommended_skills = ROLE_DATA[predicted_role]["skills"]
            courses = [{"name": n, "link": l} for n, l in ROLE_DATA[predicted_role]["courses"]]

        # ---------- Resume Score ----------
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

        # ---------- Save to DB ----------
        resume.resume_score = resume_score
        resume.tips = "\n".join(tips)
        resume.recommended_skills = ", ".join(recommended_skills)
        resume.courses = json.dumps([c["name"] for c in courses])
        resume.course_links = json.dumps([c["link"] for c in courses])
        db.session.commit()

    except Exception as e:
        traceback.print_exc()
        flash(f"Error analyzing resume: {str(e)}", "danger")

    # ---------- Load Courses ----------
    courses = []
    if resume.courses and resume.course_links:
        try:
            names = json.loads(resume.courses)
            links = json.loads(resume.course_links)
            courses = [{"name": n, "link": l} for n, l in zip(names, links)]
        except:
            pass

    # ---------- Recommended Skills ----------
    recommended_skills = resume.recommended_skills.split(",") if resume.recommended_skills else []
    tips = resume.tips.split("\n") if resume.tips else []

    # ---------- Roadmap ----------
    roadmap = ROADMAPS.get(resume.predicted_role)

    # -------------------------------------------------------
    # SAMPLE RESUME LOGIC (Case detection)
    # -------------------------------------------------------
    predicted_role = resume.predicted_role

    case_flag = 1
    case_message = ""

    if not skills_cleaned and not predicted_role:
        case_flag = 2
        case_message = (
            "Either your resume does not include a Skills section "
            "or the formatting prevented skill extraction. "
            "Please correct your resume using the sample format below."
        )

    # ---------- Render ----------
    return render_template(
        "view_resume.html",
        resume={
            "id": resume.id,
            "candidate_name": resume.candidate_name,
            "candidate_level": resume.candidate_level,
            "parsed_text": resume.parsed_text or "",
            "skills": resume.skills or "",
            "predicted_role": resume.predicted_role,
            "recommended_skills": recommended_skills,
            "tips": tips,
            "score": resume.resume_score,
            "courses": courses,
            "roadmap": roadmap
        },
        case_flag=case_flag,
        case_message=case_message
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
        {"name": "Cloud & DevOps", "image": "roadmaps/cloud___devops_roadmap.png"},
        {"name": "Cybersecurity", "image": "roadmaps/cybersecurity_roadmap.png"},
        {"name": "Quality Assurance", "image": "roadmaps/quality_assurance_roadmap.png"},
        {"name": "Business Analyst", "image": "roadmaps/business_analyst_roadmap.png"},
        {"name": "Database Administrator", "image": "roadmaps/database_administrator_roadmap.png"},
        {"name": "AI / NLP Engineer", "image": "roadmaps/ai___nlp_engineer_roadmap.png"},
        {"name": "Product Manager", "image": "roadmaps/product_manager_roadmap.png"},

        # ----------- NEW ROLES -----------
        {"name": "Python Developer", "image": "roadmaps/python_developer_roadmap.png"},
        {"name": "Java Developer", "image": "roadmaps/java_developer_roadmap.png"},
        {"name": "C/C++ Developer", "image": "roadmaps/c_c___developer_roadmap.png"},
        {"name": ".NET Developer", "image": "roadmaps/_net_developer_roadmap.png"},
        {"name": "JavaScript Developer", "image": "roadmaps/javascript_developer_roadmap.png"},
        {"name": "Full Stack Developer", "image": "roadmaps/fullstack_developer_roadmap.png"},
        {"name": "Backend Developer", "image": "roadmaps/backend_developer_roadmap.png"},
        {"name": "Frontend Developer", "image": "roadmaps/frontend_developer_roadmap.png"}
    ]

    return render_template("roadmap.html", roadmaps=roadmaps)



# ---------------- LOGOUT ---------------- #
# @app.route('/logout')
# def logout():
#     session.clear()
#     flash("You have been logged out.", "info")
#     return redirect(url_for('login'))
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