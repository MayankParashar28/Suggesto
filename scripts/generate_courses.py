import pandas as pd
import os

courses = [
    # AI & ML
    {"courseId": 1, "title": "Machine Learning Specialization", "instructor": "Andrew Ng", "platform": "Coursera", "category": "AI", "rating": 4.9, "url": "https://www.coursera.org/specializations/machine-learning-introduction"},
    {"courseId": 2, "title": "Deep Learning Specialization", "instructor": "Andrew Ng", "platform": "Coursera", "category": "AI", "rating": 4.8, "url": "https://www.coursera.org/specializations/deep-learning"},
    {"courseId": 3, "title": "CS50's Introduction to Computer Science", "instructor": "David J. Malan", "platform": "edX", "category": "Computer Science", "rating": 4.9, "url": "https://www.edx.org/course/introduction-computer-science-harvardx-cs50x"},
    {"courseId": 4, "title": "Python for Everybody", "instructor": "Charles Severance", "platform": "Coursera", "category": "Python", "rating": 4.8, "url": "https://www.coursera.org/specializations/python"},
    {"courseId": 5, "title": "Practical Deep Learning for Coders", "instructor": "Jeremy Howard", "platform": "fast.ai", "category": "AI", "rating": 4.9, "url": "https://course.fast.ai/"},
    {"courseId": 6, "title": "Introduction to Data Science", "instructor": "IBM", "platform": "Coursera", "category": "Data Science", "rating": 4.7, "url": "https://www.coursera.org/specializations/introduction-data-science"},
    {"courseId": 7, "title": "Mathematics for Machine Learning", "instructor": "Imperial College London", "platform": "Coursera", "category": "Math", "rating": 4.6, "url": "https://www.coursera.org/specializations/mathematics-machine-learning"},
    {"courseId": 8, "title": "Generative AI with Large Language Models", "instructor": "DeepLearning.AI", "platform": "Coursera", "category": "Generative AI", "rating": 4.8, "url": "https://www.coursera.org/learn/generative-ai-with-llms"},
    
    # Development
    {"courseId": 9, "title": "The Web Developer Bootcamp", "instructor": "Colt Steele", "platform": "Udemy", "category": "Web Dev", "rating": 4.7, "url": "https://www.udemy.com/course/the-web-developer-bootcamp/"},
    {"courseId": 10, "title": "React - The Complete Guide", "instructor": "Maximilian Schwarzmüller", "platform": "Udemy", "category": "Web Dev", "rating": 4.8, "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/"},
    {"courseId": 11, "title": "Full Stack Open", "instructor": "University of Helsinki", "platform": "Free", "category": "Web Dev", "rating": 4.9, "url": "https://fullstackopen.com/en/"},
    {"courseId": 12, "title": "Modern JavaScript From The Beginning", "instructor": "Brad Traversy", "platform": "Udemy", "category": "Web Dev", "rating": 4.7, "url": "https://www.udemy.com/course/modern-javascript-from-the-beginning/"},
    
    # Design & Creative
    {"courseId": 13, "title": "Google UX Design Professional Certificate", "instructor": "Google", "platform": "Coursera", "category": "UX Design", "rating": 4.8, "url": "https://www.coursera.org/professional-certificates/google-ux-design"},
    {"courseId": 14, "title": "Graphic Design Specialization", "instructor": "CalArts", "platform": "Coursera", "category": "Design", "rating": 4.7, "url": "https://www.coursera.org/specializations/graphic-design"},
    {"courseId": 15, "title": "Product Design Masterclass", "instructor": "Various", "platform": "Skillshare", "category": "Design", "rating": 4.6, "url": "https://www.skillshare.com/"},
    {"courseId": 16, "title": "UI/UX Design Bootcamp", "instructor": "Various", "platform": "Udemy", "category": "UX Design", "rating": 4.5, "url": "https://www.udemy.com/"},
    
    # More AI/ML
    {"courseId": 17, "title": "Reinforcement Learning Specialization", "instructor": "University of Alberta", "platform": "Coursera", "category": "AI", "rating": 4.7, "url": "https://www.coursera.org/specializations/reinforcement-learning"},
    {"courseId": 18, "title": "Natural Language Processing Specialization", "instructor": "DeepLearning.AI", "platform": "Coursera", "category": "AI", "rating": 4.8, "url": "https://www.coursera.org/specializations/natural-language-processing"},
    {"courseId": 19, "title": "TensorFlow Developer Certificate", "instructor": "DeepLearning.AI", "platform": "Coursera", "category": "AI", "rating": 4.8, "url": "https://www.coursera.org/professional-certificates/tensorflow-in-practice"},
    {"courseId": 20, "title": "PyTorch for Deep Learning", "instructor": "Various", "platform": "Udemy", "category": "AI", "rating": 4.7, "url": "https://www.udemy.com/"},
    
    # Data Science
    {"courseId": 21, "title": "Data Engineering Zoomcamp", "instructor": "DataTalksClub", "platform": "GitHub-Free", "category": "Data Engineering", "rating": 4.9, "url": "https://github.com/DataTalksClub/data-engineering-zoomcamp"},
    {"courseId": 22, "title": "Tableau for Data Science", "instructor": "Various", "platform": "Udemy", "category": "Data Science", "rating": 4.6, "url": "https://www.udemy.com/"},
    {"courseId": 23, "title": "SQL for Data Science", "instructor": "UC Davis", "platform": "Coursera", "category": "Data Science", "rating": 4.7, "url": "https://www.coursera.org/learn/sql-for-data-science"}
]

# Generate more pseudo-data to reach ~100
for i in range(24, 101):
    cat = courses[i % len(courses)]["category"]
    courses.append({
        "courseId": i,
        "title": f"Advanced {cat} Techniques {i}",
        "instructor": "Suggesto Expert",
        "platform": "Suggesto Academy",
        "category": cat,
        "rating": round(4.0 + (i % 10) / 10, 1),
        "url": "https://suggesto.inc/academy"
    })

df = pd.DataFrame(courses)
os.makedirs("processed", exist_ok=True)
df.to_csv("processed/courses_processed.csv", index=False)
print(f"✅ Generated {len(df)} courses in processed/courses_processed.csv")
