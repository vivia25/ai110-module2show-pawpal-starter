from datetime import date, datetime, timedelta

from pawpal_system import Owner, Pet, Recurrence, Scheduler, Task, TaskType


def make_task() -> Task:
    return Task(TaskType.WALK, datetime(2026, 10, 17, 8, 0))


def test_mark_complete_changes_status():
    task = make_task()
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Rex", 3, "male", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(make_task())

    assert len(pet.tasks) == 1


def make_scheduler():
    owner = Owner("Bob", "Dylan", 25)
    rex, tom = Pet("Rex", 3, "male", "dog"), Pet("Tom", 2, "female", "cat")
    owner.add_pet(rex)
    owner.add_pet(tom)
    return Scheduler(owner), rex, tom


def test_tasks_sorted_by_time():
    sched, rex, _ = make_scheduler()
    late = Task(TaskType.VET, datetime(2026, 10, 17, 14, 0))
    early = Task(TaskType.WALK, datetime(2026, 10, 17, 8, 0))
    rex.add_task(late)
    rex.add_task(early)

    assert sched.get_pending_tasks() == [early, late]


def test_filter_by_pet_and_status():
    sched, rex, tom = make_scheduler()
    a = Task(TaskType.WALK, datetime(2026, 10, 17, 8, 0))
    b = Task(TaskType.FEED, datetime(2026, 10, 17, 9, 0))
    rex.add_task(a)
    tom.add_task(b)
    a.mark_complete()

    assert sched.filter_tasks(pet_name="Tom") == [b]
    assert sched.filter_tasks(completed=True) == [a]
    assert sched.filter_tasks(pet_name="Rex", completed=False) == []


def test_recurring_task_creates_next_occurrence_once():
    _, rex, _ = make_scheduler()
    walk = Task(TaskType.WALK, datetime(2026, 10, 17, 8, 0), recurrence=Recurrence.DAILY)
    rex.add_task(walk)

    nxt = walk.mark_complete(today=date(2026, 10, 17))
    assert nxt.due_time == datetime(2026, 10, 18, 8, 0)
    assert nxt in rex.tasks and not nxt.completed
    assert walk.mark_complete() is None  # completing again adds no duplicate
    assert len(rex.tasks) == 2


def test_next_occurrence_is_relative_to_completion_day():
    _, rex, _ = make_scheduler()
    daily = Task(TaskType.WALK, datetime(2026, 10, 10, 8, 0), recurrence=Recurrence.DAILY)
    weekly = Task(TaskType.VET, datetime(2026, 10, 10, 14, 30), recurrence=Recurrence.WEEKLY)
    rex.add_task(daily)
    rex.add_task(weekly)

    # Both completed late, on the 17th: next due is counted from that day, keeping time of day.
    assert daily.mark_complete(today=date(2026, 10, 17)).due_time == datetime(2026, 10, 18, 8, 0)
    assert weekly.mark_complete(today=date(2026, 10, 17)).due_time == datetime(2026, 10, 24, 14, 30)


def test_non_recurring_task_creates_nothing():
    _, rex, _ = make_scheduler()
    task = make_task()
    rex.add_task(task)

    assert task.mark_complete() is None
    assert len(rex.tasks) == 1


def test_conflict_detection():
    sched, rex, tom = make_scheduler()
    walk = Task(TaskType.WALK, datetime(2026, 10, 17, 8, 0), duration_minutes=30)
    feed = Task(TaskType.FEED, datetime(2026, 10, 17, 8, 15))
    vet = Task(TaskType.VET, datetime(2026, 10, 17, 8, 30))  # starts as walk ends
    rex.add_task(walk)
    tom.add_task(feed)
    rex.add_task(vet)

    assert sched.find_conflicts() == [(walk, feed)]
    assert sched.conflicts_with(Task(TaskType.FEED, datetime(2026, 10, 17, 8, 5))) == [walk, feed]


def test_conflict_warnings_same_pet_and_different_pets():
    sched, rex, tom = make_scheduler()
    at8 = datetime(2026, 10, 17, 8, 0)
    rex.add_task(Task(TaskType.WALK, at8, duration_minutes=30))
    rex.add_task(Task(TaskType.FEED, at8))   # same pet, same time
    tom.add_task(Task(TaskType.VET, at8))    # different pet, same time

    warnings = sched.get_conflict_warnings()

    assert len(warnings) == 3
    assert all(w.startswith("Warning:") for w in warnings)
    assert any("for Rex" in w and "Rex and" not in w for w in warnings)
    assert any("Rex and Tom" in w or "Tom and Rex" in w for w in warnings)


def test_no_conflicts_gives_no_warnings():
    sched, rex, _ = make_scheduler()
    rex.add_task(Task(TaskType.WALK, datetime(2026, 10, 17, 8, 0)))
    rex.add_task(Task(TaskType.FEED, datetime(2026, 10, 17, 9, 0)))

    assert sched.get_conflict_warnings() == []
