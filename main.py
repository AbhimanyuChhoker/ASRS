import random

level0 = ["Road Not Taken", "Wind", "Reported Speech", "The Fun They Had", "The Lost Child", "Diary Entry", "Integrated Grammer", "The Sound Of Music PT.1", "The Sound Of Music PT.2", "The Adventures Of Toto", "Cells: The Fundamental Units of Life", "Matter in Our Surroundings", "Is Matter Around Us Pure?", "Motion", "Force and Laws of Motion", "What is Democracy? Why Democracy?", "Electoral Politics", "The Story of Village Palampur", "People as a Resource", "The Story of Village Palampur", "People as a Resource", "Lektion 1", "Introduction to Python", "Entrepreneurial Skills-I", "The French Revolution"]
level1 = [] # Scheduled to be revised in one day
level2 = [] # Scheduled to be revised in three days
level3 = [] # Scheduled to be revised in one week
level4 = [] # Scheduled to be revised in one month
level5 = [] # Scheduled to be revised in three months
levels = {
    0: level0,
    1: level1,
    2: level2,
    3: level3,
    4: level4,
    5: level5
}

print("REVISION SCHEDULER")
while True:
    cmd = str(input(">>>"))
    cmd = cmd.lower()
    if cmd == "help":
        print("""
              'Add' adds a new topic
              'Remove' removes a topic
              'List' lists all topics in a specific level
              'Create todo' gives todays topics
              'Start' starts a study session
              'Exit' exits the program
              """)
    elif cmd == "add":
        topic = str(input("Enter topic name: "))
        level0.append(topic)
    elif cmd == "remove":
        topic = input("Enter topic name: ")
        topic_level = int(input("Enter topic level: "))
        if topic_level in levels:
            levels[topic_level].remove(topic)
        else:
            print("Invalid topic level.")
    elif cmd == "list":
        level = int(input("Enter topic level: "))
        if level in levels:
            print(f"Level {level}:")
            for topic in levels[level]:
                print(topic)
        else:
            print("Invalid topic level.")
    elif cmd == "create todo":
        pass
        # TODO: Complete this and use the datetime module for scheduling
    elif cmd == "exit":
        print("Exiting program. Bye!")
        break