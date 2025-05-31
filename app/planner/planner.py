import datetime
from tabulate import tabulate


class Task:
    """
    Задание привязанное ко времени и расписанию
    """
    def __init__(self,
                 name: str,
                 start: datetime.datetime = None,
                 duration: datetime.timedelta = None,
                 complexity: int = 3,
                 description: str = "",
                 deadline: datetime.datetime = None,
                 min_start_time: datetime.datetime = None,
                 duration_inaccuracy: datetime.timedelta = datetime.timedelta(),
                 priority: int = 3):
        if not 1 <= complexity <= 5:
            raise ValueError("complexity must be between 1 and 5")

        if not 1 <= priority <= 5:
            raise ValueError("priority must be between 1 and 5")

        self.name = name
        self.duration = duration
        self.complexity = complexity
        self.description = description
        self.deadline = deadline
        self.min_start_time = min_start_time
        self.duration_inaccuracy = duration_inaccuracy
        self.start = start
        self.stop = None
        if start:
            self.stop = start + duration

    def pin_task(self, start):
        self.start = start
        self.stop = start + self.duration


class Buffer(Task):
    def __init__(self, start: datetime.datetime, duration: datetime.timedelta):
        super().__init__("buffer", start=start, duration=duration, description="buffer between tasks, free time")


class Rest(Task):
    def __init__(self, start: datetime.datetime, duration: datetime.timedelta):
        super().__init__("rest", start=start, duration=duration, description="free time, take a rest")

class Schedule:
    def __init__(self, start: datetime.datetime, stop: datetime.datetime):
        self.start = start
        self.stop = stop
        self.tasks: list[Task] = []

    def add_task(self, task: Task):
        self.tasks.append(task)

    def complete_schedule(self):
        self.tasks = sorted(self.tasks, key=lambda t: t.start)
        self.check_collision()

    def check_collision(self):
        last_stop = self.start
        for task in self.tasks:
            if task.start < last_stop:
                raise ValueError("Tasks collision")

            last_stop = task.stop


    def __str__(self):
        data = [[i, t.name, t.description, t.start, t.stop] for i, t in enumerate(self.tasks)]
        return tabulate(data, headers=["Task", "Name", "Description", "Start", "Stop"], tablefmt="orgtbl")

class Planner:
    def __init__(self, tasks: list[Task], day_start: datetime.datetime, day_stop: datetime.datetime):
        self.schedule = None
        self.tasks = tasks
        self.day_start = day_start
        self.day_stop = day_stop

    def plan(self):
        self.schedule = Schedule(self.day_start, self.day_stop)
        tasks = sorted(self.tasks, key=lambda t: t.complexity)
        next_time = self.day_start
        for task in tasks:
            task.pin_task(next_time)
            self.schedule.add_task(task)
            next_time = task.stop
            buffer_lenght = task.duration_inaccuracy*1.5+task.duration*0.1
            buffer = Buffer(next_time, buffer_lenght)
            self.schedule.add_task(buffer)
            next_time = buffer.stop

        self.schedule.complete_schedule()
