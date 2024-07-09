import datetime
import json
import time
import random
import os
import csv
from typing import Dict, List, Any
from collections import defaultdict
import pygame
from pygame import mixer
from pytube import YouTube

# TODO: Add feature to automatically download music files from youtube

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
        pygame.init()
        mixer.init()
        self.music_playing = False

    def load_data(self) -> Dict[str, Any]:
        if not os.path.exists(DATA_FILE):
            return {
                "topics": {},
                "total_reviews": 0,
                "subjects": {},
                "streak": {"current": 0, "longest": 0, "last_review": None},
            }

        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Error reading the data file. Creating a new one.")
            return {
                "topics": {},
                "total_reviews": 0,
                "subjects": {},
                "streak": {"current": 0, "longest": 0, "last_review": None},
            }

    def _initialize_subjects(self):
        for topic, data in self.data["topics"].items():
            self.subjects[data["subject"]].add(topic)

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

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
        topics_reviewed = sum(
            1 for topic in self.data["topics"].values() if topic["reviews"] > 0
        )

        print(f"\nProgress Report:")
        print(f"Total topics: {total_topics}")
        print(f"Topics reviewed at least once: {topics_reviewed}")
        print(f"Total reviews: {total_reviews}")
        print(f"Average reviews per topic: {total_reviews / total_topics:.2f}")

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
        if not self.music_playing:
            music_dir = "music"
            if not os.path.exists(music_dir):
                print("Music directory does not exist")
            else:
                music_files = [f for f in os.listdir(music_dir) if f.endswith(".mp3")]
                if music_files:
                    music_file = os.path.join(music_dir, random.choice(music_files))
                    mixer.music.load(music_file)
                    mixer.music.play(-1)
                    self.music_started = True
                    print("Music started.")
                else:
                    print("No music data available.")
        else:
            mixer.music.stop()
            self.music_started = False
            print("Music stopped")
    
    def download_music(url, download_path="music"):
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        print("You can download music from YouTube")
        print("Options are: ")
        print("1. Piano music")
        print("2. Lofi music")
        choice = input("Enter a choice or paste url of you video you want to download: ")
        if choice == 1 or 2 or 3:
            print("Downloading music")
            if choice == 1:
                url = "https://www.youtube.com/watch?v=sAcj8me7wGI"
                yt = YouTube(url)
                audio_stream = yt.streams.filter(only_audio=True).first()
                audio_stream.download(output_path=download_path)
                print(f"{yt.title} downloaded successfully to {download_path}")
            elif choice == 2:
                url = "https://www.youtube.com/watch?v=CfPxlb8-ZQ0"
                yt = YouTube(url)
                audio_stream = yt.streams.filter(only_audio=True).first()
                audio_stream.download(output_path=download_path)
                print(f"{yt.title} downloaded successfully to {download_path}")
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        audio_stream.download(output_path=download_path)
        print(f"{yt.title} downloaded successfully to {download_path}")

    def show_subjects(self):
        print("\nsubjects:")
        for subject, topics in self.subjects.items():
            print(f"- {subject}: {len(topics)} topics")

    def export_data(self):
        filename = input("Enter the filename to export data (e.g., 'export.json'): ")
        try:
            with open(filename, "w") as f:
                json.dump(self.data, f, indent=2)
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

    def update_streak(self):
        today = datetime.date.today().isoformat()
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

        if self.data["streak"]["last_review"] == yesterday:
            self.data["streak"]["current"] += 1
            self.data["streak"]["longest"] = max(
                self.data["streak"]["current"], self.data["streak"]["longest"]
            )
        elif self.data["streak"]["last_review"] != today:
            self.data["streak"]["current"] = 1

        self.data["streak"]["last_review"] = today
        self.save_data()

    def show_streak(self):
        print(f"\nCurrent streak: {self.data['streak']['current']} days")
        print(f"Longest streak: {self.data['streak']['longest']} days")

    def export_to_csv(self):
        filename = input("Enter the filename to export data (e.g., 'export.csv'): ")
        try:
            with open(filename, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(
                    [
                        "Topic",
                        "subject",
                        "Level",
                        "Next Review",
                        "Difficulty",
                        "Reviews",
                    ]
                )
                for topic, topic_data in self.data["topics"].items():
                    writer.writerow(
                        [
                            topic,
                            topic_data["subject"],
                            topic_data["level"],
                            topic_data["next_review"],
                            topic_data["difficulty"],
                            topic_data["reviews"],
                        ]
                    )
            print(f"Data exported successfully to {filename}")
        except IOError:
            print("Error occurred while exporting data.")

    def import_from_csv(self):
        filename = input(
            "Enter the filename to import data from (e.g., 'import.csv'): "
        )
        try:
            imported_data = {"topics": {}, "total_reviews": 0, "subjects": {}}
            with open(filename, "r") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    topic = row["Topic"]
                    imported_data["topics"][topic] = {
                        "subject": row["subject"],
                        "level": int(row["Level"]),
                        "next_review": row["Next Review"],
                        "difficulty": int(row["Difficulty"]),
                        "reviews": int(row["Reviews"]),
                    }
                    imported_data["total_reviews"] += int(row["Reviews"])
                    if row["subject"] not in imported_data["subjects"]:
                        imported_data["subjects"][row["subject"]] = []
                    imported_data["subjects"][row["subject"]].append(topic)
            self.data = imported_data
            self._initialize_subjects()
            self.save_data()
            print(f"Data imported successfully from {filename}")
        except (IOError, csv.Error):
            print(
                "Error occurred while importing data. Make sure the file exists and contains valid CSV data."
            )

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
        print("12. Export data (CSV)")
        print("13. Import data (CSV)")
        print("14. Show topic history")
        print("15. Toggle music")
        print("16. Download music(YouTube)")
        print("17. Exit")

        choice = input("Enter your choice (1-16): ")

        if choice == "1":
            topic = input("Enter the topic name: ")
            subject = input("Enter the subject: ")
            srs.add_topic(topic, subject)
        elif choice == "2":
            topic = input("Enter the topic to review: ")
            srs.review_topic(topic)
        elif choice == "3":
            subject = input(
                "Enter a subject (or press Enter for all subjects): "
            ).strip()
            topics_to_review = srs.get_topics_to_review(subject if subject else None)
            if topics_to_review:
                print(f"Topics to review today (max {MAX_TOPICS_PER_DAY}):")
                for topic in topics_to_review:
                    print(
                        f"- {topic} (subject: {srs.data['topics'][topic]['subject']})"
                    )
            else:
                print("No topics to review today.")
        elif choice == "4":
            if srs.data["topics"]:
                print("All topics:")
                for topic, topic_data in srs.data["topics"].items():
                    print(
                        f"- {topic} (subject: {topic_data['subject']}, Next review: {topic_data['next_review']}, Difficulty: {topic_data['difficulty']}, Reviews: {topic_data['reviews']})"
                    )
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
            srs.export_to_csv()
        elif choice == "13":
            srs.import_from_csv()
        elif choice == "14":
            srs.show_topic_history()
        elif choice == "15":
            srs.toggle_music()
        elif choice == "16":
            srs.download_music()
        elif choice == "17":
            if srs.music_playing:
                srs.toggle_music()
            print("Exiting program. Bye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 15.")


if __name__ == "__main__":
    main()
