# SKOLAR
**Samy Y, 2024**

**SKOLAR** is an innovative CMS which allows schools to efficiently manage and distribute their resources. This project was created in under 10 hours for the 2024 Algorithmics Hackathon. Skolar relies on Flask and SQLite on the backend, and vanilla HTML/CSS/JS on the frontend. This was my first time interacting with Flask and SQL databases.

![](https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExdGU4ZHc1ajBwZzdud3pmNGIwazFpanpleG50bzZ4Y2t0bnI5dWoxeCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3KPMtFHoACj4dBaE0H/giphy.gif)

## Quick features overview

### Blog
Skolar comes with a pre-installed blog system allowing educational institutions to efficiently manage their online presence. Articles are created through the admin panel. They are text-only and do not support rich content.

### Usertypes
Skolar manages users by separating them into seperate roles, called "usertypes". They are referenced internally using their IDs (0 through 3). Each role has its own separate permissions and can only interact with specific parts of the webapp, except for admin users.
- **Admin (0)**: Has access to all webapp features. Can manage students and teachers through a dedicated interface.
- **Manager (1)**: Can only manage blog-related content.
- **Teacher (2)**: Can upload and manage educational content specific to their classes.
- **Student (3)**: Can only access and view educational content specific to their classes.

### School content
Teachers can upload school-related documents through the user panel and specify which classes may view the uploaded resource. Students can then access and download these documents. 
