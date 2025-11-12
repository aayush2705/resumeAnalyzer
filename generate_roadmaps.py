import os
from PIL import Image, ImageDraw, ImageFont
import re

# ---------- DEFINE ALL ROADMAPS ----------
ROADMAPS = {
    'Data Science': [
        'Learn Python and Statistics Fundamentals',
        'Master Data Wrangling and Visualization with Pandas & Matplotlib',
        'Understand Machine Learning Algorithms',
        'Practice with Real-World Datasets (Kaggle)',
        'Build and Deploy End-to-End Data Science Projects'
    ],
    'Web Development': [
        'Learn HTML, CSS, and JavaScript',
        'Understand Frontend Frameworks like React or Angular',
        'Master Backend with Node.js, Django, or Flask',
        'Work with Databases like MySQL or MongoDB',
        'Deploy Full Stack Applications on Cloud Platforms'
    ],
    'Android Development': [
        'Learn Java or Kotlin for Android',
        'Understand Android Studio and XML Layouts',
        'Learn Android Jetpack Components and APIs',
        'Integrate SQLite and Firebase for Data Management',
        'Publish Your First App on Google Play Store'
    ],
    'iOS Development': [
        'Learn Swift and Xcode IDE',
        'Understand UIKit and SwiftUI Frameworks',
        'Implement Core Data and API Networking',
        'Build UI/UX for iOS Devices',
        'Publish Your First App on Apple App Store'
    ],
    'UI/UX Design': [
        'Understand Design Thinking Process',
        'Learn Wireframing and Prototyping with Figma/Adobe XD',
        'Master Visual Design Principles',
        'Test and Iterate User Experience Flows',
        'Build a Professional UI/UX Design Portfolio'
    ],
    'Data Analyst': [
        'Learn Excel, SQL, and Power BI/Tableau',
        'Understand Data Cleaning and Transformation',
        'Master Data Visualization Tools',
        'Learn Statistics and Basic Python Analysis',
        'Work on Business-Oriented Dashboards and Reports'
    ],
    'Cloud & DevOps': [
        'Learn Linux, Networking, and Shell Scripting',
        'Understand Cloud Platforms (AWS, Azure, GCP)',
        'Work with Docker and Kubernetes',
        'Implement CI/CD Pipelines and Infrastructure as Code',
        'Monitor and Optimize Deployments'
    ],
    'Cybersecurity': [
        'Understand Networking and Operating Systems',
        'Learn Ethical Hacking Tools (Nmap, Burp Suite)',
        'Master Security Concepts: Firewalls, Encryption, SIEM',
        'Explore Vulnerability Management and Incident Response',
        'Pursue CEH or CompTIA Security+ Certification'
    ],
    'Quality Assurance': [
        'Understand Software Testing Fundamentals',
        'Learn Manual and Automated Testing (Selenium/Postman)',
        'Master API and UI Testing Frameworks',
        'Integrate Testing into CI/CD Pipelines',
        'Explore QA Tools like JIRA and TestNG'
    ],
    'Business Analyst': [
        'Learn Requirement Gathering and Documentation',
        'Understand Agile and Scrum Methodologies',
        'Develop Analytical Thinking and Communication Skills',
        'Use Tools like Excel, JIRA, Power BI',
        'Collaborate on Project Reports and Stakeholder Analysis'
    ],
    'Database Administrator': [
        'Learn SQL Fundamentals and Normalization',
        'Understand Database Design and Modeling',
        'Manage Backups, Recovery, and Performance Tuning',
        'Work with Oracle, PostgreSQL, or MySQL',
        'Secure and Monitor Database Systems'
    ],
    'AI / NLP Engineer': [
        'Understand NLP Fundamentals and Text Processing',
        'Learn Machine Learning and Deep Learning Basics',
        'Work with Transformers, BERT, and GPT Models',
        'Use Libraries like Hugging Face and SpaCy',
        'Deploy NLP Models into Production Environments'
    ],
    'Product Manager': [
        'Understand Product Lifecycle and Market Research',
        'Develop Communication and Leadership Skills',
        'Learn Agile and Scrum Frameworks',
        'Use Tools like JIRA, Notion, and Trello',
        'Work on Real Product Strategy and Launch Projects'
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
