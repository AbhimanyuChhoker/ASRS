import datetime
import json
import time
import random
import os

DATA_FILE = "spaced_repetition_data.json"
MAX_TOPICS_PER_DAY = 3

INITIAL_TOPICS = [
    ("Road Not Taken", "Literature"),
    ("Wind", "Literature"),
    ("Reported Speech", "Grammar"),
    ("The Fun They Had", "Literature"),
    ("The Lost Child", "Literature"),
    ("Diary Entry", "Writing"),
    ("Integrated Grammar", "Grammar"),
    ("The Sound Of Music PT.1", "Literature"),
    ("The Sound Of Music PT.2", "Literature"),
    ("The Adventures Of Toto", "Literature"),
    ("Cells: The Fundamental Units of Life", "Science"),
    ("Matter in Our Surroundings", "Science"),
    ("Is Matter Around Us Pure?", "Science"),
    ("Motion", "Physics"),
    ("Force and Laws of Motion", "Physics"),
    ("What is Democracy? Why Democracy?", "Social Studies"),
    ("Electoral Politics", "Social Studies"),
    ("The Story of Village Palampur", "Economics"),
    ("People as a Resource", "Economics"),
    ("Lektion 1", "German"),
    ("Introduction to Python", "Computer Science"),
    ("Entrepreneurial Skills-I", "Business"),
    ("The French Revolution", "History")
]

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"topics": {}, "total_reviews": 0, "categories": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_topic(data, topic, category):
    if topic not in data["topics"]:
        data["topics"][topic] = {
            "level": 0,
            "next_review": datetime.date.today().isoformat(),
            "difficulty": 3,
            "reviews": 0,
            "category": category
        }
        if category not in data["categories"]:
            data["categories"][category] = []
        data["categories"][category].append(topic)
        save_data(data)
        print(f"Added topic: {topic} (Category: {category})")
    else:
        print(f"Topic '{topic}' already exists.")

def review_topic(data, topic):
    if topic in data["topics"]:
        topic_data = data["topics"][topic]
        topic_data["level"] += 1
        topic_data["reviews"] += 1
        data["total_reviews"] += 1
        
        while True:
            try:
                difficulty = int(input("Rate the difficulty (1-5, where 1 is easiest and 5 is hardest): "))
                if 1 <= difficulty <= 5:
                    topic_data["difficulty"] = difficulty
                    break
                else:
                    print("Please enter a number between 1 and 5.")
            except ValueError:
                print("Please enter a valid number.")
        
        base_days = 2 ** topic_data["level"]
        difficulty_factor = (6 - difficulty) / 3
        days_to_next_review = int(base_days * difficulty_factor)
        
        topic_data["next_review"] = (datetime.date.today() + datetime.timedelta(days=days_to_next_review)).isoformat()
        save_data(data)
        print(f"Reviewed '{topic}'. Next review in {days_to_next_review} days.")
    else:
        print(f"Topic '{topic}' not found.")

def get_topics_to_review(data, category=None):
    today = datetime.date.today().isoformat()
    if category:
        due_topics = [topic for topic in data["categories"].get(category, [])
                      if data["topics"][topic]["next_review"] <= today]
    else:
        due_topics = [topic for topic, topic_data in data["topics"].items() 
                      if topic_data["next_review"] <= today]
    
    if len(due_topics) > MAX_TOPICS_PER_DAY:
        topics_for_today = due_topics[:MAX_TOPICS_PER_DAY]
        topics_for_tomorrow = due_topics[MAX_TOPICS_PER_DAY:]
        
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        for topic in topics_for_tomorrow:
            data["topics"][topic]["next_review"] = tomorrow
        
        save_data(data)
        print(f"Rescheduled {len(topics_for_tomorrow)} topic(s) for tomorrow.")
        return topics_for_today
    else:
        return due_topics

def initialize_topics(data):
    for topic, category in INITIAL_TOPICS:
        if topic not in data["topics"]:
            add_topic(data, topic, category)
    print("Initial topics have been added.")

