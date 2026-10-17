from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import List


class TaskType(Enum):
    WALK = "walk"
    FEED = "feed"
    VET = "vet"


class Recurrence(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"

    @property
    def interval(self) -> timedelta:
        """Time between occurrences of this recurrence."""
        return timedelta(days=1 if self is Recurrence.DAILY else 7)


# eq=False: tasks compare by identity, so two identical "feed" tasks stay distinct.
@dataclass(eq=False)
class Task:
    task_type: TaskType
    due_time: datetime
    pet: Pet | None = field(default=None, repr=False)  # set by Pet.add_task
    description: str = ""
    duration_minutes: int = 15
    priority: int = 1  # higher wins when tasks conflict
    recurrence: Recurrence | None = None
    completed: bool = False

    @property
    def end_time(self) -> datetime:
        """When the task finishes (due_time plus duration)."""
        return self.due_time + timedelta(minutes=self.duration_minutes)

    def mark_complete(self) -> Task | None:
        """Mark done; if recurring, add and return the next occurrence."""
        self.completed = True
        if self.recurrence is None:
            return None
        next_task = Task(
            task_type=self.task_type,
            due_time=self.due_time + self.recurrence.interval,
            description=self.description,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            recurrence=self.recurrence,
        )
        if self.pet is not None:
            self.pet.add_task(next_task)
        return next_task

    def overlaps(self, other: Task) -> bool:
        """True if the time ranges of the two tasks intersect."""
        return self.due_time < other.end_time and other.due_time < self.end_time


@dataclass
class Pet:
    name: str
    age: int
    gender: str
    animal_type: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach task to this pet and set task.pet."""
        task.pet = self
        if task not in self.tasks:
            self.tasks.append(task)


@dataclass
class Owner:
    first_name: str
    last_name: str
    age: int
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner, ignoring duplicates."""
        if pet not in self.pets:
            self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """All tasks across all pets (derived, not stored)."""
        return [task for pet in self.pets for task in pet.tasks]


@dataclass
class Scheduler:
    """Builds schedules from owner.get_all_tasks(); stores no task list of its own."""

    owner: Owner

    def get_daily_schedule(self, day: date) -> List[Task]:
        """Incomplete tasks for the day, sorted by due_time then priority."""
        tasks = [
            t for t in self.owner.get_all_tasks()
            if not t.completed and t.due_time.date() == day
        ]
        return sorted(tasks, key=lambda t: (t.due_time, -t.priority))

    def get_pending_tasks(self) -> List[Task]:
        """All incomplete tasks across every pet, soonest first."""
        pending = [t for t in self.owner.get_all_tasks() if not t.completed]
        return sorted(pending, key=lambda t: t.due_time)

    def find_conflicts(self) -> List[tuple[Task, Task]]:
        """Pairs of incomplete tasks whose time ranges overlap."""
        tasks = self.get_pending_tasks()
        return [
            (a, b)
            for i, a in enumerate(tasks)
            for b in tasks[i + 1:]
            if a.overlaps(b)
        ]
