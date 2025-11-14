import os
from PIL import Image, ImageDraw, ImageFont
import re

# ---------- DEFINE ALL ROADMAPS ----------
ROADMAPS = {
    'Data Science': [
        'Learn Python, Statistics, and Probability',
        'Master Pandas, NumPy, and Data Visualization',
        'Understand Machine Learning Algorithms',
        'Work on Kaggle and Real ML Projects',
        'Build and Deploy End-to-End ML Pipelines'
    ],
    'Web Development': [
        'Learn HTML, CSS, and JavaScript',
        'Master Frontend Frameworks (React/Angular)',
        'Learn Backend (Node.js, Django, Laravel)',
        'Work with Databases like MySQL, MongoDB',
        'Deploy Full Stack Apps to Cloud'
    ],
    'Android Development': [
        'Learn Java/Kotlin and Android Studio',
        'Understand XML Layouts and Jetpack Components',
        'Use APIs, SQLite, and Firebase',
        'Build Responsive Android UI/UX',
        'Publish Apps to Google Play Store'
    ],
    'iOS Development': [
        'Learn Swift and Xcode',
        'Master UIKit and SwiftUI',
        'Understand API Integration and Core Data',
        'Build Production-Level iOS Apps',
        'Publish App on Apple App Store'
    ],
    'UI/UX Design': [
        'Learn Design Thinking Process',
        'Practice Wireframing and Prototyping',
        'Master Figma and Adobe XD Tools',
        'Conduct Usability Testing',
        'Build and Publish Your UI/UX Portfolio'
    ],
    'Data Analyst': [
        'Master Excel, SQL, and Power BI/Tableau',
        'Understand Data Cleaning and Preparation',
        'Learn Data Visualization Techniques',
        'Perform Statistical and Business Analysis',
        'Create Dashboards and Real Reports'
    ],
    'Cloud & DevOps': [
        'Learn Linux and Cloud Fundamentals',
        'Master AWS, Azure, or Google Cloud',
        'Work with Docker and Kubernetes',
        'Build CI/CD Pipelines with Jenkins',
        'Implement Infrastructure as Code (Terraform)'
    ],
    'Cybersecurity': [
        'Learn Networking, OS, and Protocols',
        'Master Tools (Nmap, Burp Suite, Wireshark)',
        'Understand Firewalls, SIEM, IDS/IPS',
        'Perform Vulnerability Assessment & PenTesting',
        'Prepare for CEH/Security+ Certification'
    ],
    'Quality Assurance': [
        'Learn Software Testing Fundamentals',
        'Master Manual & Automation Testing',
        'Work with Selenium, Cypress, and Postman',
        'Write Test Cases & Bug Reports (JIRA)',
        'Integrate QA with CI/CD Pipelines'
    ],
    'Business Analyst': [
        'Learn Business Analysis Fundamentals',
        'Understand Requirement Gathering & SDLC',
        'Master Excel, SQL, and Documentation',
        'Use Tools like JIRA, Power BI',
        'Work with Stakeholders & Agile Teams'
    ],
    'Database Administrator': [
        'Learn SQL & Database Fundamentals',
        'Master Database Architecture & Normalization',
        'Work with Oracle, PostgreSQL, MySQL',
        'Handle Backups, Recovery, and Security',
        'Optimize Performance & Indexing'
    ],
    'AI / NLP Engineer': [
        'Learn NLP Basics and Text Processing',
        'Master ML & Deep Learning Concepts',
        'Work with BERT, GPT, Transformers',
        'Use HuggingFace, SpaCy, NLTK',
        'Deploy NLP Models at Scale'
    ],
    'Product Manager': [
        'Understand Product Lifecycle',
        'Learn Market Research & Strategy',
        'Master Agile, Scrum & Roadmapping',
        'Use Tools like JIRA, Notion, Trello',
        'Deliver Real Product Launches'
    ],
    'Python Developer': [
        'Learn Core Python and OOP',
        'Master Django or Flask Frameworks',
        'Work with REST APIs and Databases',
        'Learn Testing, Debugging, Deployment',
        'Build Real-World Python Applications'
    ],
    'Java Developer': [
        'Master Core Java & OOP',
        'Learn Spring & Spring Boot',
        'Work with Hibernate & Microservices',
        'Build Secure REST APIs',
        'Deploy Java Apps to Cloud'
    ],
    'C/C++ Developer': [
        'Learn C/C++ Fundamentals',
        'Master Memory Management & Pointers',
        'Work with STL and OOP Concepts',
        'Practice OS & Linux Programming',
        'Build High-Performance Applications'
    ],
    '.NET Developer': [
        'Learn C# Programming',
        'Master ASP.NET Core & MVC',
        'Work with Entity Framework & LINQ',
        'Build REST APIs using .NET',
        'Deploy .NET Projects to Cloud'
    ],
    'JavaScript Developer': [
        'Master Core JavaScript & DOM',
        'Understand Async JS, Promises, Event Loop',
        'Learn TypeScript and Modern ES6+',
        'Build Real Projects with Vanilla JS',
        'Deploy JS Apps to Production'
    ],
    'Full Stack Developer': [
        'Learn Frontend (HTML, CSS, JS, React)',
        'Master Backend (Node/Django/PHP)',
        'Work with Databases (SQL/NoSQL)',
        'Learn Git, API Design, and Testing',
        'Deploy Full Stack Projects'
    ],
    'Backend Developer': [
        'Learn Server-Side Languages',
        'Master REST API Development',
        'Work with Redis, Authentication, JWT',
        'Use SQL + NoSQL Databases',
        'Implement Caching & Deployments'
    ],
    'Frontend Developer': [
        'Master HTML, CSS, and JavaScript',
        'Learn Frameworks (React, Vue)',
        'Build Responsive UI with Tailwind/Bootstrap',
        'Learn Web Accessibility & Performance',
        'Deploy Frontend Apps to Cloud'
    ]
}


