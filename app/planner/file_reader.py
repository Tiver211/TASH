import os
import datetime

from .planner import Planner, Task


class Reader:
    def read_tasks(self, path: str):
        with open(path, 'r') as f:
            text = f.read()

        texts = text.split("<--->")
        tasks = []
        for text in texts:
            data = self.get_data(text)
            if not data:
                continue

            tasks.append(Task(**data))

        return tasks

    def read_task(self, path: str):
        with open(path, 'r') as f:
            text = f.read()
        data = self.get_data(text)
        if not data:
            raise ValueError("empty file given")

        task = Task(**data)
        return task

    def get_data(self, text: str):
        data = {}
        if not text:
            return data

        for line in text.split(","):
            line = line.replace("\n", "")
            key, value = line.split('=')
            data[key] = self.parse_value(value)

        return data

    def parse_value(self, value: str):
        if value.isdigit():
            return int(value)

        elif value.startswith('"') and value.endswith('"'):
            return value[1:-1]

        elif len(value.split(":")) == 3:
            delta = value.split(":")
            delta = list(map(int, delta))
            return datetime.timedelta(hours=delta[0], minutes=delta[1], seconds=delta[2])

        elif len(value.split(".")) == 6:
            delta = value.split(".")
            delta = list(map(int, delta))
            return datetime.datetime(year=delta[0],
                                     month=delta[1],
                                     day=delta[2],
                                     hour=delta[3],
                                     minute=delta[4],
                                     second=delta[5])

        else:
            raise ValueError("Wrong format")


if __name__ == '__main__':
    reader = Reader()
    tasks = reader.read_tasks("G:\\python\\TASH\\examples\\simple\\many.tashes")
    planner = Planner(tasks, datetime.datetime(year=2025, month=5, day=31, hour=8), datetime.datetime(year=2025, month=5, day=31, hour=20))
    planner.plan()
    print(planner.schedule)
