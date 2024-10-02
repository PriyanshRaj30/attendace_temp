import json
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['attendance_system']  # Replace with your database name
students_collection = db['students']  # Replace with your collection name

def update_json_from_mongo(json_file_path='data.json'):
    # Load the existing JSON file
    try:
        with open(json_file_path, 'r') as json_file:
            json_data = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        json_data = {}  # If the file doesn't exist or is corrupted, start with an empty dictionary

    # Query all data from MongoDB
    mongo_data = students_collection.find()
  
    # Update the JSON data based on MongoDB data
    for student in mongo_data:
        student_id = str(student['_id'])  # Use MongoDB's _id as the key in the JSON data

        # Remove the '_id' field from the document as it shouldn't go into the JSON
        student.pop('_id', None)

        # Update or add the student's data in the JSON structure
        json_data[student_id] = student

    # Save the updated data back to the JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)

    print("JSON file successfully updated based on MongoDB data.")


if __name__ == "__main__":
    update_json_from_mongo()