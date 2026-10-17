from datetime import datetime

from pawpal_system import Owner, Pet, Recurrence, Scheduler, Task, TaskType

owner = Owner("Bob", "Dylan", 25)

dog = Pet("Rex", 3, "male", "dog")
cat = Pet("Mittens", 2, "female", "cat")
owner.add_pet(dog)
owner.add_pet(cat)

today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)

dog.add_task(Task(TaskType.WALK, today, duration_minutes=30, recurrence=Recurrence.DAILY))
cat.add_task(Task(TaskType.FEED, today.replace(hour=9), priority=2))
dog.add_task(Task(TaskType.VET, today.replace(hour=14), duration_minutes=60))

scheduler = Scheduler(owner)

print("Today's Schedule")
for task in scheduler.get_daily_schedule(today.date()):
    print(f"  {task.due_time:%H:%M}  {task.task_type.value:<5} {task.pet.name}")