def show_progress(data):
    total_topics = len(data["topics"])
    total_reviews = data["total_reviews"]
    topics_reviewed = sum(1 for topic in data["topics"].values() if topic["reviews"] > 0)
    
    print(f"\nProgress Report:")
    print(f"Total topics: {total_topics}")
    print(f"Topics reviewed at least once: {topics_reviewed}")
    print(f"Total reviews: {total_reviews}")
    print(f"Average reviews per topic: {total_reviews / total_topics:.2f}")
    
    print("\nTop 5 most reviewed topics:")
    sorted_topics = sorted(data["topics"].items(), key=lambda x: x[1]["reviews"], reverse=True)[:5]
    for topic, topic_data in sorted_topics:
        print(f"- {topic} ({topic_data['category']}): {topic_data['reviews']} reviews")

def study_session(data):
    try:
        duration = int(input("Enter the duration of the study session in minutes: "))
    except ValueError:
        print("Please enter a valid number of minutes.")
        return

    category = input("Enter a category to focus on (or press Enter for all categories): ").strip()
    if category and category not in data["categories"]:
        print(f"Category '{category}' not found.")
        return

    end_time = time.time() + duration * 60
    topics_reviewed = 0

    while time.time() < end_time:
        due_topics = get_topics_to_review(data, category)
        if not due_topics:
            print("No more topics to review. Session ended early.")
            break

        topic = random.choice(due_topics)
        print(f"\nTime remaining: {int((end_time - time.time()) / 60)} minutes")
        print(f"Review topic: {topic} (Category: {data['topics'][topic]['category']})")
        input("Press Enter when you're ready to rate the difficulty...")
        review_topic(data, topic)
        topics_reviewed += 1

    print(f"\nSession ended. You reviewed {topics_reviewed} topic(s) in this session.")

def show_categories(data):
    print("\nCategories:")
    for category, topics in data["categories"].items():
        print(f"- {category}: {len(topics)} topics")

def export_data(data):
    filename = input("Enter the filename to export data (e.g., 'export.json'): ")
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Data exported successfully to {filename}")
    except IOError:
        print("Error occurred while exporting data.")

def import_data():
    filename = input("Enter the filename to import data from: ")
    try:
        with open(filename, 'r') as f:
            imported_data = json.load(f)
        if not all(key in imported_data for key in ["topics", "total_reviews", "categories"]):
            print("Invalid data format in the import file.")
            return None
        print(f"Data imported successfully from {filename}")
        return imported_data
    except (IOError, json.JSONDecodeError):
        print("Error occurred while importing data. Make sure the file exists and contains valid JSON.")
        return None

def main():
    data = load_data()
    initialize_topics(data)

    while True:
        print("\n1. Add a new topic")
        print("2. Review a topic")
        print("3. Show topics to review today")
        print("4. Show all topics")
        print("5. Show progress")
        print("6. Start a study session")
        print("7. Show categories")
        print("8. Export data")
        print("9. Import data")
        print("10. Exit")

        choice = input("Enter your choice (1-10): ")

        if choice == '1':
            topic = input("Enter the topic name: ")
            category = input("Enter the category: ")
            add_topic(data, topic, category)
        elif choice == '2':
            topic = input("Enter the topic to review: ")
            review_topic(data, topic)
        elif choice == '3':
            category = input("Enter a category (or press Enter for all categories): ").strip()
            topics_to_review = get_topics_to_review(data, category if category else None)
            if topics_to_review:
                print(f"Topics to review today (max {MAX_TOPICS_PER_DAY}):")
                for topic in topics_to_review:
                    print(f"- {topic} (Category: {data['topics'][topic]['category']})")
            else:
                print("No topics to review today.")
        elif choice == '4':
            if data["topics"]:
                print("All topics:")
                for topic, topic_data in data["topics"].items():
                    print(f"- {topic} (Category: {topic_data['category']}, Next review: {topic_data['next_review']}, Difficulty: {topic_data['difficulty']}, Reviews: {topic_data['reviews']})")
            else:
                print("No topics added yet.")
        elif choice == '5':
            show_progress(data)
        elif choice == '6':
            study_session(data)
        elif choice == '7':
            show_categories(data)
        elif choice == '8':
            export_data(data)
        elif choice == '9':
            imported_data = import_data()
            if imported_data:
                data = imported_data
                save_data(data)
        elif choice == '10':
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()