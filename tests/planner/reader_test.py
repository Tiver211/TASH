import pytest
from unittest.mock import mock_open, patch
import datetime
from app.planner import Planner, Task
from app.planner import Reader  # Замените на ваш реальный импорт


class TestReader:
    """Тесты для класса Reader"""

    @pytest.fixture
    def reader(self):
        return Reader()

    # Тесты для parse_value
    @pytest.mark.parametrize("input_value, expected", [
        ("42", 42),  # Целое число
        ('"text"', "text"),  # Строка в кавычках
        ("1:30:15", datetime.timedelta(hours=1, minutes=30, seconds=15)),  # timedelta
        ("2025.5.31.8.0.0", datetime.datetime(2025, 5, 31, 8, 0, 0)),  # datetime
    ])
    def test_parse_value_valid(self, reader, input_value, expected):
        assert reader.parse_value(input_value) == expected

    def test_parse_value_invalid(self, reader):
        with pytest.raises(ValueError, match="Wrong format"):
            reader.parse_value("invalid_value")

    # Тесты для get_data
    def test_get_data_simple(self, reader):
        text = "name=\"Task 1\",duration=1:0:0,complexity=3"
        result = reader.get_data(text)
        assert result == {
            "name": "Task 1",
            "duration": datetime.timedelta(hours=1),
            "complexity": 3
        }

    def test_get_data_with_datetime(self, reader):
        text = "name=\"Meeting\",deadline=2025.5.31.15.0.0"
        result = reader.get_data(text)
        assert result == {
            "name": "Meeting",
            "deadline": datetime.datetime(2025, 5, 31, 15, 0, 0)
        }

    # Тесты для read_task
    def test_read_task_single(self, reader):
        mock_file_content = 'name="Single Task",duration=0:30:0,complexity=2'

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            task = reader.read_task("dummy_path.txt")

        assert isinstance(task, Task)
        assert task.name == "Single Task"
        assert task.duration == datetime.timedelta(minutes=30)
        assert task.complexity == 2

    # Тесты для read_tasks
    def test_read_tasks_multiple(self, reader):
        mock_file_content = (
            'name="Task 1",duration=1:0:0,complexity=3<--->'
            'name="Task 2",duration=0:45:0,complexity=1'
        )

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            tasks = reader.read_tasks("dummy_path.txt")

        assert len(tasks) == 2
        assert tasks[0].name == "Task 1"
        assert tasks[1].name == "Task 2"
        assert tasks[0].duration == datetime.timedelta(hours=1)
        assert tasks[1].duration == datetime.timedelta(minutes=45)

    def test_read_tasks_empty_file(self, reader):
        with patch("builtins.open", mock_open(read_data="")):
            tasks = reader.read_tasks("empty.txt")
            assert len(tasks) == 0

    def test_read_task_empty_file(self, reader):
        with pytest.raises(ValueError):
            with patch("builtins.open", mock_open(read_data="")):
                task = reader.read_task("empty.txt")
                assert len(task) == 0

    def test_read_tasks_with_all_fields(self, reader):
        mock_file_content = (
            'name="Full Task",duration=2:30:0,complexity=5,'
            'description="Important task",deadline=2025.6.1.18.0.0,'
            'min_start_time=2025.5.31.9.0.0,'
            'duration_inaccuracy=0:15:0'
        )

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            task = reader.read_task("full_task.txt")

        assert task.name == "Full Task"
        assert task.duration == datetime.timedelta(hours=2, minutes=30)
        assert task.complexity == 5
        assert task.description == "Important task"
        assert task.deadline == datetime.datetime(2025, 6, 1, 18, 0, 0)
        assert task.min_start_time == datetime.datetime(2025, 5, 31, 9, 0, 0)
        assert task.duration_inaccuracy == datetime.timedelta(minutes=15)

    # Тесты на ошибки
    def test_read_nonexistent_file(self, reader):
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                reader.read_task("nonexistent.txt")

    def test_malformed_data(self, reader):
        mock_file_content = "name=Task1,duration=invalid"

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            with pytest.raises(ValueError):
                reader.read_task("malformed.txt")

    def test_incomplete_data(self, reader):
        mock_file_content = "duration=1:0:0"  # Нет обязательного поля name

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            with pytest.raises(TypeError):
                reader.read_task("incomplete.txt")

    # Интеграционный тест с Planner
    def test_integration_with_planner(self, reader):
        mock_file_content = (
            'name="Task 1",duration=1:0:0,complexity=3<--->'
            'name="Task 2",duration=0:45:0,complexity=1'
        )

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            tasks = reader.read_tasks("dummy_path.txt")

            planner = Planner(
                tasks,
                datetime.datetime(2025, 5, 31, 9, 0, 0),
                datetime.datetime(2025, 5, 31, 18, 0, 0)
            )
            planner.plan()

            assert len(planner.schedule.tasks) > 0
            assert planner.schedule.tasks[0].name in ["Task 1", "Task 2"]