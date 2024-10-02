import cv2
import face_recognition
import pickle
import os
from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['attendance_system']  # Replace with your database name
students_collection = db['students']  # Replace with your collection name
    
# Importing student images
folderpath = 'Resources/Images'
# folderpath = 'testImg/Images'
pathList = os.listdir(folderpath)
imgList = []
studentIds = []
  
for path in pathList:
    # Check if the file is an image (based on file extension)
    if path.lower().endswith(('.png', '.jpg', '.jpeg')):
        img_path = os.path.join(folderpath, path)
        img = cv2.imread(img_path)
        if img is None:
            print(f"Warning: Unable to load image at {img_path}")
        else:
            imgList.append(img)
            studentIds.append(os.path.splitext(path)[0])
    
# print(studentIds)

def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

print("Encoding Started ...")
try:
    encodeListKnown = findEncodings(imgList)
    encodeListKnownWithIds = [encodeListKnown, studentIds]
    print("Encoding Complete")

    with open("EncodeFile.p", 'wb') as file:
        pickle.dump(encodeListKnownWithIds, file)
    print("File Saved")
except Exception as e:
    print(f"Error occurred: {e}")