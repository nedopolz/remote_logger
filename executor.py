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
        container = self.client.containers.run(image=self.image,
                                               command=['sh', '-c', self.command],
                                               detach=True,
                                               name=self.image,
                                               network_mode="host",
                                               stdout=True,
                                               stderr=True,
                                               tty=True)
        message = b''
        for log in container.logs(stream=True, follow=True):
            if self.stop_event.is_set():
                self.rm_container(self.image)
                self.queue.put(item=log)
                break
            if log != b'\n':
                message += log
                continue
            self.queue.put(item=message.decode("utf-8").strip())
            message = b''
        self.queue.put("DONE")
