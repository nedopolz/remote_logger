# remote_logger

### Architecture overview

1. Since we need to work with IO, a multi-threaded application architecture was chosen.
2. To achieve graceful shutdown Event-based synchronisation is used.
3. "DONE" message is used to indicate end of container log.
4. Honestly I need to add more accurate error handling)))

### Features
1. Can handle network error and wait for given amount of time for error to goes away.
2. In case of shutdown clean makes sure that all logs is delivered to AWS.
