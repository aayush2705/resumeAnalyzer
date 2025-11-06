import os
from PIL import Image, ImageDraw, ImageFont
import re

# ---------- DEFINE ROADMAPS ----------
ROADMAPS = {
    'Data Science': [
        'Learn Python and Statistics',
        'Master Libraries: NumPy, Pandas, Matplotlib',
        'Understand Machine Learning Algorithms',
        'Work on Data Cleaning and EDA Projects',
        'Learn Deep Learning and TensorFlow/PyTorch',
        'Build End-to-End ML Projects and Deploy'
    ],
    'Web Development': [
        'Learn HTML, CSS, and JavaScript',
        'Master Frontend Frameworks (React, Angular, or Vue)',
        'Learn Backend (Node.js, Django, Flask)',
        'Understand Databases (MySQL, MongoDB)',
        'Learn APIs, Authentication, and Deployment',
        'Build Full Stack Projects'
    ],
    'Android Development': [
        'Learn Java or Kotlin',
        'Understand Android Studio and XML Layouts',
        'Learn Android Jetpack Components',
        'Work with APIs and Databases',
        'Publish Your First App on Play Store'
    ],
    'iOS Development': [
        'Learn Swift Programming Language',
        'Understand Xcode and Storyboards',
        'Learn UIKit and SwiftUI',
        'Implement Core Data and Networking',
        'Publish App on App Store'
    ],
    'UI/UX Design': [
        'Understand Design Principles',
        'Learn Wireframing and Prototyping Tools (Figma, Adobe XD)',
        'Study Color Theory and Typography',
        'Build User-Centered Designs',
        'Create Case Studies for Portfolio'
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

# ---------- GENERATE IMAGES ----------
for role, steps in ROADMAPS.items():
    width, height = 1000, 100 + len(steps) * 100
    img = Image.new('RGB', (width, height), color=(240, 248, 255))
    draw = ImageDraw.Draw(img)

    # Title
    title = f"{role} Roadmap"
    draw.text((width // 2 - 150, 30), title, fill=(0, 51, 102), font=font)

    y = 100
    box_color = (70, 130, 180)
    text_color = (255, 255, 255)
    connector_color = (70, 130, 180)

    for i, step in enumerate(steps):
        x1, y1, x2, y2 = 100, y, width - 100, y + 60
        draw.rectangle([x1, y1, x2, y2], fill=box_color, outline=(0, 0, 0))
        draw.text((x1 + 20, y1 + 15), step, fill=text_color, font=font)

        # Connector arrow
        if i < len(steps) - 1:
            draw.line([(width // 2, y2), (width // 2, y2 + 40)], fill=connector_color, width=4)
            draw.polygon([
                (width // 2 - 10, y2 + 40),
                (width // 2 + 10, y2 + 40),
                (width // 2, y2 + 55)
            ], fill=connector_color)
        y += 100

    # Save image
    filename = re.sub(r'[^a-zA-Z0-9_]', '_', role.lower()) + "_roadmap.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    print(f"✅ Generated: {filepath}")

print("\n🎉 All roadmap images created successfully in static/roadmaps/")
