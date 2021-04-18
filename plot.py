import numpy as np
import matplotlib.pyplot as plt

x = [0,20,40,60,80,100] # insert % x axis fields
y = [2000,3000,5000,7000,9000,2000] # y axis fields

for i in range(0, len(x)):
    plt.plot(x[i:i+2], y[i:i+2], 'ro-')

plt.xlabel("X axis label") #give x label
plt.ylabel("Y axis label") #give y label
plt.savefig('name_you want to save.png') #give name
plt.show()