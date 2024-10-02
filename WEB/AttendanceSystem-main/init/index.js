const mongoose = require("mongoose");
const initData = require("./data.js"); // Ensure this points to your student data file
const Student = require("../models/Student.js"); // Make sure the Student schema is correctly imported

// Establish the MongoDB connection
main()
    .then(() => {
        console.log("Connection Successful");
    })
    .catch((err) => {
        console.log(err);
    });

async function main() {
    await mongoose.connect('mongodb://127.0.0.1:27017/Student'); // Changed to Student database
}

// Function to initialize the database
const initDB = async () => {
    try {
        await Student.deleteMany({}); // Clear existing records
        // Directly insert data without adding owner field
        await Student.insertMany(initData.data); // Inserting student data
        console.log("Data was initialized successfully");
    } catch (err) {
        console.error("Error initializing data: ", err);
    }
};

// Initialize the database with student data
initDB();