import datetime
import json
import time
import random
import os
from typing import Dict, List, Any
from collections import defaultdict
import pygame
from pygame import mixer
from pytube import YouTube
import ssl
ssl._create_default_https_context = ssl._create_unverified_context # for SSL Certificate Verification Failed


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
    ("The French Revolution", "History"),
]


class SpacedRepetitionSystem:
    def __init__(self):
        self.data: Dict[str, Any] = self.load_data()
        self.subjects: Dict[str, set] = defaultdict(set)
        self._initialize_subjects()
        self.homework = {}
        pygame.init()
        mixer.init()
        self.music_playing = False

    def load_data(self) -> Dict[str, Any]:
        if not os.path.exists(DATA_FILE):
            return {
                "topics": {},
                "total_reviews": 0,
                "subjects": {},
                "streak": {"current": 0, "longest": 0, "last_review": None, "last_homework": None},
                "homework": {},
                "total_homework_completed": 0
            }

        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                if "homework" not in data:
                    data["homework"] = {}
                if "total_homework_completed" not in data:
                    data["total_homework_completed"] = 0
                if "last_homework" not in data["streak"]:
                    data["streak"]["last_homework"] = None
                return data
        except json.JSONDecodeError:
            print("Error reading the data file. Creating a new one.")
            return {
                "topics": {},
                "total_reviews": 0,
                "subjects": {},
                "streak": {"current": 0, "longest": 0, "last_review": None, "last_homework": None},
                "homework": {},
                "total_homework_completed": 0
            }

    def _initialize_subjects(self):
        for topic, data in self.data["topics"].items():
            self.subjects[data["subject"]].add(topic)

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump({
                "topics": self.data["topics"],
                "total_reviews": self.data["total_reviews"],
                "subjects": self.data["subjects"],
                "streak": self.data["streak"],
                "homework": self.homework,
                "total_homework_completed": self.data.get("total_homework_completed", 0)
            }, f, indent=2)

    def add_topic(self, topic: str, subject: str):
        if topic not in self.data["topics"]:
            self.data["topics"][topic] = {
                "level": 0,
                "next_review": datetime.date.today().isoformat(),
                "difficulty": 3,
                "reviews": 0,
                "subject": subject,
                "review_dates": [],
            }
            self.subjects[subject].add(topic)
            self.save_data()
            print(f"Added topic: {topic} (subject: {subject})")
        else:
            print(f"Topic '{topic}' already exists.")

    def review_topic(self, topic: str):
        if topic in self.data["topics"]:
            topic_data = self.data["topics"][topic]
            topic_data["level"] += 1
            topic_data["reviews"] += 1
            self.data["total_reviews"] += 1

            topic_data["review_dates"].append(datetime.date.today().isoformat())

            while True:
                try:
                    difficulty = int(
                        input(
                            "Rate the difficulty (1-5, where 1 is easiest and 5 is hardest): "
                        )
                    )
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

            topic_data["next_review"] = (
                datetime.date.today() + datetime.timedelta(days=days_to_next_review)
            ).isoformat()
            self.update_streak()
            self.save_data()
            print(f"Reviewed '{topic}'. Next review in {days_to_next_review} days.")
        else:
            print(f"Topic '{topic}' not found.")

    def get_topics_to_review(self, subject: str = None) -> List[str]:
        today = datetime.date.today().isoformat()
        if subject:
            due_topics = {
                topic
                for topic in self.subjects.get(subject, set())
                if self.data["topics"][topic]["next_review"] <= today
            }
        else:
            due_topics = {
                topic
                for topic, topic_data in self.data["topics"].items()
                if topic_data["next_review"] <= today
            }

        sorted_topics = sorted(
            due_topics, key=lambda x: self.data["topics"][x]["next_review"]
        )

        if len(sorted_topics) > MAX_TOPICS_PER_DAY:
            topics_for_today = sorted_topics[:MAX_TOPICS_PER_DAY]
            topics_for_tomorrow = sorted_topics[MAX_TOPICS_PER_DAY:]

            tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
            for topic in topics_for_tomorrow:
                self.data["topics"][topic]["next_review"] = tomorrow

            self.save_data()
            print(f"Rescheduled {len(topics_for_tomorrow)} topic(s) for tomorrow.")
            return topics_for_today
        else:
            return sorted_topics

    def show_progress(self):
        total_topics = len(self.data["topics"])
        total_reviews = self.data["total_reviews"]
        total_homework = len(self.homework)
        total_homework_completed = self.data.get("total_homework_completed", 0)
        topics_reviewed = sum(1 for topic in self.data["topics"].values() if topic["reviews"] > 0)

        print(f"\nProgress Report:")
        print(f"Total topics: {total_topics}")
        print(f"Topics reviewed at least once: {topics_reviewed}")
        print(f"Total reviews: {total_reviews}")
        print(f"Average reviews per topic: {total_reviews / total_topics:.2f}")
        print(f"Total homework assigned: {total_homework}")
        print(f"Total homework completed: {total_homework_completed}")
        print(f"Homework completion rate: {(total_homework_completed / total_homework * 100) if total_homework else 0:.2f}%")

        print("\nTop 5 most reviewed topics:")
        sorted_topics = sorted(
            self.data["topics"].items(), key=lambda x: x[1]["reviews"], reverse=True
        )[:5]
        for topic, topic_data in sorted_topics:
            print(
                f"- {topic} ({topic_data['subject']}): {topic_data['reviews']} reviews"
            )

    def study_session(self):
        try:
            duration = int(
                input("Enter the duration of the study session in minutes: ")
            )
        except ValueError:
            print("Please enter a valid number of minutes.")
            return

        subject = input(
            "Enter a subject to focus on (or press Enter for all subject): "
        ).strip()
        if subject not in self.subjects:
            print(f"Subject '{subject}' not found.")
            return

        play_music = (
            input("Do you want to play music for this study session? (y/n): ")
            .lower()
            .strip()
        )
        if play_music == "y":
            self.toggle_music()

        end_time = time.time() + duration * 60
        topics_reviewed = 0

        while time.time() < end_time:
            due_topics = self.get_topics_to_review(subject)
            if not due_topics:
                print("No more topics to review. Session ended early.")
                break

            topic = random.choice(due_topics)
            print(f"\nTime remaining: {int((end_time - time.time()) / 60)} minutes")
            print(
                f"Review topic: {topic} (subject: {self.data['topics'][topic]['subject']})"
            )
            input("Press Enter when you're ready to rate the difficulty...")
            self.review_topic(topic)
            topics_reviewed += 1

        if self.music_playing:
            self.toggle_music()

        print(
            f"\nSession ended. You reviewed {topics_reviewed} topic(s) in this session."
        )

    def toggle_music(self):
        if self.music_playing:
            mixer.music.stop()
            self.music_playing = False
            print("Music stopped")
        else:
            music_dir = "music"
            if not os.path.exists(music_dir):
                print("Music directory does not exist. Creating...")
                os.mkdir(music_dir)
            music_files = [f for f in os.listdir(music_dir) if f.endswith(".mp3")]
            if music_files:
                music_file = os.path.join(music_dir, random.choice(music_files))
                mixer.music.load(music_file)
                mixer.music.play(-1)
                self.music_playing = True
                print("Music started.")
            else:
                print("No music files available.")

    def show_subjects(self):
        print("\nsubjects:")
        for subject, topics in self.subjects.items():
            print(f"- {subject}: {len(topics)} topics")

    def export_data(self):
        filename = input("Enter the filename to export data (e.g., 'export.json'): ")
        try:
            export_data = {
                "topics": self.data["topics"],
                "total_reviews": self.data["total_reviews"],
                "subjects": self.data["subjects"],
                "streak": self.data["streak"],
                "homework": self.homework,
                "total_homework_completed": self.data.get("total_homework_completed", 0)
            }
            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2)
            print(f"Data exported successfully to {filename}")
        except IOError:
            print("Error occurred while exporting data.")

    def import_data(self):
        filename = input("Enter the filename to import data from: ")
        try:
            with open(filename, "r") as f:
                imported_data = json.load(f)
            if not all(
                key in imported_data for key in ["topics", "total_reviews", "subjects"]
            ):
                print("Invalid data format in the import file.")
                return
            self.data = imported_data
            self._initialize_subjects()
            self.save_data()
            print(f"Data imported successfully from {filename}")
        except (IOError, json.JSONDecodeError):
            print(
                "Error occurred while importing data. Make sure the file exists and contains valid JSON."
            )

    def show_weekly_progress(self):
        today = datetime.date.today()
        week_ago = today - datetime.timedelta(days=7)
        daily_reviews = {
            (today - datetime.timedelta(days=i)).isoformat(): 0 for i in range(7)
        }

        for topic in self.data["topics"].values():
            for review_date in topic.get("review_dates", []):
                if review_date in daily_reviews:
                    daily_reviews[review_date] += 1

        print("\nWeekly Progress (Reviews per day):")
        for date, count in daily_reviews.items():
            bar = "#" * count
            print(f"{date}: {bar} ({count})")

    def update_streak(self, homework=False):
        today = datetime.date.today().isoformat()
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

        if self.data["streak"]["last_review"] == yesterday or (homework and self.data["streak"]["last_homework"] == yesterday):
            self.data["streak"]["current"] += 1
            self.data["streak"]["longest"] = max(
                self.data["streak"]["current"], self.data["streak"]["longest"]
            )
        elif self.data["streak"]["last_review"] != today and (not homework or self.data["streak"]["last_homework"] != today):
            self.data["streak"]["current"] = 1

        if homework:
            self.data["streak"]["last_homework"] = today
        else:
            self.data["streak"]["last_review"] = today
        self.save_data()

    def show_streak(self):
        print(f"\nCurrent streak: {self.data['streak']['current']} days")
        print(f"Longest streak: {self.data['streak']['longest']} days")
        print(f"Last review: {self.data['streak']['last_review']}")
        print(f"Last homework completion: {self.data['streak'].get('last_homework', 'Never')}")

    
    def show_topic_history(self):
        topic = input("Enter the topic name to show history: ")
        if topic in self.data["topics"]:
            topic_data = self.data["topics"][topic]
            print(f"\nReview history for '{topic}':")
            print(f"subject: {topic_data['subject']}")
            print(f"Current level: {topic_data['level']}")
            print(f"Total reviews: {topic_data['reviews']}")
            print(f"Current difficulty: {topic_data['difficulty']}")
            print(f"Next review: {topic_data['next_review']}")

            if "review_dates" in topic_data:
                print("\nPast reviews:")
                for date in topic_data["review_dates"]:
                    print(f"- {date}")
            else:
                print("\nNo past review data available.")
        else:
            print(f"Topic '{topic}' not found.")
    def add_homework(self, subject, description, due_date):
        homework_id = len(self.homework) + 1
        self.homework[homework_id] = {
            "subject": subject,
            "description": description,
            "due_date": due_date,
            "completed": False
        }
        print(f"Homework added with ID: {homework_id}")
        self.save_data()

    def complete_homework(self, homework_id):
        if homework_id in self.homework:
            if not self.homework[homework_id]["completed"]:
                self.homework[homework_id]["completed"] = True
                self.homework[homework_id]["completion_date"] = datetime.date.today().isoformat()
                self.data["total_homework_completed"] = self.data.get("total_homework_completed", 0) + 1
                self.update_streak(homework=True)
                print(f"Homework (ID: {homework_id}) marked as completed.")
                self.save_data()
            else:
                print(f"Homework (ID: {homework_id}) was already completed.")
        else:
            print(f"Homework with ID {homework_id} not found.")

    def show_homework(self):
        if not self.homework:
            print("No homework assigned.")
            return
        
        print("\nCurrent Homework:")
        for id, hw in self.homework.items():
            status = "Completed" if hw["completed"] else "Pending"
            print(f"ID: {id}, Subject: {hw['subject']}, Description: {hw['description']}, Due: {hw['due_date']}, Status: {status}")


