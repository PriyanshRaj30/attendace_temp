const Student = require("./models/Student"); // Update to import the Student model

module.exports.IsLoggedIn = (req, res, next) => {
    if (!req.isAuthenticated()) {
        req.session.redirectUrl = req.originalUrl;
        req.flash("error", "You must be logged in to perform this operation");
        return res.redirect("/login");
    }
    next();
}

module.exports.savedRedirectUrl = (req, res, next) => {
    if (req.session.redirectUrl) {
        res.locals.redirectUrl = req.session.redirectUrl;
    }
    next();
}

module.exports.isOwner = async (req, res, next) => {
    let { id } = req.params; // Extracting `id` from route parameters
    let student;

    try {
        student = await Student.findById(id); // Fetching the student by ID

        // Check if the student exists
        if (!student) {
            req.flash("error", "Student not found");
            return res.redirect("/students"); // Redirect to students page if not found
        }

        // Checking if the current user is the owner of the student
        if (!student.owner.equals(res.locals.currUser._id)) {
            req.flash("error", "You don't have permission to access this!");
            return res.redirect(`/students/${id}`); // Redirect to the specific student's page
        }
    } catch (err) {
        // Handle potential errors from the database query
        req.flash("error", "An error occurred while checking ownership.");
        console.error(err); // Log the error for debugging
        return res.redirect("/students");
    }
    
    next();
};