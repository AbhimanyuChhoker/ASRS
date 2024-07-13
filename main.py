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

MAX_TOPICS_PER_DAY = 3

from classes import SpacedRepetitionSystem


def initialize_topics(srs):
    for topic, subject in INITIAL_TOPICS:
        srs.add_topic(topic.lower(), subject.lower())
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