def initialize_topics(srs):
    for topic, subject in INITIAL_TOPICS:
        srs.add_topic(topic, subject)
    print("Initial topics have been added.")


def main():
    srs = SpacedRepetitionSystem()
    if not srs.data["topics"]:
        initialize_topics(srs)

    while True:
        print("\n1. Add a new topic")
        print("2. Review a topic")
        print("3. Show topics to review today")
        print("4. Show all topics")
        print("5. Show progress")
        print("6. Start a study session")
        print("7. Show subjects")
        print("8. Export data (JSON)")
        print("9. Import data (JSON)")
        print("10. Show weekly progress")
        print("11. Show streak")
        print("12. Show topic history")
        print("13. Toggle music")
        print("14. Add homework")
        print("15. Complete homework")
        print("16. Show homework")
        print("17. Exit")

        choice = input("Enter your choice (1-17): ")

        if choice == "1":
            topic = input("Enter the topic name: ")
            subject = input("Enter the subject: ")
            srs.add_topic(topic, subject)
        elif choice == "2":
            topic = input("Enter the topic to review: ")
            srs.review_topic(topic)
        elif choice == "3":
            subject = input("Enter a subject (or press Enter for all subjects): ").strip()
            topics_to_review = srs.get_topics_to_review(subject if subject else None)
            if topics_to_review:
                print(f"Topics to review today (max {MAX_TOPICS_PER_DAY}):")
                for topic in topics_to_review:
                    print(f"- {topic} (subject: {srs.data['topics'][topic]['subject']})")
            else:
                print("No topics to review today.")
        elif choice == "4":
            if srs.data["topics"]:
                print("All topics:")
                for topic, topic_data in srs.data["topics"].items():
                    print(f"- {topic} (subject: {topic_data['subject']}, Next review: {topic_data['next_review']}, Difficulty: {topic_data['difficulty']}, Reviews: {topic_data['reviews']})")
            else:
                print("No topics added yet.")
        elif choice == "5":
            srs.show_progress()
        elif choice == "6":
            srs.study_session()
        elif choice == "7":
            srs.show_subjects()
        elif choice == "8":
            srs.export_data()
        elif choice == "9":
            srs.import_data()
        elif choice == "10":
            srs.show_weekly_progress()
        elif choice == "11":
            srs.show_streak()
        elif choice == "12":
            srs.show_topic_history()
        elif choice == "13":
            srs.toggle_music()
        elif choice == "14":
            subject = input("Enter the subject for the homework: ")
            description = input("Enter the homework description: ")
            due_date = input("Enter the due date (YYYY-MM-DD): ")
            srs.add_homework(subject, description, due_date)
        elif choice == "15":
            homework_id = int(input("Enter the homework ID to mark as completed: "))
            srs.complete_homework(homework_id)
        elif choice == "16":
            srs.show_homework()
        elif choice == "17":
            if srs.music_playing:
                srs.toggle_music()
            print("Exiting program. Bye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 17.")

if __name__ == "__main__":
    main()
