# ASRS - Abhimanyu's Spaced Revision Scheduler

ASRS is a Python-based spaced repetition system designed to help users manage and review topics across various subjects. It uses a spaced repetition algorithm to schedule reviews and includes features like study sessions, homework management, and progress tracking.

## Main Components

### 1. SpacedRepetitionSystem Class (classes.py)

The core of the system, handling data management, topic reviews, and various user interactions.

Key methods:
- `__init__()`: Initializes the system, loading existing data or creating new data structures.
- `add_topic(topic, subject)`: Adds a new topic to the system.
- `review_topic(topic)`: Allows users to review a topic and updates its review schedule.
- `get_topics_to_review(subject=None)`: Returns topics due for review, optionally filtered by subject.
- `study_session()`: Manages a timed study session with topic reviews.
- `show_progress()`: Displays overall progress statistics.
- `add_homework(subject, description, due_date)`: Adds new homework assignments.
- `complete_homework(homework_id)`: Marks homework as completed.

### 2. Main Script (main.py)

Provides the user interface for interacting with the SpacedRepetitionSystem.

Key functions:
- `initialize_topics(srs)`: Adds initial topics to the system.
- `main()`: The main loop handling user input and calling appropriate methods.

## Features

1. Topic Management: Add, review, and track progress of study topics.
2. Spaced Repetition: Automatically schedules topic reviews based on difficulty and previous review performance.
3. Study Sessions: Timed study sessions with randomly selected due topics.
4. Progress Tracking: View overall progress, weekly progress, and topic history.
5. Homework Management: Add, complete, and track homework assignments.
6. Data Import/Export: Save and load system data in JSON format.
7. Music Integration: Play background music during study sessions.
8. Streak Tracking: Monitor daily study streaks.

## Usage

Run `main.py` to start the program. Users can interact with the system through a command-line interface, choosing options from a menu to perform various actions like adding topics, reviewing, starting study sessions, and managing homework.

## Data Storage

The system uses a JSON file (`spaced_repetition_data.json`) to persist data between sessions, storing information about topics, reviews, homework, and user progress.

## Dependencies

- Python 3.x
- Pygame (for music playback)
- PyTube (for potential YouTube integration, though not actively used in the provided code)

## Notes

- The system includes a predefined list of initial topics (`INITIAL_TOPICS`) covering various subjects.
- There's a daily limit (`MAX_TOPICS_PER_DAY`) on the number of topics scheduled for review.
- The spaced repetition algorithm adjusts review intervals based on user-rated difficulty and the number of successful reviews.

This documentation provides an overview of the ASRS system. For more detailed information on specific functions or usage, refer to the comments within the code or reach out to the developer.