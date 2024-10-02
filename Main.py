import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')  # Connect to the MongoDB server
db = client['attendance_system']  # Select the 'attendance_system' database
students_collection = db['students']  # Select the 'students' collection

# Initialize webcam
cap = cv2.VideoCapture(0)  # Open the default webcam (camera 0)
cap.set(3, 640)  # Set the width of the webcam frame
cap.set(4, 480)  # Set the height of the webcam frame

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
                print(studentInfo)
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