"""
High School Management System API

A FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.

The app now persists data in SQLite using SQLModel instead of in-memory
Python dictionaries.
"""

from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import selectinload
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select
import os
from pathlib import Path

app = FastAPI(
    title="Mergington High School API",
    description="API for viewing and signing up for extracurricular activities",
)

# Mount the static files directory
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(Path(__file__).parent, "static")),
    name="static",
)


# ----------
# Persistence
# ----------

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{DATA_DIR / 'app.db'}"


class Enrollment(SQLModel, table=True):
    activity_name: str = Field(foreign_key="activity.name", primary_key=True)
    participant_email: str = Field(foreign_key="participant.email", primary_key=True)


class Activity(SQLModel, table=True):
    name: str = Field(primary_key=True)
    description: str
    schedule: str
    max_participants: int
    participants: List["Participant"] = Relationship(
        back_populates="activities", link_model=Enrollment
    )


class Participant(SQLModel, table=True):
    email: str = Field(primary_key=True)
    activities: List[Activity] = Relationship(
        back_populates="participants", link_model=Enrollment
    )


engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)


SEED_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
}


def seed_database() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        has_activities = session.exec(select(Activity)).first()
        if has_activities:
            return

        for name, details in SEED_ACTIVITIES.items():
            activity = Activity(
                name=name,
                description=details["description"],
                schedule=details["schedule"],
                max_participants=details["max_participants"],
            )
            session.add(activity)
            for email in details["participants"]:
                participant = session.get(Participant, email)
                if not participant:
                    participant = Participant(email=email)
                    session.add(participant)
                activity.participants.append(participant)

        session.commit()


seed_database()


def activity_payload(activity: Activity) -> dict:
    return {
        "description": activity.description,
        "schedule": activity.schedule,
        "max_participants": activity.max_participants,
        "participants": [participant.email for participant in activity.participants],
    }


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    with Session(engine) as session:
        activities = session.exec(
            select(Activity).options(selectinload(Activity.participants))
        ).all()
        return {activity.name: activity_payload(activity) for activity in activities}


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    with Session(engine) as session:
        activity = session.exec(
            select(Activity)
            .where(Activity.name == activity_name)
            .options(selectinload(Activity.participants))
        ).first()

        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        if any(participant.email == email for participant in activity.participants):
            raise HTTPException(status_code=400, detail="Student is already signed up")

        if len(activity.participants) >= activity.max_participants:
            raise HTTPException(status_code=400, detail="Activity is full")

        participant = session.get(Participant, email)
        if not participant:
            participant = Participant(email=email)
            session.add(participant)

        activity.participants.append(participant)
        session.add(activity)
        session.commit()

        return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    with Session(engine) as session:
        activity = session.exec(
            select(Activity)
            .where(Activity.name == activity_name)
            .options(selectinload(Activity.participants))
        ).first()

        if not activity:
            raise HTTPException(status_code=404, detail="Activity not found")

        participant = session.get(Participant, email)
        if not participant or participant not in activity.participants:
            raise HTTPException(
                status_code=400, detail="Student is not signed up for this activity"
            )

        activity.participants.remove(participant)
        session.add(activity)
        session.commit()

        return {"message": f"Unregistered {email} from {activity_name}"}
