import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
from pymongo import MongoClient
from datetime import datetime
import json
import AddDatatoDatabase
import dearpygui.dearpygui as dpg
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QLabel, QPushButton, QVBoxLayout, QMessageBox
import tkinter as tk
from tkinter import messagebox

  

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')  # Connect to the MongoDB server
db = client['attendance_system']  # Select the 'attendance_system' database
students_collection = db['students']  # Select the 'students' collection

def check_mongo_connection():
    try:
        # Try to connect to MongoDB
        client.admin.command('ping')
        print("MongoDB connection is active.")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        return False
    
# Initialize webcam
cap = cv2.VideoCapture(0)  # Open the default webcam (camera 0)
cap.set(3, 640)  # Set the width of the webcam frame
cap.set(4, 480)  # Set the height of the webcam frame


# Load the encoding file
print("Loading Encode File ...")
file = open('EncodeFile.p', 'rb')  # Open the encoding file in read-binary mode
encodeListKnownWithIds = pickle.load(file)  # Load the encodings and IDs from the file
file.close()  # Close the file
encodeListKnown, studentIds = encodeListKnownWithIds  # Split the loaded data into encodings and student IDs
print("Encode File Loaded")

# Define the accuracy threshold (e.g., 80%)
THRESHOLD = 0.4  # Face distance below this value means high confidence match



def log_event(message):
    with open("log.txt", "a") as log_file:
        log_file.write(f"{datetime.now()} - {message}\n")


