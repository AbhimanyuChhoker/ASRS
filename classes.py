import math
from datetime import datetime, timedelta, date
import json
import time
import random
import os
from typing import Dict, List, Any, Optional
from collections import defaultdict
import pygame
from pygame import mixer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
import io
import threading
import logging
import yaml

# Load configuration
with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

DATA_FILE = config['data_file']
MAX_TOPICS_PER_DAY = config['max_topics_per_day']

# Set up logging
logging.basicConfig(filename='srs.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DataManager:
    @staticmethod
    def load_data() -> Dict[str, Any]:
        if not os.path.exists(DATA_FILE):
            return DataManager._create_default_data()

        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                DataManager._validate_data_structure(data)
                return data
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            logging.error(f"Error loading data file: {e}")
            return DataManager._create_default_data()

    @staticmethod
    def save_data(data: Dict[str, Any]) -> None:
        try:
            backup_file = f"{DATA_FILE}.bak"
            if os.path.exists(DATA_FILE):
                os.rename(DATA_FILE, backup_file)
            
            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=2)

            if os.path.exists(backup_file):
                os.remove(backup_file)

        except (IOError, PermissionError) as e:
            logging.error(f"Error saving data file: {e}")
            if os.path.exists(backup_file):
                os.rename(backup_file, DATA_FILE)

    @staticmethod
    def _create_default_data() -> Dict[str, Any]:
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

    @staticmethod
    def _validate_data_structure(data: Dict[str, Any]) -> None:
        required_keys = ["topics", "total_reviews", "subjects", "streak", "homework", "total_homework_completed"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Invalid data structure: missing '{key}' key")

class PomodoroTimer:
    def __init__(self, work_duration: int = 25, break_duration: int = 5):
        self.work_duration = work_duration * 60
        self.break_duration = break_duration * 60
        self.timer_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.is_break = False

    def start(self) -> None:
        self.is_running = True
        self.timer_thread = threading.Thread(target=self._run_timer)
        self.timer_thread.start()

    def stop(self) -> None:
        self.is_running = False
        if self.timer_thread:
            self.timer_thread.join()

    def _run_timer(self) -> None:
        while self.is_running:
            if not self.is_break:
                logging.info("Work session started. Focus for 25 minutes!")
                self._countdown(self.work_duration)
            else:
                logging.info("Break time! Take a 5-minute break.")
                self._countdown(self.break_duration)

            if self.is_running:
                self.is_break = not self.is_break

    def _countdown(self, duration: int) -> None:
        start_time = time.time()
        while time.time() - start_time < duration and self.is_running:
            remaining = duration - int(time.time() - start_time)
            mins, secs = divmod(remaining, 60)
            timer = f"{mins:02d}:{secs:02d}"
            print(f"\rTime remaining: {timer}", end="", flush=True)
            time.sleep(1)
        print()

    def get_state(self) -> str:
        return "break" if self.is_break else "work"

class SpacedRepetitionSystem:
    def __init__(self):
        self.data: Dict[str, Any] = DataManager.load_data()
        self.subjects: Dict[str, set] = defaultdict(set)
        self._initialize_subjects()
        self.homework: Dict[int, Dict[str, Any]] = self.data.get("homework", {})
        pygame.init()
        mixer.init()
        self.music_playing = False

    def _initialize_subjects(self) -> None:
        for topic, data in self.data["topics"].items():
            self.subjects[data["subject"]].add(topic)

    def save_data(self) -> None:
        DataManager.save_data(self.data)

    def add_topic(self, topic: str, subject: str) -> None:
        topic = topic.strip()
        subject = subject.strip()
        if not topic or not subject:
            logging.warning("Topic and subject cannot be empty.")
            return
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
            logging.info(f"Added topic: {topic} (subject: {subject})")
        else:
            logging.warning(f"Topic '{topic}' already exists.")

    def review_topic(self, topic: str) -> None:
        topic = topic.strip()
        if not topic:
            logging.warning("Topic name cannot be empty.")
            return
        if topic not in self.data["topics"]:
            logging.warning(f"Topic '{topic}' not found.")
            return

        topic_data = self.data["topics"][topic]
        current_date = datetime.now()

        days_since_last_review = (
            current_date - datetime.fromisoformat(topic_data["next_review"])
        ).days
        early_review_factor = max(
            0, 1 - (days_since_last_review / 7)
        )

        difficulty = self._get_user_rating(
            "Rate the difficulty (1-5, where 1 is easiest and 5 is hardest): "
        )
        confidence = self._get_user_rating(
            "Rate your confidence (1-5, where 1 is least confident and 5 is most confident): "
        )

        review_score = (
            (6 - difficulty) + confidence
        ) / 2

        topic_data["level"] += review_score / 5
        topic_data["reviews"] += 1
        topic_data["review_dates"].append(current_date.isoformat())

        base_interval = math.pow(2, topic_data["level"])
        difficulty_factor = (6 - difficulty) / 3
        confidence_factor = confidence / 3
        early_review_bonus = 1 + early_review_factor

        next_interval = int(
            base_interval * difficulty_factor * confidence_factor * early_review_bonus
        )

        spaced_interval = self._apply_spaced_repetition_curve(
            next_interval, topic_data["reviews"]
        )

        topic_data["next_review"] = (
            current_date + timedelta(days=spaced_interval)
        ).isoformat()

        topic_data["difficulty"] = self._update_topic_difficulty(
            topic_data["difficulty"], difficulty
        )

        self.data["total_reviews"] += 1
        self.update_streak()
        self.save_data()

        logging.info(f"Reviewed '{topic}'. Next review in {spaced_interval} days.")

    def _get_user_rating(self, prompt: str) -> int:
        while True:
            try:
                rating = input(prompt).strip()
                if not rating:
                    logging.warning("Please enter a number between 1 and 5.")
                    continue
                rating = int(rating)
                if 1 <= rating <= 5:
                    return rating
                else:
                    logging.warning("Please enter a number between 1 and 5.")
            except ValueError:
                logging.warning("Please enter a valid number.")

    def _apply_spaced_repetition_curve(self, interval: int, num_reviews: int) -> int:
        if num_reviews <= 3:
            return min(interval, 7)
        elif num_reviews <= 7:
            return min(interval, 14)
        else:
            return min(interval, 60)

    def _update_topic_difficulty(
        self, current_difficulty: float, new_difficulty: int
    ) -> float:
        learning_rate = 0.2
        return current_difficulty + learning_rate * (
            new_difficulty - current_difficulty
        )

    def get_topics_to_review(self, subject: Optional[str] = None) -> List[str]:
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
            logging.info(f"Rescheduled {len(topics_for_tomorrow)} topic(s) for tomorrow.")
            return topics_for_today
        else:
            return sorted_topics

    def show_progress(self) -> None:
        total_topics = len(self.data["topics"])
        total_reviews = self.data["total_reviews"]
        total_homework = len(self.homework)
        total_homework_completed = self.data.get("total_homework_completed", 0)
        topics_reviewed = sum(
            1 for topic in self.data["topics"].values() if topic["reviews"] > 0
        )

        logging.info(f"\nProgress Report:")
        logging.info(f"Total topics: {total_topics}")
        logging.info(f"Topics reviewed at least once: {topics_reviewed}")
        logging.info(f"Total reviews: {total_reviews}")
        logging.info(f"Average reviews per topic: {total_reviews / total_topics:.2f}")
        logging.info(f"Total homework assigned: {total_homework}")
        logging.info(f"Total homework completed: {total_homework_completed}")
        logging.info(
            f"Homework completion rate: {(total_homework_completed / total_homework * 100) if total_homework else 0:.2f}%"
        )

        logging.info("\nTop 5 most reviewed topics:")
        sorted_topics = sorted(
            self.data["topics"].items(), key=lambda x: x[1]["reviews"], reverse=True
        )[:5]
        for topic, topic_data in sorted_topics:
            logging.info(
                f"- {topic} ({topic_data['subject']}): {topic_data['reviews']} reviews"
            )

    def study_session(self) -> None:
        try:
            duration = int(
                input("Enter the duration of the study session in minutes: ")
            )
        except ValueError:
            logging.warning("Please enter a valid number of minutes.")
            return

        subject = input(
            "Enter a subject to focus on (or press Enter for all subjects): "
        ).strip()
        if subject and subject not in self.subjects:
            logging.warning(f"Subject '{subject}' not found.")
            return

        play_music = (
            input("Do you want to play music for this study session? (y/n): ")
            .lower()
            .strip()
        )
        if play_music == "y":
            self.toggle_music()

        pomodoro = PomodoroTimer()
        pomodoro.start()

        end_time = time.time() + duration * 60
        topics_reviewed = 0

        while time.time() < end_time:
            if pomodoro.get_state() == "work":
                due_topics = self.get_topics_to_review(subject)
                if not due_topics:
                    logging.info("No more topics to review. Session ended early.")
                    break

                topic = random.choice(due_topics)
                logging.info(f"\nTime remaining: {int((end_time - time.time()) / 60)} minutes")
                logging.info(
                    f"Review topic: {topic} (subject: {self.data['topics'][topic]['subject']})"
                )
                input("Press Enter when you're ready to rate the difficulty...")
                self.review_topic(topic)
                topics_reviewed += 1
            else:
                logging.info("It's break time! Take a moment to relax.")
                time.sleep(10)

            if time.time() >= end_time:
                logging.info("\nStudy session time is up!")
                break

        pomodoro.stop()

        if self.music_playing:
            self.toggle_music()

        logging.info(
            f"\nSession ended. You reviewed {topics_reviewed} topic(s) in this session."
        )

    def toggle_music(self) -> None:
        if self.music_playing:
            mixer.music.stop()
            self.music_playing = False
            logging.info("Music stopped")
        else:
            music_dir = "music"
            if not os.path.exists(music_dir):
                logging.info("Music directory does not exist. Creating...")
                os.mkdir(music_dir)
            music_files = [f for f in os.listdir(music_dir) if f.endswith(".mp3")]
            if music_files:
                music_file = os.path.join(music_dir, random.choice(music_files))
                mixer.music.load(music_file)
                mixer.music.play(-1)
                self.music_playing = True
                logging.info("Music started.")
            else:
                logging.warning("No music files available.")

    def show_subjects(self) -> None:
        logging.info("\nSubjects:")
        for subject, topics in self.subjects.items():
            logging.info(f"- {subject}: {len(topics)} topics")

    def export_data(self) -> None:
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
                logging.info(f"Data exported successfully to {filename}")
            except IOError as e:
                logging.error(f"Error occurred while exporting data: {e}")

    def import_data(self) -> None:
        filename = input("Enter the filename to import data from: ")
        try:
            with open(filename, "r") as f:
                imported_data = json.load(f)
            if not all(
                key in imported_data for key in ["topics", "total_reviews", "subjects"]
            ):
                logging.error("Invalid data format in the import file.")
                return
            self.data = imported_data
            self._initialize_subjects()
            self.save_data()
            logging.info(f"Data imported successfully from {filename}")
        except (IOError, json.JSONDecodeError) as e:
            logging.error(f"Error occurred while importing data: {e}")

    def show_weekly_progress(self) -> None:
        today = date.today()
        week_ago = today - timedelta(days=7)
        daily_reviews = {
            (today - timedelta(days=i)).isoformat(): 0 for i in range(7)
        }

        for topic in self.data["topics"].values():
            for review_date in topic.get("review_dates", []):
                if review_date in daily_reviews:
                    daily_reviews[review_date] += 1

        logging.info("\nWeekly Progress (Reviews per day):")
        for date, count in daily_reviews.items():
            bar = "#" * count
            logging.info(f"{date}: {bar} ({count})")

    def update_streak(self, homework: bool = False) -> None:
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

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

    def show_streak(self) -> None:
        logging.info(f"\nCurrent streak: {self.data['streak']['current']} days")
        logging.info(f"Longest streak: {self.data['streak']['longest']} days")
        logging.info(f"Last review: {self.data['streak']['last_review']}")
        logging.info(
            f"Last homework completion: {self.data['streak'].get('last_homework', 'Never')}"
        )

    def show_topic_history(self) -> None:
        topic = input("Enter the topic name to show history: ")
        if topic in self.data["topics"]:
            topic_data = self.data["topics"][topic]
            logging.info(f"\nReview history for '{topic}':")
            logging.info(f"Subject: {topic_data['subject']}")
            logging.info(f"Current level: {topic_data['level']}")
            logging.info(f"Total reviews: {topic_data['reviews']}")
            logging.info(f"Current difficulty: {topic_data['difficulty']}")
            logging.info(f"Next review: {topic_data['next_review']}")

            if "review_dates" in topic_data:
                logging.info("\nPast reviews:")
                for date in topic_data["review_dates"]:
                    logging.info(f"- {date}")
            else:
                logging.info("\nNo past review data available.")
        else:
            logging.warning(f"Topic '{topic}' not found.")

    def add_homework(self, subject: str, description: str, due_date: str) -> None:
        subject = subject.strip()
        description = description.strip()
        due_date = due_date.strip()
        if not subject or not description or not due_date:
            logging.warning("Subject, description, and due date cannot be empty.")
            return
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            logging.warning("Invalid date format. Please use YYYY-MM-DD.")
            return
        homework_id = len(self.homework) + 1
        self.homework[homework_id] = {
            "subject": subject,
            "description": description,
            "due_date": due_date,
            "completed": False,
        }
        logging.info(f"Homework added with ID: {homework_id}")
        self.save_data()

    def complete_homework(self, homework_id: int) -> None:
        if homework_id in self.homework:
            if not self.homework[homework_id]["completed"]:
                self.homework[homework_id]["completed"] = True
                self.homework[homework_id]["completion_date"] = date.today().isoformat()
                self.data["total_homework_completed"] = (
                    self.data.get("total_homework_completed", 0) + 1
                )
                self.update_streak(homework=True)
                logging.info(f"Homework (ID: {homework_id}) marked as completed.")
                self.save_data()
            else:
                logging.info(f"Homework (ID: {homework_id}) was already completed.")
        else:
            logging.warning(f"Homework with ID {homework_id} not found.")

    def show_homework(self) -> None:
        if not self.homework:
            logging.info("No homework assigned.")
            return

        logging.info("\nCurrent Homework:")
        for id, hw in self.homework.items():
            status = "Completed" if hw["completed"] else "Pending"
            logging.info(
                f"ID: {id}, Subject: {hw['subject']}, Description: {hw['description']}, Due: {hw['due_date']}, Status: {status}"
            )

    def edit_homework(self, homework_id: int) -> None:
        if homework_id in self.homework:
            homework = self.homework[homework_id]
            logging.info(f"\nCurrent homework details:")
            logging.info(f"Subject: {homework['subject']}")
            logging.info(f"Description: {homework['description']}")
            logging.info(f"Due date: {homework['due_date']}")
            logging.info(f"Completed: {homework['completed']}")

            new_subject = input(
                "Enter new subject (or press Enter to keep current): "
            ).strip()
            new_description = input(
                "Enter new description (or press Enter to keep current): "
            ).strip()
            new_due_date = input(
                "Enter new due date (YYYY-MM-DD) (or press Enter to keep current): "
            ).strip()
            new_completed = (
                input("Is it completed? (y/n) (or press Enter to keep current): ")
                .strip()
                .lower()
            )

            if new_subject:
                homework["subject"] = new_subject
            if new_description:
                homework["description"] = new_description
            if new_due_date:
                try:
                    datetime.strptime(new_due_date, "%Y-%m-%d")
                    homework["due_date"] = new_due_date
                except ValueError:
                    logging.warning("Invalid date format. Due date not updated.")
            if new_completed in ["y", "n"]:
                homework["completed"] = new_completed == "y"

            logging.info("Homework updated successfully.")
            self.save_data()
        else:
            logging.warning(f"Homework with ID {homework_id} not found.")

    def generate_progress_graph(self) -> io.BytesIO:
        topics = list(self.data["topics"].keys())
        reviews = [topic_data["reviews"] for topic_data in self.data["topics"].values()]

        plt.figure(figsize=(10, 6))
        plt.bar(topics, reviews)
        plt.title("Topic Review Frequency")
        plt.xlabel("Topics")
        plt.ylabel("Number of Reviews")
        plt.xticks(rotation=90)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()  # Close the figure to free up memory
        return buf