import math
from datetime import datetime, timedelta, date
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

DATA_FILE = "spaced_repetition_data.json"
MAX_TOPICS_PER_DAY = 3


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
                "streak": {
                    "current": 0,
                    "longest": 0,
                    "last_review": None,
                    "last_homework": None,
                },
                "homework": {},
                "total_homework_completed": 0,
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
                "streak": {
                    "current": 0,
                    "longest": 0,
                    "last_review": None,
                    "last_homework": None,
                },
                "homework": {},
                "total_homework_completed": 0,
            }

    def _initialize_subjects(self):
        for topic, data in self.data["topics"].items():
            self.subjects[data["subject"]].add(topic)

    def save_data(self):
        with open(DATA_FILE, "w") as f:
            json.dump(
                {
                    "topics": self.data["topics"],
                    "total_reviews": self.data["total_reviews"],
                    "subjects": self.data["subjects"],
                    "streak": self.data["streak"],
                    "homework": self.homework,
                    "total_homework_completed": self.data.get(
                        "total_homework_completed", 0
                    ),
                },
                f,
                indent=2,
            )

    def add_topic(self, topic: str, subject: str):
        if topic not in self.data["topics"]:
            self.data["topics"][topic] = {
                "level": 0,
                "next_review": date.today().isoformat(),
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
        if topic not in self.data["topics"]:
            print(f"Topic '{topic}' not found.")
            return

        topic_data = self.data["topics"][topic]
        current_date = datetime.now()

        # Calculate review performance
        days_since_last_review = (
            current_date - datetime.fromisoformat(topic_data["next_review"])
        ).days
        early_review_factor = max(
            0, 1 - (days_since_last_review / 7)
        )  # Bonus for early review

        # Get user input for difficulty and confidence
        difficulty = self._get_user_rating(
            "Rate the difficulty (1-5, where 1 is easiest and 5 is hardest): "
        )
        confidence = self._get_user_rating(
            "Rate your confidence (1-5, where 1 is least confident and 5 is most confident): "
        )

        # Calculate review score
        review_score = (
            (6 - difficulty) + confidence
        ) / 2  # Average of inverted difficulty and confidence

        # Update topic data
        topic_data["level"] += review_score / 5  # Incremental level increase
        topic_data["reviews"] += 1
        topic_data["review_dates"].append(current_date.isoformat())

        # Calculate next review interval
        base_interval = math.pow(2, topic_data["level"])
        difficulty_factor = (6 - difficulty) / 3
        confidence_factor = confidence / 3
        early_review_bonus = 1 + early_review_factor

        next_interval = int(
            base_interval * difficulty_factor * confidence_factor * early_review_bonus
        )

        # Apply spaced repetition curve
        spaced_interval = self._apply_spaced_repetition_curve(
            next_interval, topic_data["reviews"]
        )

        # Set next review date
        topic_data["next_review"] = (
            current_date + timedelta(days=spaced_interval)
        ).isoformat()

        # Update topic difficulty
        topic_data["difficulty"] = self._update_topic_difficulty(
            topic_data["difficulty"], difficulty
        )

        self.data["total_reviews"] += 1
        self.update_streak()
        self.save_data()

        print(f"Reviewed '{topic}'. Next review in {spaced_interval} days.")

    def _get_user_rating(self, prompt: str) -> int:
        while True:
            try:
                rating = int(input(prompt))
                if 1 <= rating <= 5:
                    return rating
                else:
                    print("Please enter a number between 1 and 5.")
            except ValueError:
                print("Please enter a valid number.")

    def _apply_spaced_repetition_curve(self, interval: int, num_reviews: int) -> int:
        # Implement a custom spaced repetition curve
        if num_reviews <= 3:
            return min(interval, 7)  # Cap at 7 days for the first 3 reviews
        elif num_reviews <= 7:
            return min(interval, 14)  # Cap at 14 days for the next 4 reviews
        else:
            return min(interval, 60)  # Cap at 60 days for subsequent reviews

    def _update_topic_difficulty(
        self, current_difficulty: float, new_difficulty: int
    ) -> float:
        # Gradually adjust the topic's overall difficulty
        learning_rate = 0.2
        return current_difficulty + learning_rate * (
            new_difficulty - current_difficulty
        )

    def get_topics_to_review(self, subject: str = None) -> List[str]:
        today = date.today().isoformat()
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

            tomorrow = (date.today() + timedelta(days=1)).isoformat()
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
        topics_reviewed = sum(
            1 for topic in self.data["topics"].values() if topic["reviews"] > 0
        )

        print(f"\nProgress Report:")
        print(f"Total topics: {total_topics}")
        print(f"Topics reviewed at least once: {topics_reviewed}")
        print(f"Total reviews: {total_reviews}")
        print(f"Average reviews per topic: {total_reviews / total_topics:.2f}")
        print(f"Total homework assigned: {total_homework}")
        print(f"Total homework completed: {total_homework_completed}")
        print(
            f"Homework completion rate: {(total_homework_completed / total_homework * 100) if total_homework else 0:.2f}%"
        )

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
                "total_homework_completed": self.data.get(
                    "total_homework_completed", 0
                ),
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
        today = date.today()
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
        today = date.today().isoformat()
        yesterday = (date.today() - datetime.timedelta(days=1)).isoformat()

        if self.data["streak"]["last_review"] == yesterday or (
            homework and self.data["streak"]["last_homework"] == yesterday
        ):
            self.data["streak"]["current"] += 1
            self.data["streak"]["longest"] = max(
                self.data["streak"]["current"], self.data["streak"]["longest"]
            )
        elif self.data["streak"]["last_review"] != today and (
            not homework or self.data["streak"]["last_homework"] != today
        ):
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
        print(
            f"Last homework completion: {self.data['streak'].get('last_homework', 'Never')}"
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

    def add_homework(self, subject, description, due_date):
        homework_id = len(self.homework) + 1
        self.homework[homework_id] = {
            "subject": subject,
            "description": description,
            "due_date": due_date,
            "completed": False,
        }
        print(f"Homework added with ID: {homework_id}")
        self.save_data()

    def complete_homework(self, homework_id):
        if homework_id in self.homework:
            if not self.homework[homework_id]["completed"]:
                self.homework[homework_id]["completed"] = True
                self.homework[homework_id][
                    "completion_date"
                ] = date.today().isoformat()
                self.data["total_homework_completed"] = (
                    self.data.get("total_homework_completed", 0) + 1
                )
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
            print(
                f"ID: {id}, Subject: {hw['subject']}, Description: {hw['description']}, Due: {hw['due_date']}, Status: {status}"
            )
