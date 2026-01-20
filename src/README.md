# Mergington High School Activities API

A FastAPI application that allows students to view and sign up for extracurricular activities. Data now persists to a SQLite database so sign-ups survive server restarts.

## Features

- View all available extracurricular activities
- Sign up for activities

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run the application from the `src` directory:

   ```
   cd src
   uvicorn app:app --reload
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister from an activity |

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

## Persistence

- Data is stored in a SQLite database at `src/data/app.db` using SQLModel/SQLAlchemy.
- On first run, the database is seeded with example activities and participants. Subsequent runs keep prior sign-ups.
- To reset the data, stop the app and delete `src/data/app.db`; it will be recreated and reseeded on next start.
