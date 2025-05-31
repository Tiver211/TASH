import datetime
import pytest
from app.planner import Task, Buffer, Rest, Schedule, Planner


class TestAbstractTask:
    """Тесты для базового класса задач"""

    def test_init_valid_complexity(self):
        """Проверка корректной инициализации с допустимой сложностью"""
        task = Task(name="test", complexity=3)
        assert task.complexity == 3

    @pytest.mark.parametrize("complexity", [0, 6])
    def test_init_invalid_complexity_raises(self, complexity):
        """Проверка вызова исключения при недопустимой сложности"""
        with pytest.raises(ValueError, match="complexity must be between 1 and 5"):
            Task(name="test", complexity=complexity)

    @pytest.mark.parametrize("priority", [0, 6])
    def test_init_invalid_priority_raises(self, priority):
        """Проверка вызова исключения при недопустимой сложности"""
        with pytest.raises(ValueError, match="priority must be between 1 and 5"):
            Task(name="test", priority=priority)

    def test_default_values(self):
        """Проверка значений по умолчанию"""
        task = Task(name="test")
        assert task.duration is None
        assert task.description == ""
        assert task.deadline is None
        assert task.min_start_time is None
        assert task.duration_inaccuracy == datetime.timedelta()


class TestTask:
    """Тесты для класса Task"""

    @pytest.fixture
    def sample_abstract_task(self):
        return Task(
            name="test task",
            duration=datetime.timedelta(hours=1),
            complexity=2,
            description="test description"
        )

    def test_init_with_start_time(self, sample_abstract_task):
        """Проверка инициализации с указанием времени начала"""
        start_time = datetime.datetime(2023, 1, 1, 10, 0)
        task = Task(
            name=sample_abstract_task.name,
            start=start_time,
            duration=sample_abstract_task.duration,
            complexity=sample_abstract_task.complexity,
            description=sample_abstract_task.description
        )

        assert task.start == start_time
        assert task.stop == start_time + sample_abstract_task.duration

    def test_pin_task_classmethod(self, sample_abstract_task):
        """Проверка фабричного метода pin_task"""
        start_time = datetime.datetime(2023, 1, 1, 10, 0)
        sample_abstract_task.pin_task(start_time)

        assert isinstance(sample_abstract_task, Task)
        assert sample_abstract_task.name == sample_abstract_task.name
        assert sample_abstract_task.start == start_time
        assert sample_abstract_task.stop == start_time + sample_abstract_task.duration


class TestSchedule:
    """Тесты для класса Schedule"""

    @pytest.fixture
    def sample_schedule(self):
        start = datetime.datetime(2023, 1, 1, 9, 0)
        stop = datetime.datetime(2023, 1, 1, 18, 0)
        return Schedule(start, stop)

    @pytest.fixture
    def sample_tasks(self):
        start1 = datetime.datetime(2023, 1, 1, 10, 0)
        start2 = datetime.datetime(2023, 1, 1, 12, 0)

        return [
            Task("Task 1", start1, datetime.timedelta(hours=1)),
            Task("Task 2", start2, datetime.timedelta(hours=2))
        ]

    def test_add_task(self, sample_schedule, sample_tasks):
        """Проверка добавления задач в расписание"""
        for task in sample_tasks:
            sample_schedule.add_task(task)

        assert len(sample_schedule.tasks) == 2
        assert sample_schedule.tasks[0].name == "Task 1"

    def test_complete_schedule_sorts_tasks(self, sample_schedule, sample_tasks):
        """Проверка сортировки задач по времени начала"""
        # Добавляем задачи в обратном порядке
        sample_schedule.add_task(sample_tasks[1])
        sample_schedule.add_task(sample_tasks[0])

        sample_schedule.complete_schedule()

        assert sample_schedule.tasks[0].start < sample_schedule.tasks[1].start

    def test_check_collision_raises(self, sample_schedule):
        """Проверка обнаружения коллизий во времени"""
        start = datetime.datetime(2023, 1, 1, 10, 0)
        sample_schedule.add_task(Task("Task 1", start, datetime.timedelta(hours=2)))
        sample_schedule.add_task(Task("Task 2", start + datetime.timedelta(hours=1), datetime.timedelta(hours=1)))

        with pytest.raises(ValueError, match="Tasks collision"):
            sample_schedule.check_collision()


class TestPlanner:
    """Тесты для класса Planner"""

    @pytest.fixture
    def sample_abstract_tasks(self):
        return [
            Task(
                name="Task 1",
                duration=datetime.timedelta(hours=1),
                complexity=2
            ),
            Task(
                name="Task 2",
                duration=datetime.timedelta(hours=2),
                complexity=1
            )
        ]

    @pytest.fixture
    def sample_planner(self, sample_abstract_tasks):
        day_start = datetime.datetime(2023, 1, 1, 9, 0)
        day_stop = datetime.datetime(2023, 1, 1, 18, 0)
        return Planner(sample_abstract_tasks, day_start, day_stop)

    def test_plan_creates_schedule(self, sample_planner):
        """Проверка создания расписания"""
        sample_planner.plan()
        assert isinstance(sample_planner.schedule, Schedule)

    def test_plan_sorts_by_complexity(self, sample_planner):
        """Проверка сортировки задач по сложности"""
        sample_planner.plan()
        tasks = sample_planner.schedule.tasks[::2]  # Берем только задачи (каждая вторая - буфер)

        # Проверяем что задачи отсортированы по возрастанию complexity
        assert tasks[0].name == "Task 2"  # complexity=1
        assert tasks[1].name == "Task 1"  # complexity=2

    def test_plan_adds_buffers(self, sample_planner):
        """Проверка добавления буферных задач"""
        sample_planner.plan()
        tasks = sample_planner.schedule.tasks

        # Проверяем что между задачами есть буферы
        assert isinstance(tasks[1], Buffer)
        assert isinstance(tasks[3], Buffer)


class TestSpecialTasks:
    """Тесты для специализированных классов задач"""

    def test_buffer_task(self):
        """Проверка создания буферной задачи"""
        start = datetime.datetime(2023, 1, 1, 10, 0)
        duration = datetime.timedelta(minutes=30)
        buffer = Buffer(start, duration)

        assert buffer.name == "buffer"
        assert buffer.description == "buffer between tasks, free time"
        assert buffer.start == start
        assert buffer.stop == start + duration

    def test_rest_task(self):
        """Проверка создания задачи отдыха"""
        start = datetime.datetime(2023, 1, 1, 10, 0)
        duration = datetime.timedelta(minutes=30)
        rest = Rest(start, duration)

        assert rest.name == "rest"
        assert rest.description == "free time, take a rest"
        assert rest.start == start
        assert rest.stop == start + duration