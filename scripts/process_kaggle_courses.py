import pandas as pd
import numpy as np
import os

RAW_FILE = "processed/kaggle_temp.csv"
OUT_FILE = "processed/courses_processed.csv"

def process():
    print(f"🛠️ Processing Kaggle data from {RAW_FILE}...")
    if not os.path.exists(RAW_FILE):
        print("❌ Raw file not found!")
        return

    df_raw = pd.read_csv(RAW_FILE)
    
    # Mapping
    df = pd.DataFrame()
    df["courseId"] = df_raw["course_id"]
    df["title"] = df_raw["course_title"]
    df["instructor"] = "Udemy Expert" # Mirror dataset doesn't have instructor names
    df["platform"] = "Udemy"
    
    # Normalize subjects
    df["category"] = df_raw["subject"].replace({
        "Business Finance": "Business",
        "Graphic Design": "Design",
        "Musical Instruments": "Music",
        "Web Development": "Web Dev"
    })
    
    # Calculate Rating (1.0 - 5.0)
    # Using log-normalized subscriber/review counts
    score = (np.log1p(df_raw["num_subscribers"]) + np.log1p(df_raw["num_reviews"])) / 2
    df["rating"] = (3.5 + (score / score.max() * 1.5)).clip(1.0, 5.0).round(1)
    
    # URL formatting
    df["url"] = df_raw["url"]
    
    df.to_csv(OUT_FILE, index=False)
    print(f"✅ Successfully processed {len(df)} real Kaggle masterpieces into {OUT_FILE}")
    print("\n📚 Final Category Sync for app.js:")
    print(df["category"].unique().tolist())

if __name__ == "__main__":
    process()

