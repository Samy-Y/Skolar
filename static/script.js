// script.js

function toggleStudentList() {
    const studentList = document.getElementById("studentList");
    const studentBtn = document.getElementById("toggleStudentsButton");
    if (studentList.style.display === "none") {
        studentList.style.display = "block";
        studentBtn.textContent = "Hide List of Students";
    } else {
        studentList.style.display = "none";
        studentBtn.textContent = "Show List of Students";
    }
}

function toggleTeacherList() {
    const teacherList = document.getElementById("teacherList");
    const teacherBtn = document.getElementById("toggleTeachersButton");
    if (teacherList.style.display === "none") {
        teacherList.style.display = "block";
        teacherBtn.textContent = "Hide List of Teachers";
    } else {
        teacherList.style.display = "none";
        teacherBtn.textContent = "Show List of Teachers";
    }
}

// Add smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();

        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Add form validation
document.addEventListener('DOMContentLoaded', (event) => {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});