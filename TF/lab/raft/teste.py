import threading

variable = 0
cond = threading.Condition()

def waitsForTen():
    with cond:
        cond.wait_for(lambda : variable == '10', 5)
        print('Woke up!')

threading.Thread(target=waitsForTen).start()
while(True):
    temp = input('Value? ')
    with cond:
        variable = temp
        cond.notify()
