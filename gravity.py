#Gravity

import math

def new_pos(current_pos, velocity = (0,0), acceleration = (0, 10), time = 1):
    #X
    x = current_pos[0] + velocity[0]*time + 0.5*acceleration[0]*math.pow(time, 2)
    vx = velocity[0]*time + acceleration[0]*time
    #Y
    y = current_pos[1] + velocity[1]*time + 0.5*acceleration[1]*math.pow(time, 2)
    vy = velocity[1]*time + acceleration[1]*time
    
    return (vx, vy), (x, y)
