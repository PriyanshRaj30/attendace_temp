const mongoose = require('mongoose');

const studentSchema = new mongoose.Schema({
  _id: { type: String, required: true },
  dept: { type: String, required: true },
  email: { type: String, required: true },
  last_attendance_time: { type: String, required: true },
  name: { type: String, required: true },
  postion: { type: String, required: true },
  starting_year: { type: Number, required: true },
  total_attendance: { type: Number, required: true },
});

module.exports = mongoose.model('Student', studentSchema);