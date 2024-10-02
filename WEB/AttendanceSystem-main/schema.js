const Joi = require('joi');

module.exports.employeeSchema = Joi.object({
    employeeId: Joi.string().required(), // Employee ID is required
    name: Joi.string().required(), // Employee's name
    department: Joi.string().required(), // Employee's department
    position: Joi.string().required(), // Employee's position
    dateOfJoining: Joi.date().required(), // Date the employee joined
    totalAttendance: Joi.number().default(0).min(0), // Total attendance, defaults to 0
    lastAttendanceTime: Joi.date().default(Date.now) // Last attendance time, defaults to now
}).required();