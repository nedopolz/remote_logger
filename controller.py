import time
from queue import Queue
from threading import Thread
from threading import Event
from aws_logger import AWSLogger
from executor import ContainerExecutor


class Controller:
    def __init__(
        self: str,
        docker_image: str,
        bash_command: str,
        aws_cloudwatch_group: str,
        aws_cloudwatch_stream: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
    ):
        self.queue = Queue()
        self.stop_event = Event()
        self.container = ContainerExecutor(
            queue=self.queue,
            stop_event=self.stop_event,
            image=docker_image,
            command=bash_command,
        )
        self.aws_logger = AWSLogger(
            self.queue,
            self.stop_event,
            aws_cloudwatch_group,
            aws_cloudwatch_stream,
            aws_access_key_id,
            aws_secret_access_key,
            aws_region,
        )

    def run(self):
        if err := self.aws_logger.before_run_check():
            return err
        aws_thread = Thread(target=self.aws_logger.listen)
        docker_thread = Thread(target=self.container.execute)
        try:
            aws_thread.start()
            docker_thread.start()
            aws_thread.join()
            docker_thread.join()
        except (KeyboardInterrupt, SystemExit):
            self.stop_event.set()
            for i in range(20):
                if aws_thread.is_alive() or docker_thread.is_alive():
                    print("pls wait cleaning buffer")
                    time.sleep(1)
            return "terminated"
        return "success"
