from threading import Lock, Thread
lock = Lock()
g = 0

def add_one():
   """
   Just used for demonstration. It’s bad to use the ‘global’
   statement in general.
   """
   
   global g
   lock.acquire()
   g += 1
   print(g , "in one")
   lock.release()

def add_two():
   global g
   lock.acquire()
   g -= 2
   print(g , "in two")
   lock.release()

threads = []
for func in [ add_two, add_one]:
   threads.append(Thread(target=func))
   threads[-1].start()

for thread in threads:
   """
   Waits for threads to complete before moving on with the main
   script.
   """
   thread.join()

print(g)