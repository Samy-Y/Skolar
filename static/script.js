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

function seePass() {
    const passField = document.getElementById("password");
    if (passField.getAttribute("type") === "password") {
        passField.setAttribute("type", "text");
    } else {
        passField.setAttribute("type", "password");
    }
}

function hidePass(){
    const passField = document.getElementById("password");
    passField.setAttribute("type") = "password"
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

// ——————————————————————————————————————————————————
// TextScramble
// ——————————————————————————————————————————————————

class TextScramble {
    constructor(el) {
      this.el = el
      this.chars = '!<>-_\\/[]{}—=+*^?#________'
      this.update = this.update.bind(this)
    }
    setText(newText) {
      const oldText = this.el.innerText
      const length = Math.max(oldText.length, newText.length)
      const promise = new Promise((resolve) => this.resolve = resolve)
      this.queue = []
      for (let i = 0; i < length; i++) {
        const from = oldText[i] || ''
        const to = newText[i] || ''
        const start = Math.floor(Math.random() * 15)
        const end = start + Math.floor(Math.random() * 15)
        this.queue.push({ from, to, start, end })
      }
      cancelAnimationFrame(this.frameRequest)
      this.frame = 0
      this.update()
      return promise
    }
    update() {
      let output = ''
      let complete = 0
      for (let i = 0, n = this.queue.length; i < n; i++) {
        let { from, to, start, end, char } = this.queue[i]
        if (this.frame >= end) {
          complete++
          output += to
        } else if (this.frame >= start) {
          if (!char || Math.random() < 0.28) {
            char = this.randomChar()
            this.queue[i].char = char
          }
          output += `<span class="dud">${char}</span>`
        } else {
          output += from
        }
      }
      this.el.innerHTML = output
      if (complete === this.queue.length) {
        this.resolve()
      } else {
        this.frameRequest = requestAnimationFrame(this.update)
        this.frame++
      }
    }
    randomChar() {
      return this.chars[Math.floor(Math.random() * this.chars.length)]
    }
  }
  
  // ——————————————————————————————————————————————————
  // Example
  // ——————————————————————————————————————————————————
  
  const phrases = [
    'Skolar',
    'Leave pen and paper behind',
    'Manage your school efficiently'
    
  ]
  
  const el = document.querySelector('.text')
  const fx = new TextScramble(el)
  
  let counter = 0
  const next = () => {
    fx.setText(phrases[counter]).then(() => {
      setTimeout(next, 2000)
    })
    counter = (counter + 1) % phrases.length

  }
  
  next()