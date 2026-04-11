import pandas as pd
import os

URL = "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2020/2020-02-11/udemy_courses.csv"

def fetch_and_transform():
    print(f"📦 Fetching real Udemy data from {URL}...")
    try:
        df_raw = pd.read_csv(URL)
        print(f"✅ Downloaded {len(df_raw)} courses.")
        
        # Mapping to Suggesto Format
        # Original keys: course_id, course_title, url, is_paid, price, num_subscribers, num_reviews, num_lectures, level, content_duration, published_timestamp, subject
        
        df = pd.DataFrame()
        df["courseId"] = df_raw["course_id"]
        df["title"] = df_raw["course_title"]
        df["instructor"] = "Udemy Expert" # Default since instructors aren't in this CSV
        df["platform"] = "Udemy"
        df["category"] = df_raw["subject"].replace({
            "Business Finance": "Business",
            "Graphic Design": "Design",
            "Musical Instruments": "Music",
            "Web Development": "Web Dev"
        })
        
        # Calculate a pseudo-rating 1.0 - 5.0 based on subscribers/reviews
        # We'll use a simple log-scale estimate
        import numpy as np
        norm_reviews = np.log1p(df_raw["num_reviews"]) / np.log1p(df_raw["num_reviews"].max())
        df["rating"] = (4.0 + norm_reviews).clip(1.0, 5.0).round(1)
        
        # Format URLs (ensure absolute)
        df["url"] = df_raw["url"]
        
        os.makedirs("processed", exist_ok=True)
        df.to_csv("processed/courses_processed.csv", index=False)
        print(f"✅ Successfully processed {len(df)} real courses into processed/courses_processed.csv")
        
        # Print category distribution for app.js sync
        print("\n📊 Subject Distribution for 'CATEGORIES.courses':")
        print(df["category"].unique().tolist())
        
    except Exception as e:
        print(f"❌ Failed to fetch real data: {e}")

if __name__ == "__main__":
    fetch_and_transform()