# ---------- OUTPUT FOLDER ----------
output_dir = os.path.join('static', 'roadmaps')
os.makedirs(output_dir, exist_ok=True)

# ---------- FONT ----------
try:
    font = ImageFont.truetype("arial.ttf", 22)
except:
    font = ImageFont.load_default()

# ---------- GENERATE ROADMAP IMAGES ----------
for role, steps in ROADMAPS.items():
    width, height = 1100, 120 + len(steps) * 100
    img = Image.new('RGB', (width, height), color=(240, 248, 255))
    draw = ImageDraw.Draw(img)

    # Title
    title = f"{role} Roadmap"
    text_width = draw.textlength(title, font=font)
    draw.text(((width - text_width) / 2, 30), title, fill=(0, 51, 102), font=font)

    y = 120
    box_color = (25, 118, 210)
    text_color = (255, 255, 255)
    connector_color = (33, 150, 243)

    for i, step in enumerate(steps):
        x1, y1, x2, y2 = 100, y, width - 100, y + 60
        draw.rounded_rectangle([x1, y1, x2, y2], radius=15, fill=box_color, outline=(0, 0, 0))
        draw.text((x1 + 20, y1 + 15), step, fill=text_color, font=font)

        # Connector arrow
        if i < len(steps) - 1:
            mid_x = width // 2
            draw.line([(mid_x, y2), (mid_x, y2 + 35)], fill=connector_color, width=4)
            draw.polygon([
                (mid_x - 10, y2 + 35),
                (mid_x + 10, y2 + 35),
                (mid_x, y2 + 50)
            ], fill=connector_color)
        y += 100

    # Save image
    filename = re.sub(r'[^a-zA-Z0-9_]', '_', role.lower()) + "_roadmap.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    print(f"✅ Generated: {filepath}")

print("\n🎉 All roadmap images created successfully in static/roadmaps/")