# PyQt5 form to capture student details
class StudentForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Student Details")
        self.setGeometry(100, 100, 300, 300)

        # Create layout
        layout = QVBoxLayout()

        # Student ID
        self.student_id_label = QLabel("Enter Student ID:")
        self.student_id_input = QLineEdit()
        layout.addWidget(self.student_id_label)
        layout.addWidget(self.student_id_input)

        # Name
        self.name_label = QLabel("Enter Name:")
        self.name_input = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)

        # Major
        self.position_label = QLabel("Enter position:")
        self.position_input = QLineEdit()
        layout.addWidget(self.position_label)
        layout.addWidget(self.position_input)

        # Starting Year
        self.starting_year_label = QLabel("Enter Starting Year:")
        self.starting_year_input = QLineEdit()
        layout.addWidget(self.starting_year_label)
        layout.addWidget(self.starting_year_input)

        # Current Year
        self.dept_label = QLabel("Enter dept:")
        self.dept_input = QLineEdit()
        layout.addWidget(self.dept_label)
        layout.addWidget(self.dept_input)

        # Academic email
        self.email_label = QLabel("Enter email")
        self.email_input = QLineEdit()
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)

        # Submit Button
        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.submit_details)
        layout.addWidget(self.submit_button)

        # Set layout
        self.setLayout(layout)

    # Capture the entered details when the submit button is clicked
    def submit_details(self):
        student_id = self.student_id_input.text()
        name = self.name_input.text()
        position = self.position_input.text()
        dept = self.dept_input.text()
        email = self.email_input.text().upper()
        try:
            starting_year = int(self.starting_year_input.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Starting Year and Current Year must be integers!")
            return

        # standing = self.standing_input.text().upper()


        # Call the capture_new_person function with the form data
        capture_new_person(student_id, name, position, starting_year, dept, email)
        self.close()  # Close the form once details are submitted


# Function to capture the new person data
def capture_new_person(student_id, name, position, starting_year, dept, email):
    print("Press 'c' to capture an image of the new person...")

    # Ensure MongoDB connection is established
    if not check_mongo_connection():
        log_event("MongoDB connection failed.")
        return

    # Open video capture
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Failed to open camera.")
        log_event("Camera access failed.")
        return

    while True:
        success, img = cap.read()
        if not success:
            print("Failed to capture image from camera.")
            log_event("Image capture failed.")
            break

        cv2.imshow("New Person Capture", img)

        # Wait for the user to press 'c' to capture the image
        if cv2.waitKey(1) & 0xFF == ord('c'):
            # Define the path where the image will be saved (in Resources/Images folder)
            image_dir = 'Resources/Images'
            os.makedirs(image_dir, exist_ok=True)
            image_path = os.path.join(image_dir, f'{student_id}.jpg')

            # Save the captured image to the specified path
            cv2.imwrite(image_path, img)
            print(f"Image captured and saved as '{image_path}'")
            log_event(f"Image captured for {student_id}")
            break

    # Close the window after capturing the image
    cap.release()
    cv2.destroyWindow("New Person Capture")

    # Load and encode the captured image
    new_image = cv2.imread(image_path)
    new_image_rgb = cv2.cvtColor(new_image, cv2.COLOR_BGR2RGB)
    face_encodings = face_recognition.face_encodings(new_image_rgb)

    if face_encodings:
        encode = face_encodings[0]
        encodeListKnown.append(encode)  # Append new face encoding to the list
        studentIds.append(student_id)  # Add the student ID

        # Save the updated encodings and IDs to the file
        with open("EncodeFile.p", 'wb') as file:
            pickle.dump([encodeListKnown, studentIds], file)
        print("Face encoding and details saved!")

        # Insert the student's information into MongoDB
        student_data = {
            '_id': student_id,
            'name': name,
            'postion': position,
            'starting_year': starting_year,
            'dept': dept,
            'total_attendance': 1,  # Set initial attendance to 1
            'email': email,
            'last_attendance_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        students_collection.update_one({'_id': student_id}, {'$set': student_data}, upsert=True)
        print("Student details saved to MongoDB.")
        log_event(f"Student {student_id} saved to MongoDB.")

        # ------------------ Update the JSON file ------------------
        json_file_path = 'data.json'  # Path to your JSON file

        # Load existing data from the JSON file if it exists
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                try:
                    students_data = json.load(json_file)
                except json.JSONDecodeError:
                    students_data = {}  # Start with an empty dictionary if the file is empty or corrupted
        else:
            students_data = {}  # Start with an empty dictionary if the file doesn't exist

        # Add the new student's information to the dictionary
        student_json_data = {
            'name': name,
            'position': position,
            'starting_year': starting_year,
            'dept': dept,
            'total_attendance': 1,  # Set initial attendance to 1
            'email': email,
            'last_attendance_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        students_data[student_id] = student_json_data  # Use student_id as the key in the dictionary

        # Save the updated data back to the JSON file
        with open(json_file_path, 'w') as json_file:
            json.dump(students_data, json_file, indent=4)  # Use indent for better readability
        print("Student details updated in JSON file.")
        log_event(f"Student {student_id} details updated in JSON file.")
        # ------------------------------------------------------------
    else:
        print("No face found in the image. Please try again.")
        log_event("No face found during image processing.")


def main_loop():
    # Load background and mode images
    imgBackground = cv2.imread('Resources/background.png')  # Load the background image
    folderModePath = 'Resources/Modes'  # Path to the folder containing mode images
    modePathList = os.listdir(folderModePath)  # List all files in the mode folder
    imgModeList = [cv2.imread(os.path.join(folderModePath, path)) for path in modePathList]  # Load all mode images
    imgModeList = [cv2.resize(img, (414, 633)) for img in imgModeList]
   
   
   
    # Load the encoding file
    print("Loading Encode File ...")
    file = open('EncodeFile.p', 'rb')  # Open the encoding file in read-binary mode
    encodeListKnownWithIds = pickle.load(file)  # Load the encodings and IDs from the file
    file.close()  # Close the file
    encodeListKnown, studentIds = encodeListKnownWithIds  # Split the loaded data into encodings and student IDs
    print("Encode File Loaded")

    # Define the accuracy threshold (e.g., 80%)
    THRESHOLD = 0.4  # Face distance below this value means high confidence match

    # Initialize variables for the state of the system
    modeType = 3  # Start with a default mode type
    counter = 0  # Initialize a counter for controlling the timing of operations
    id = -1  # Placeholder for the recognized student ID
    imgStudent = []  # Placeholder for the student's image (not used here, but could be)

    while True:

        success, img = cap.read()  # Capture a frame from the webcam
        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)  # Resize the frame to 1/4 size for faster processing
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)  # Convert the frame from BGR (OpenCV format) to RGB (face_recognition format)

        faceCurFrame = face_recognition.face_locations(imgS)  # Detect face locations in the frame
        encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)  # Generate face encodings for detected faces

        # Place the webcam frame onto the background image
        imgBackground[162:162 + 480, 55:55 + 640] = img
        # Place the current mode image onto the background image
        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

        if faceCurFrame:  # If a face is detected
            for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):  # Loop over each detected face and its encoding
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace)  # Compare face encoding with known encodings
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)  # Calculate face distances to known encodings
                
                # Determine the index of the minimum face distance
                min_dis_index = np.argmin(faceDis)
                
                # Check if the minimum distance is below the threshold (high confidence match)
                if faceDis[min_dis_index] < THRESHOLD:
                    y1, x2, y2, x1 = faceLoc  # Get the face location coordinates
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4  # Scale the coordinates back up to the original frame size
                    bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1  # Define the bounding box for the detected face
                    imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)  # Draw the bounding box on the background image
                    id = studentIds[min_dis_index]  # Get the student ID corresponding to the recognized face

                    if counter == 0:  # If this is the first frame with a recognized face
                        cvzone.putTextRect(imgBackground, "Loading", (275, 400))  # Display "Loading" on the screen
                        cv2.imshow("Face Attendance", imgBackground)  # Show the image
                        cv2.waitKey(1)  # Wait for 1 millisecond
                        counter = 1  # Start the counter
                        modeType = 2  # Switch to the next mode

            if counter != 0:  # If the counter is active
                if counter == 1:  # On the first count
                    studentInfo = students_collection.find_one({'_id': id})  # Retrieve student info from the database using the ID
                    # print(studentInfo)
                    imgStudent = None  # MongoDB doesn't store images, so this is set to None

                    # Calculate the time since the last attendance was recorded
                    datetimeObject = datetime.strptime(studentInfo['last_attendance_time'], "%Y-%m-%d %H:%M:%S")
                    secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                    # print(secondsElapsed)

                    if secondsElapsed > 30:  # If more than 30 seconds have passed since the last attendance
                        students_collection.update_one(
                            {'_id': id},
                            {
                                '$inc': {'total_attendance': 1},  # Increment the attendance count
                                '$set': {'last_attendance_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  # Update the attendance time
                            }
                        )
                        AddDatatoDatabase.update_json_from_mongo()                        
                    else:  # If less than 30 seconds have passed
                        modeType = 0  # Set the mode to indicate a duplicate scan
                        counter = 0  # Reset the counter
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]  # Update the background with the new mode

                # if modeType != 3:  # If not in the duplicate scan mode
                #     if 10 < counter < 20000:  # Between counts 10 and 20
                #         modeType = 2  # Set the mode to display the student info


                #         # Center and display the student's name on the screen
                #         (w, h), _ = cv2.getTextSize(studentInfo['name'], cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                #         offset = (414 - w) // 2
                #         cv2.putText(imgBackground, str(studentInfo['name']), (808 + offset, 445),
                #                     cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                        if imgStudent is not None:  # If the student's image is available (not in this case)
                            imgBackground[175:175 + 216, 909:909 + 216] = imgStudent  # Display the student's image

                    counter += 1  # Increment the counter

                    if counter >= 20000:  # After the counter reaches 200000
                        counter = 0  # Reset the counter to 0
                        modeType = 3  # Set the mode to the default mode (0)
                        studentInfo = []  # Clear the student information
                        imgStudent = []  # Clear the student image
                        imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]  # Update the background to the default mode

        else:  # If no face is detected
            modeType = 3  # Set the mode to indicate no face detected (default mode)
            counter = 0  # Reset the counter

        if cv2.waitKey(100) & 0xFF == ord('q'):  # Check if 'q' is pressed to quit the loop
            break

        cv2.imshow("Face Attendance", imgBackground)  # Display the final composed image with background and information
        cv2.waitKey(1)  # Wait for 1 millisecond before the next loop iteration

    # Release resources
    cap.release()  # Release the webcam resource
    cv2.destroyAllWindows()  # Close all OpenCV windows
    


def on_choice1():
    # Here you would add the functionality for choice 1
    app = QApplication(sys.argv)
    form = StudentForm()  # Create and show the student form
    form.show()
    sys.exit(app.exec_())
def on_choice2():
    # Here you would add the functionality for choice 2
    main_loop()



# # Main loop for face recognition
if __name__ == '__main__':
#     print("1: Capture new person and save details")
#     print("2: Start face recognition attendance system")
#     choice = input("Enter your choice (1 or 2): ")

#     if choice == '1':
        # app = QApplication(sys.argv)
        # form = StudentForm()  # Create and show the student form
        # form.show()
        # sys.exit(app.exec_())
#     elif choice == '2':
        # main_loop()
#     else:
#         print("Invalid choice!")



# Create the main window
    root = tk.Tk()
    root.title("Attendance System")

    # Create and place the buttons
    btn_choice1 = tk.Button(root, text="1: Capture new person and save details", command=on_choice1)
    btn_choice1.pack(pady=10)

    btn_choice2 = tk.Button(root, text="2: Start face recognition attendance system", command=on_choice2)
    btn_choice2.pack(pady=10)

    # Run the application
    root.mainloop()