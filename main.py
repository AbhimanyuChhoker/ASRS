import datetime
import json

DATA_FILE = "spaced_repetition_data.json"
MAX_TOPICS_PER_DAY = 3

INITIAL_TOPICS = [
    "Road Not Taken", "Wind", "Reported Speech", "The Fun They Had", "The Lost Child",
    "Diary Entry", "Integrated Grammer", "The Sound Of Music PT.1", "The Sound Of Music PT.2",
    "The Adventures Of Toto", "Cells: The Fundamental Units of Life", "Matter in Our Surroundings",
    "Is Matter Around Us Pure?", "Motion", "Force and Laws of Motion", 
    "What is Democracy? Why Democracy?", "Electoral Politics", "The Story of Village Palampur",
    "People as a Resource", "Lektion 1", "Introduction to Python", "Entrepreneurial Skills-I",
    "The French Revolution"
]

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"topics": {}}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def add_topic(data, topic):
    if topic not in data["topics"]:
        data["topics"][topic] = {
            "level": 0,
            "next_review": datetime.date.today().isoformat(),
            "difficulty": 3  # Default difficulty
        }
        save_data(data)
        print(f"Added topic: {topic}")
    else:
        print(f"Topic '{topic}' already exists.")

def review_topic(data, topic):
    if topic in data["topics"]:
        topic_data = data["topics"][topic]
        topic_data["level"] += 1
        
        # Ask for difficulty rating
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
        
        # Adjust days to next review based on difficulty
        base_days = 2 ** topic_data["level"]
        difficulty_factor = (6 - difficulty) / 3  # This makes easier topics have longer intervals
        days_to_next_review = int(base_days * difficulty_factor)
        
        topic_data["next_review"] = (datetime.date.today() + datetime.timedelta(days=days_to_next_review)).isoformat()
        save_data(data)
        print(f"Reviewed '{topic}'. Next review in {days_to_next_review} days.")
    else:
        print(f"Topic '{topic}' not found.")

def get_topics_to_review(data):
    today = datetime.date.today().isoformat()
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
    for topic in INITIAL_TOPICS:
        if topic not in data["topics"]:
            add_topic(data, topic)
    print("Initial topics have been added.")

def main():
    data = load_data()
    initialize_topics(data)

    while True:
        print("\n1. Add a new topic")
        print("2. Review a topic")
        print("3. Show topics to review today")
        print("4. Show all topics")
        print("5. Exit")

        choice = input("Enter your choice (1-5): ")

        if choice == '1':
            topic = input("Enter the topic name: ")
            add_topic(data, topic)
        elif choice == '2':
            topic = input("Enter the topic to review: ")
            review_topic(data, topic)
        elif choice == '3':
            topics_to_review = get_topics_to_review(data)
            if topics_to_review:
                print(f"Topics to review today (max {MAX_TOPICS_PER_DAY}):")
                for topic in topics_to_review:
                    print(f"- {topic}")
            else:
                print("No topics to review today.")
        elif choice == '4':
            if data["topics"]:
                print("All topics:")
                for topic, topic_data in data["topics"].items():
                    print(f"- {topic} (Next review: {topic_data['next_review']}, Difficulty: {topic_data['difficulty']})")
            else:
                print("No topics added yet.")
        elif choice == '5':
            print("Exiting program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()