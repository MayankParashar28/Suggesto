import pandas as pd
import os

def generate_youtube_data():
    courses = [
        # Web Dev / Programming
        {
            "courseId": 2000001,
            "title": "Harvard CS50 – Full Computer Science Course",
            "instructor": "David J. Malan",
            "platform": "YouTube",
            "category": "Web Dev",
            "rating": 4.9,
            "url": "https://www.youtube.com/watch?v=8mAITcNt77k"
        },
        {
            "courseId": 2000002,
            "title": "JavaScript Mastery – Build 4 Real World Apps",
            "instructor": "Adrian Twarog",
            "platform": "YouTube",
            "category": "Web Dev",
            "rating": 4.8,
            "url": "https://www.youtube.com/watch?v=LMagNcngvcU"
        },
        {
            "courseId": 2000003,
            "title": "React JS Crash Course 2024",
            "instructor": "Traversy Media",
            "platform": "YouTube",
            "category": "Web Dev",
            "rating": 4.7,
            "url": "https://www.youtube.com/watch?v=w7ejDZ8SWv8"
        },
        {
            "courseId": 2000004,
            "title": "Python for Beginners (Full Course)",
            "instructor": "Programming with Mosh",
            "platform": "YouTube",
            "category": "Web Dev",
            "rating": 4.9,
            "url": "https://www.youtube.com/watch?v=_uQrJ0TkZlc"
        },
        # Design / UI/UX
        {
            "courseId": 2100001,
            "title": "Typography Hierarchy – Design Principles",
            "instructor": "The Futur",
            "platform": "YouTube",
            "category": "Design",
            "rating": 4.8,
            "url": "https://www.youtube.com/watch?v=z7vA9nI2lxs"
        },
        {
            "courseId": 2100002,
            "title": "UI/UX Design Full Course",
            "instructor": "DesignCourse",
            "platform": "YouTube",
            "category": "Design",
            "rating": 4.6,
            "url": "https://www.youtube.com/watch?v=c9Wg6ndoxSg"
        },
        # Business
        {
            "courseId": 2200001,
            "title": "How to Build a Startup",
            "instructor": "Y Combinator",
            "platform": "YouTube",
            "category": "Business",
            "rating": 4.9,
            "url": "https://www.youtube.com/watch?v=CBYhVcOn7To"
        },
        {
            "courseId": 2200002,
            "title": "Building a Personal Brand in 2024",
            "instructor": "GaryVee",
            "platform": "YouTube",
            "category": "Business",
            "rating": 4.5,
            "url": "https://www.youtube.com/watch?v=R6u_D7IuN-k"
        },
        # Music
        {
            "courseId": 2300001,
            "title": "Music Theory for Electronic Producers",
            "instructor": "Andrew Huang",
            "platform": "YouTube",
            "category": "Music",
            "rating": 4.8,
            "url": "https://www.youtube.com/watch?v=rgaTLrZGlk0"
        },
        {
            "courseId": 2300002,
            "title": "Mixing Masterclass (Logic Pro X)",
            "instructor": "In The Mix",
            "platform": "YouTube",
            "category": "Music",
            "rating": 4.7,
            "url": "https://www.youtube.com/watch?v=7uVQu8XpE80"
        }
    ]

    df = pd.DataFrame(courses)
    output_dir = "processed"
    os.makedirs(output_dir, exist_ok=True)
    df.to_csv(os.path.join(output_dir, "youtube_courses.csv"), index=False)
    print(f"✅ Generated {len(df)} YouTube courses in {output_dir}/youtube_courses.csv")

if __name__ == "__main__":
    generate_youtube_data()
