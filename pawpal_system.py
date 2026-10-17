from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from itertools import combinations
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

    def mark_complete(self, today: date | None = None) -> Task | None:
        """Mark done; if recurring, add and return the next occurrence (today + interval)."""
        if self.completed:  # already done: don't spawn a duplicate occurrence
            return None
        self.completed = True
        if self.recurrence is None:
            return None
        next_task = Task(
            task_type=self.task_type,
            due_time=datetime.combine(
                (today or date.today()) + self.recurrence.interval, self.due_time.time()
            ),
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

    @staticmethod
    def sort_by_time(tasks: List[Task]) -> List[Task]:
        """Sort tasks by due_time, breaking ties with higher priority first."""
        return sorted(tasks, key=lambda t: (t.due_time, -t.priority))

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
        task_type: TaskType | None = None,
    ) -> List[Task]:
        """Tasks matching every given filter (None means don't filter), sorted by time."""
        tasks = [
            t for t in self.owner.get_all_tasks()
            if (pet_name is None or (t.pet is not None and t.pet.name == pet_name))
            and (completed is None or t.completed == completed)
            and (task_type is None or t.task_type == task_type)
        ]
        return self.sort_by_time(tasks)

    def get_daily_schedule(self, day: date) -> List[Task]:
        """Incomplete tasks for the day, sorted by due_time then priority."""
        return [t for t in self.filter_tasks(completed=False) if t.due_time.date() == day]

    def get_pending_tasks(self) -> List[Task]:
        """All incomplete tasks across every pet, soonest first."""
        return self.filter_tasks(completed=False)

    def complete_task(self, task: Task) -> Task | None:
        """Complete a task; recurring tasks return their newly created next occurrence."""
        return task.mark_complete()

    def find_conflicts(self) -> List[tuple[Task, Task]]:
        """Pairs of incomplete tasks whose time ranges overlap."""
        # Compares every pair (not just neighbours): a long task can overlap several later ones.
        return [(a, b) for a, b in combinations(self.get_pending_tasks(), 2) if a.overlaps(b)]

    def conflicts_with(self, task: Task) -> List[Task]:
        """Incomplete tasks that would overlap the given (e.g. not yet added) task."""
        return [t for t in self.get_pending_tasks() if t is not task and t.overlaps(task)]

    def get_conflict_warnings(self) -> List[str]:
        """Human-readable warnings for overlapping tasks (same or different pets); never raises."""
        warnings = []
        for a, b in self.find_conflicts():
            a_pet = a.pet.name if a.pet else "unassigned"
            b_pet = b.pet.name if b.pet else "unassigned"
            who = f"for {a_pet}" if a_pet == b_pet else f"for {a_pet} and {b_pet}"
            warnings.append(
                f"Warning: {a.task_type.value} ({a.due_time:%a %H:%M}-{a.end_time:%H:%M}) "
                f"overlaps {b.task_type.value} ({b.due_time:%H:%M}-{b.end_time:%H:%M}) {who}"
            )
        return warnings
