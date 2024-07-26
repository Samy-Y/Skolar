function toggleStudentList() {
    const studentList = document.getElementById("studentList");
    const studentBtn = document.getElementById("toggleStudentsButton")
    if (studentList.style.display === "none") {
        studentList.style.display = "block"; // Show the table
        studentBtn.innerHTML = "Hide List of Students"
    } else {
        studentList.style.display = "none"; // Hide the table
        studentBtn.innerHTML = "Show List of Students"
    }
}

function toggleTeacherList() {
    const teacherList = document.getElementById("teacherList");
    const teacherBtn = document.getElementById("toggleTeachersButton")
    if (teacherList.style.display === "none") {
        teacherList.style.display = "block"; // Show the table
        teacherBtn.innerHTML = "Hide List of Teachers"
    } else {
        teacherList.style.display = "none"; // Hide the table
        teacherBtn.innerHTML = "Show List of Teachers"
    }
}