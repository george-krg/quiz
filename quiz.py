"""
An application for command line quiz testing and postgresql connection
It is assumed that there is locally a postgres database named quiz with a user postgress and a password - here ****
"""
import random
import psycopg2
from psycopg2 import Error
import os


# variables to control the flow
state = 0
test_topic = ""
test_topic_id = -1
score = -1
question_id = -1
connection = None
# here we hardcode the number of questions of each test
number_questions = 2
tablenames = []
test = []

# main execution loop

# given a state get a new input, execute any side effects and provide the new state

while state >= 0:
    if not connection:
        try:
            # Connect to an existing database
            connection = psycopg2.connect(
                user="postgres",
                password="****",
                host="127.0.0.1",
                port="5432",
                database="quiz",
            )

            # Create a cursor to perform database operations
            cursor = connection.cursor()
        except (Exception, Error) as error:
            print("Error while connecting to PostgreSQL", error)
            print("Please check PostgreSQL status and try later", error)
            state = -1

    os.system("cls")  # on windows
    # os.system('clear')  # on linux / os x

    if state == 0:
        # This is the initial display

        if len(tablenames) == 0:
            cursor.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
            for table in cursor.fetchall():
                topic = table[0].split("_")[0]
                tablenames.append(topic)

        print(
            f"There are currently the following {len(tablenames)} topics for testing:\n"
        )
        ind = 1
        for tablename in tablenames:
            print(f"{ind} - {tablename}\n")
            ind += 1

        sel = input(
            "If you want to be tested select the quiz number - To add a new topic a - To exit enter q\n"
        )

        if sel.isnumeric() and int(sel) >= 1 and int(sel) <= len(tablenames):
            test_topic_id = int(sel) - 1
            test_topic = tablenames[test_topic_id]
            state = 1
            score = 0
            question_id = 0

            # get the number of total questions
            sql = f"SELECT count(*) from {test_topic}_Quiz;"
            cursor.execute(sql)
            result = cursor.fetchone()
            num = int(result[0])

            # first create the random indexes of questions
            # Generate 5 random numbers between 10 and 30
            randomlist = random.sample(range(1, num + 1), number_questions)

            sql = f"SELECT * FROM {test_topic}_Quiz where id in {*randomlist,}"

            cursor.execute(sql)

            for row in cursor.fetchall():
                test.append(row)

            # finally change the state to display the questions
            state = 1

        elif sel == "a":
            state = 2
        elif sel == "q":
            state = -1
        else:
            print(f"The input {sel} is not accepted")

    elif state == 1:
        # Testing

        question = test[question_id][4]
        right = test[question_id][5]
        answers = test[question_id][5:10]

        # remove nulls
        answers = list(filter(None, answers))
        display = random.sample(answers, len(answers))

        # Print the quation and posible answers

        print(f"Question: {question}")
        print("Answers:")

        ind = 1
        for text in display:
            print(f"{ind} - {display[ind-1]}")
            ind += 1

        # Ask the user to select the right one
        accepted = False
        while not accepted:
            sel = input("Select the right one : ")
            if sel.isnumeric() and int(sel) >= 1 and int(sel) <= len(display):
                accepted = True
            else:
                print(f"The input {sel} is not accepted")

        # Check correctness

        if right == display[int(sel) - 1]:
            score += 1

        # increase question number

        question_id += 1

        # Check if test is completed

        if question_id == number_questions:
            # test complete  - Display score and reset values

            print(f"Your score is {score}/{number_questions}")
            input("To continue press any Enter")
            state = 0
            test_topic = ""
            test_topic_id = -1
            score = -1
            question_id = -1
            test = []

    elif state == 2:
        # Entering new topic/ questions

        topic = input("Give the topic subject : ")
        possname = topic + "_Quiz"
        exists = False

        # Check if topic already exists
        for tablename in tablenames:
            if topic == tablename:
                print("The table already exists - storing in this one")
                exists = True
                break

        if not exists:
            # first create the table
            sql = f"CREATE TABLE {possname} (id SERIAL PRIMARY KEY, topic VARCHAR(128) NOT NULL,subtopic VARCHAR(128), difficulty INT, question VARCHAR(512) NOT NULL,ans1 VARCHAR(512) NOT NULL, ans2 VARCHAR(512) NOT NULL, ans3 VARCHAR(512) NOT NULL, ans4 VARCHAR(512), ans5 VARCHAR(512), ans6 VARCHAR(512));"
            cursor.execute(sql)
            connection.commit()
            tablenames.append(topic)

        # Ask the user to enter the question

        entry = []
        entry.append(input("Give the module name :"))
        entry.append(input("Give the submodule name :"))
        # Ask the user to select the right one
        accepted = False
        while not accepted:
            diff = input(
                "Type difficulty level: 1- easy, 2: intermediate, 3-advanced :"
            )
            if diff == "1" or diff == "2" or diff == "3":
                accepted = True
            else:
                print(
                    f"The input {diff} is not accepted - Please select 1,2 or 3"
                )
        entry.append(diff)
        entry.append(input("Type your question:"))

        accepted = False
        while not accepted:
            num = input(
                "Select the number of possible answers - Minimum 3 - Maximum 6 :"
            )
            if num == "3" or num == "4" or num == "5" or num == "6":
                accepted = True
            else:
                print(
                    f"The input {num} is not accepted - Please select an integer between 3 and 6"
                )
        entry.append(input("Type the right answer first :"))
        ansstring = "ans1"
        for i in range(2, int(num) + 1):
            ansstring = ansstring + ",ans" + str(i)
            entry.append(input("Type a wrong answer to be displayed :"))

        sel = input("To save press s to return to main manu type r ")

        if sel == "s":
            # Store the entered values
            sql = f"insert into {possname} (topic, subtopic, difficulty, question, {ansstring}) VALUES {*entry,}"
            cursor.execute(sql)
            connection.commit()
            state = 0
        elif sel == "r":
            # Go to initial menu without storing
            state = 0
        else:
            state = 0

if state == -1:
    # Exiting

    print("Goodbye!\n")
    if connection:
        cursor.close()
        connection.close()
