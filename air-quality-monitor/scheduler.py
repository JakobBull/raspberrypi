# example of a periodic daemon thread
from time import sleep
from threading import Thread
 
# task that runs at a fixed interval
def background_task(interval_sec):
    # run forever
    while True:
        print(interval_sec)
        # block for the interval
        sleep(interval_sec)
        # perform the task
        print('Background task!')
 
# create and start the daemon thread
print('Starting background task...')
daemon = Thread(target=background_task, args=(3,), daemon=True, name='Background')
daemon.start()
# main thread is carrying on...
print('Main thread is carrying on...')
sleep(10)
print('Main thread done.')