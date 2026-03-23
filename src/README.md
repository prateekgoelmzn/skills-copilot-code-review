# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- Display active school announcements from the database
- Manage announcements when signed in as a teacher

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                                      | Description                                                         |
| ------ | ----------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                                 | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu`             | Sign up for an activity                                             |
| GET    | `/announcements`                                                              | Get announcements that are currently active                         |
| GET    | `/announcements/manage?teacher_username=principal`                            | Get all announcements for the management dialog                     |
| POST   | `/announcements?teacher_username=principal`                                   | Create a new announcement                                           |
| PUT    | `/announcements/{announcement_id}?teacher_username=principal`                 | Update an existing announcement                                     |
| DELETE | `/announcements/{announcement_id}?teacher_username=principal`                 | Delete an announcement                                              |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

The application stores activities, teachers, and announcements in MongoDB.
