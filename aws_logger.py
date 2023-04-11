import datetime
import time
from queue import Queue
from threading import Event

import boto3


class AWSLogger:
    def __init__(
        self,
        queue: Queue,
        stop_event: Event,
        aws_cloudwatch_group: str,
        aws_cloudwatch_stream: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        aws_region: str,
    ):
        self.client = boto3.client(
            "logs",
            region_name=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )
        self.aws_cloudwatch_group = aws_cloudwatch_group
        self.aws_cloudwatch_stream = aws_cloudwatch_stream
        self.queue = queue
        self.log_buffer = []
        self.stop_event = stop_event

    def _check_client(self):
        try:
            self.client.describe_log_groups()
        except Exception as e:
            return e

    def _check_group(self):
        response = self.client.describe_log_groups(
            logGroupNamePrefix=self.aws_cloudwatch_group
        )
        for group in response["logGroups"]:
            if group["logGroupName"] == self.aws_cloudwatch_group:
                return False
        return True

    def _create_group(self):
        try:
            self.client.create_log_group(logGroupName=self.aws_cloudwatch_group)
        except Exception as e:
            return e

    def _check_stream(self):
        response = self.client.describe_log_streams(
            logGroupName=self.aws_cloudwatch_group,
            logStreamNamePrefix=self.aws_cloudwatch_stream,
        )
        for group in response["logStreams"]:
            if group["logStreamName"] == self.aws_cloudwatch_stream:
                return False
        return True

    def _create_stream(self):
        try:
            self.client.create_log_stream(
                logGroupName=self.aws_cloudwatch_group,
                logStreamName=self.aws_cloudwatch_stream,
            )
        except Exception as e:
            return e

    def _write(self, log: str):
        try:
            self.client.put_log_events(
                logGroupName=self.aws_cloudwatch_group,
                logStreamName=self.aws_cloudwatch_stream,
                logEvents=[{"timestamp": int(round(time.time() * 1000)), "message": str(log)}],
            )
        except Exception as e:
            return e

    def before_run_check(self):
        if err := self._check_client():
            return err
        if self._check_group():
            if err := self._create_group():
                return err
        if self._check_stream():
            if err := self._create_stream():
                return err

    def clean_buffer(self):
        err = True
        for message in reversed(self.log_buffer):
            if self._write(message):
                err = False
            else:
                self.log_buffer.remove(message)
        return err

    def all_queue_to_buffer(self):
        while log := self.queue.get():
            self.log_buffer.append(log)

    def listen(self):
        first_err_time = None
        while True:
            if not self.stop_event.is_set: # if we need to STOP
                self.all_queue_to_buffer()
                self.clean_buffer()
                break

            log = self.queue.get()

            if log == "DONE": # if we need to finish up
                self.clean_buffer()
                break
            if not log:
                continue

            if len(self.log_buffer) > 0: # if buffer has something we need to write it first
                if not self.clean_buffer():
                    self.log_buffer.append(log)
                    continue

            if err := self._write(log):
                if len(self.log_buffer) == 0: # if error - start timer
                    first_err_time = datetime.datetime.now()
                self.log_buffer.append(log) # add message to buffer
                if datetime.datetime.now() - first_err_time > datetime.timedelta(seconds=15): # last try to send all
                    print(f"stop program after 15 seconds of AWS {err}. Total errors: {len(self.log_buffer)}")
                    self.all_queue_to_buffer()
                    self.clean_buffer()
                    self.stop_event.set()
            else:
                first_err_time = None
                self.log_buffer = []
