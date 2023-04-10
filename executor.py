import docker

from threading import Event
from queue import Queue


class ContainerExecutor:
    def __init__(self, queue: Queue, stop_event: Event, image: str, command: str):
        self.stop_event = stop_event
        self.queue = queue
        self.image = image
        self.command = command
        self.client = docker.from_env()
        self.rm_container(image)

    def rm_container(self, container_name: str):
        try:
            container = self.client.containers.get(container_name)
            container.remove(force=True)
        except docker.errors.NotFound:
            pass

    def execute(self):
        container = self.client.containers.run(
            image=self.image,
            command=self.command,
            name=self.image,
            auto_remove=True,
            detach=True,
        )
        for log in container.logs(stream=True):
            if self.stop_event.is_set():
                self.rm_container(self.image)
                self.queue.put(item=log)
                break
            self.queue.put(item=log)
        self.queue.put("DONE")
