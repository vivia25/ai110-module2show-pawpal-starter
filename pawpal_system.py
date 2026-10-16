from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class Task:
    task_type: str  # e.g. "walk", "feed", "vet"
    description: str = ""
    due_time: datetime | None = None
    completed: bool = False

    def mark_complete(self) -> None:
        pass


@dataclass
class Pet:
    name: str
    age: int
    gender: str
    animal_type: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass


@dataclass
class Owner:
    first_name: str
    last_name: str
    age: int
    pet_type: str
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def get_tasks(self) -> List[Task]:
        pass


@dataclass
class Scheduler:
    owner: Owner
    schedule: List[Task] = field(default_factory=list)

    def schedule_task(self, task: Task, time: datetime) -> None:
        pass

    def get_daily_schedule(self) -> List[Task]:
        pass
