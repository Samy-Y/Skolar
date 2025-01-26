# SKOLAR
**Samy Y, 2024**

**SKOLAR** is an innovative CMS which allows schools to efficiently manage and distribute their resources. This project was created in under 10 hours for the 2024 Algorithmics Hackathon. Skolar relies on Flask and SQLite on the backend, and vanilla HTML/CSS/JS on the frontend. This was my first time interacting with Flask and SQL databases.

![](https://media.discordapp.net/attachments/992467708450979925/1333048005653303306/scholar_screenshot.gif?ex=67977933&is=679627b3&hm=b91a8015aa7e0ea2c6fbda1a8e7668737e52172789251f8ff49121702a1532ef)

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
Teachers can upload school-related documents through the user panel and specify which classes may view the uploaded resource. Student can then access and download these documents. 
