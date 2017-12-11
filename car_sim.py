import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import random
from time import sleep

# bind to keyboard so that you can allow single steps forward
# as well as play/pause
# allow adjustable time interval between iterations

class Lane:
    '''
    Class for a single lane on a road.
    '''
    def __init__(self, length, num_cars):
        self.length = length
        self.num_cars = num_cars
        start_posns = random.sample([i for i in range(self.length)], self.num_cars)
        start_posns = sorted(start_posns)
        start_vels = [random.randint(1, 5) for i in range(self.num_cars)]
        self.cars = [Car(p, v) for (p, v) in zip(start_posns, start_vels)]

    def get_posns(self):
        '''
        Returns a list of positions for all the cars in the lane.
        '''
        return [c.posn for c in self.cars]

    def get_vels(self):
        '''
        Returns a list of velocities for all the cars in the lane.
        '''
        return [c.vel for c in self.cars]

    def update(self):
        '''
        Updates the positions of all the cars in the lane. No lane changes allowed.
        '''
        curr_posns = self.get_posns()
        for i, c in enumerate(self.cars):
            c.update(curr_posns[(i + 1) % self.num_cars], self.length)

    def update_wLC(self, adjs):
        '''
        Updates the positions of all the cars in the lane, allowing lane changes.
        '''
        curr_posns = self.get_posns()
        toPop = []
        for i, c in enumerate(self.cars):
            b = c.update_wLC(curr_posns[(i+1) % max(self.num_cars, 1)], self.length, adjs)
            if b:
                toPop.append(i)
        for i in toPop[::-1]:
            self.cars.pop(i)
            self.num_cars -= 1

    def add_car(self, car):
        '''
        Adds a car to the lane.
        '''
        self.cars.append(car)
        self.cars = sorted(self.cars, key=lambda x:x.posn)

    def crash_car(self):
        '''
        Selects a random car in the lane to "crash".
        '''
        ind = random.randint(0, self.num_cars - 1)
        self.cars[ind].crash_timer = 30
        print("Crashing car at position " + str(self.cars[ind].posn))

class Car:
    '''
    Class for a single car with position and velocity.
    '''
    def __init__(self, p, v):
        self.posn = p
        self.vel = v
        self.crash_timer = 0

    def update(self, p_ahead, road_len):
        '''
        Update rule for the car, without lane changes.
        '''
        if self.crash_timer:
            self.vel = 0
            self.crash_timer -= 1
            return
        if self.vel < 5:
            self.vel += 1
        if p_ahead < self.posn:
            p_ahead += road_len
        if (p_ahead - self.posn) < self.vel:
            self.vel = p_ahead - self.posn - 1
        if self.vel > 0:
            if random.random() < 0.5:
                self.vel -= 1
        self.posn = (self.posn + self.vel) % road_len

    def update_wLC(self, p_ahead, road_len, adjs):
        '''
        Update rule for the car, with lane changes.
        '''
        if self.crash_timer:
            self.vel = 0
            self.crash_timer -= 1
            return False
        lSpace = -1
        rSpace = -1
        mSpace = (p_ahead - self.posn) % road_len
        # find spacing in the adjacent lanes
        if adjs[0] != None:
            (l_behind, l_ahead) = ahead_behind(self, adjs[0], road_len)
            if (l_behind.posn + l_behind.vel + 1) % road_len < self.posn:
                lSpace = (l_ahead.posn - self.posn) % road_len
        if adjs[1] != None:
            (r_behind, r_ahead) = ahead_behind(self, adjs[1], road_len)
            if (r_behind.posn + r_behind.vel + 1) % road_len < self.posn:
                rSpace = (r_ahead.posn - self.posn) % road_len
        if mSpace == max([rSpace, lSpace, mSpace]):
            self.update(p_ahead, road_len)
            return False
        elif rSpace == max([rSpace, lSpace, mSpace]):
            adjs[1].add_car(self)
            adjs[1].num_cars += 1
            return True
        elif lSpace == max([rSpace, lSpace, mSpace]):
            adjs[0].add_car(self)
            adjs[0].num_cars += 1
            return True

def ahead_behind(myCar, myLane, road_len):
    '''
    Get the cars that are ahead and behind of myCar in the adjacent lane (myLane).
    '''
    p = myCar.posn
    behindCar = None
    minBehind = road_len
    for c in myLane.cars:
        d = p - c.posn
        if d > 0 and d < minBehind:
            minBehind = d
            behindCar = c
        else:
            d = d + road_len
            if d > 0 and d < minBehind:
                minBehind = d
                behindCar = c
    aheadCar = None
    minAhead = road_len
    for c in myLane.cars:
        d = c.posn - p
        if d > 0 and d < minAhead:
            minAhead = d
            aheadCar = c
        else:
            d = d + road_len
            if d > 0 and d < minAhead:
                minAhead = d
                aheadCar = c
    return (behindCar, aheadCar)

class Road:
    '''
    Class for a multilane road.
    '''
    def __init__(self, num_lanes, length, cars_per_lane):
        self.num_lanes = num_lanes
        self.length = length
        self.cars_per_lane = cars_per_lane
        self.lanes = [Lane(length, cars_per_lane) for _ in range(num_lanes)]

    def update(self):
        '''
        Update the lanes on the road, with some finite probability of a crash
        being introduced on a non-empty lane. No lane changing.
        '''
        for l in self.lanes:
            l.update()
            # randomly add car crash with low probability
            r = random.random()
            if r < .01:
                ind = random.randint(0, self.num_lanes-1)
                self.lanes[ind].crash_car()
                print("Adding a crash in lane " + str(ind))

    def update_wLC(self):
        '''
        Update the lanes on the road, with some finite probability of a crash
        being introduced on a non-empty lane. Lane changing permitted.
        '''
        for i, l in enumerate(self.lanes):
            adjs = [None, None]
            if i != 0:
                adjs[0] = self.lanes[i-1]
            if i != self.num_lanes - 1:
                adjs[1] = self.lanes[i+1]
            l.update_wLC(adjs)
            r = random.random()
            if r < .01:
                ind = random.randint(0, self.num_lanes-1)
                if self.lanes[ind].num_cars > 0:
                    self.lanes[ind].crash_car()
                    print("Adding a car crash in lane " + str(ind))

    def vel_vec(self):
        '''
        Get a vector of the velocities of all cars in all lanes for visualization
        purposes.
        '''
        vals = np.zeros((self.num_lanes, self.length)) - 1
        for i, l in enumerate(self.lanes):
            pVals = l.get_posns()
            vVals = l.get_vels()
            for (p, v) in zip(pVals, vVals):
                vals[i, p] = v
        return vals

r = Road(7, 300, 60)
vals = r.vel_vec()

fig = plt.figure(figsize=(20, 10))

im = plt.imshow(vals, vmin=-1, vmax=5, cmap='viridis', aspect='10')
cb = plt.colorbar(im)

def update_plot(i):
    print(i)
    r.update_wLC()
    vals = r.vel_vec()
    im.set_data(vals)
    return im


a = anim.FuncAnimation(fig, update_plot, frames=1000, interval=100, repeat=False)
