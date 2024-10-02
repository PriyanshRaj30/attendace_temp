import json
from pymongo import MongoClient
  
# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['attendance_system']  # Replace with your database name
students_collection = db['students']  # Replace with your collection name

def update_mongo_from_json(json_file_path='d.json'):
    # Load the JSON data
    try:
        with open(json_file_path, 'r') as json_file:
            json_data = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Error: JSON file not found or is corrupted.")
        return


    # Iterate through each entry in the JSON data
    for student_id, student_data in json_data.items():
        # Convert student_id to the correct type if necessary
        # In MongoDB, _id might be ObjectId, integer, or string. Adjust accordingly.
        student_id = str(student_id)

        # Upsert (update if exists, insert if it doesn't) the document in MongoDB
        students_collection.update_one(
            {'_id': student_id},  # Match document by _id (converted from JSON key)
            {'$set': student_data},  # Update document with new data from JSON
            upsert=True  # Insert if no matching document exists
        )

    print("MongoDB successfully updated with data from JSON.")


if __name__ == "__main__":
    update_mongo_from_json()