const express = require('express');
const path = require('path');
const app = express();
const mongoose = require("mongoose");
const ejsMate = require('ejs-mate');
const wrapAsync = require("./utils/wrapAsync.js");
const ExpressError = require("./utils/ExpressError.js");
const Student = require('./models/Student'); // Import the new Student model
const session = require("express-session");
const flash = require("connect-flash");
const User = require("./models/user.js");
const PDFDocument = require('pdfkit'); // PDF generation library
const { studentSchema } = require("./schema.js"); // Validation schema for students
const passport = require("passport");
const LocalStrategy = require("passport-local");
const { IsLoggedIn, savedRedirectUrl, isOwner } = require("./middleware.js");
const methodOverride = require("method-override");

app.use(express.static(path.join(__dirname, 'public')));
app.use(express.urlencoded({ extended: true }));
app.use(methodOverride('_method'));
app.use(express.json());

app.engine('ejs', ejsMate);

const MONGO_URL = "mongodb://127.0.0.1:27017/attendance_system";

main()
  .then(() => {
    console.log("Connected to DB");
  })
  .catch((err) => {
    console.log(err);
  });

async function main() {
  await mongoose.connect(MONGO_URL);
}

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

const validateStudent = (req, res, next) => {
  let { error } = studentSchema.validate(req.body); // Validate student fields
  if (error) {
    let errMsg = error.details.map((el) => el.message).join(",");
    throw new ExpressError(400, errMsg);
  } else {
    next();
  }
};

const sessionOptions = {
  secret: "mysupersecretcode",
  resave: false,
  saveUninitialized: true,
  cookie: {
    expires: Date.now() + 7 * 24 * 60 * 60 * 1000,
    maxAge: 7 * 24 * 60 * 60 * 1000,
    httpOnly: true,
  }
}

app.use(session(sessionOptions));
app.use(flash());

app.use(passport.initialize());
app.use(passport.session());
passport.use(new LocalStrategy(User.authenticate()));

passport.serializeUser(User.serializeUser());
passport.deserializeUser(User.deserializeUser());

app.use((req, res, next) => {
  res.locals.success = req.flash("success");
  res.locals.error = req.flash("error");
  res.locals.currUser = req.user;
  next();
});

app.get("/privacy", (req, res) => {
  res.render("listings/privacy.ejs");
});

app.get("/terms", (req, res) => {
  res.render("listings/terms.ejs");
});



// Signup and Login Routes
app.get("/signup", (req, res) => {
  res.render("users/signup.ejs");
});

app.post("/signup", async (req, res) => {
  try {
    let { username, email, password } = req.body;
    const newUser = new User({ email, username });
    const registeredUser = await User.register(newUser, password);
    req.login(registeredUser, (err) => {
      if (err) {
        return next(err);
      }
      req.flash("success", "Welcome to The Attendance System");
      res.redirect("/students");
    });
  } catch (err) {
    req.flash("error", err.message);
    res.redirect("/signup");
  }
});

app.get("/login", (req, res) => {
  res.render("users/login.ejs");
});

app.post("/login", savedRedirectUrl, passport.authenticate("local", { failureRedirect: "/login", failureFlash: true }), async (req, res) => {
  req.flash("success", "Welcome to The Attendance System");
  let redirectUrl = res.locals.redirectUrl || "/students";
  res.redirect(redirectUrl);
});

app.get("/logout", (req, res, next) => {
  req.logout((err) => {
    if (err) {
      return next(err);
    }
    req.flash("success", "You are Logged Out");
    res.redirect("/login");
  });
});

// Student Routes
app.get('/students', IsLoggedIn, async (req, res) => {
  const students = await Student.find({});
  res.render('listings/index', { students });
});



app.get("/students/:id", IsLoggedIn,wrapAsync(async (req, res) => {
  let { id } = req.params;
  const student = await Student.findById(id);
  if (!student) {
    req.flash("error", "Student you are requesting doesn't exist!!");
    return res.redirect("/students");
  }
  res.render("listings/show", { student });
}));

// Generate Student Report (PDF)
app.get('/students/:id/generate-report', IsLoggedIn, wrapAsync(async (req, res) => {
  const { id } = req.params;
  const student = await Student.findById(id);
  if (!student) {
    return res.status(404).send('Student not found');
  }

  const doc = new PDFDocument();
  res.setHeader('Content-disposition', 'attachment; filename=student-report.pdf');
  res.setHeader('Content-type', 'application/pdf');
  doc.pipe(res);

  // Add content to the PDF
  doc.fontSize(25).text('Student Report', { align: 'center' });
  doc.moveDown();
  doc.fontSize(20).text(`Name: ${student.name}`);
  doc.text(`Department: ${student.dept}`);
  doc.text(`Position: ${student.position}`); // Corrected "postion" to "position"
  doc.text(`Email: ${student.email}`);
  doc.text(`Starting Year: ${student.starting_year}`);
  doc.text(`Total Attendance: ${student.total_attendance}`);

  doc.end();
}));



app.get("/students/:id/edit", IsLoggedIn, async (req, res) => {
  let { id } = req.params;
  const student = await Student.findById(id);
  if (!student) {
    req.flash("error", "Student you are requesting doesn't exist!!");
    return res.redirect("/students");
  }
  res.render("listings/edit.ejs", { student });
});

app.put("/students/:id", IsLoggedIn, wrapAsync(async (req, res) => {
  let { id } = req.params;
  await Student.findByIdAndUpdate(id, req.body, { new: true });
  req.flash("success", "Student has been Updated Successfully!!");
  res.redirect("/students");
}));

app.delete("/students/:id", IsLoggedIn,  async (req, res) => {
  let { id } = req.params;
  let deletedStudent = await Student.findByIdAndDelete(id);
  req.flash("success", "Student has been Deleted Successfully!!");
  res.redirect("/students");
});

// Catch-all for 404
app.all("*", (req, res, next) => {
  next(new ExpressError(404, "Page Not Found"));
});

// Error handling middleware
app.use((err, req, res, next) => {
  let { statusCode = 500, message = "Something went wrong" } = err;
  res.status(statusCode).render("error.ejs", { message });
  console.log(err);
});

// Start the server
app.listen(4000, () => {
  console.log('Server running on http://localhost:4000');
});