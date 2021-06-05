import math
import random

from shapely.geometry.point import Point

from simpleai.search import SearchProblem

from arrakis.poly import generate_random


def rotateAboutPoint(ox, oy, px, py, angle):
    nx = ox + math.cos(angle)*(px-ox)-math.sin(angle)*(py-oy)
    ny = oy + math.sin(angle)*(px-ox)+math.cos(angle)*(py-oy)
    return nx, ny


def shiftFromPoint(ox, oy, px, py, delta):
    if -1 < px-ox < 1:
        # slope is practically vertical in px dimensions
        return px, px + delta
    m = (py-oy)/(px-ox)
    nx = px + delta
    ny = py + m*delta + oy
    return nx, ny


def distance(ox, oy, px, py):
    return math.sqrt((ox-px)**2+(oy-py)**2)


def mutant(state, polygon):
    ox, oy = polygon.centroid.x, polygon.centroid.y
    px, py = state
    rnd = random.random()
    if rnd < 0.5:
        angle = 2*math.pi*random.random()
        return rotateAboutPoint(ox, oy, px, py, angle)
    else:
        delta = (1 if random.random() < 0.5 else -1)*random.random()*distance(ox, oy, px, py)
        return shiftFromPoint(ox, oy, px, py, delta)


class TokenPlacementProblem(SearchProblem):
    def __init__(self, polygons_maximize_overlap, polygons_avoid_overlap_areas, target_radius, tolerance=0.1, initial_state=None):
        self.polygons_maximize_overlap = polygons_maximize_overlap
        self.polygons_avoid_overlap_areas = polygons_avoid_overlap_areas
        self.target_radius = target_radius
        self.tolerance = tolerance
        if initial_state is None:
            initial_state = self.generate_random_state()
        super().__init__(initial_state=initial_state)

    def polygonize(self, state):
        x, y = state
        state_center = Point(x, y)
        return state_center.buffer(self.target_radius)

    def heuristic(self, state):
        # how far are we from the goal?
        bad = 0
        state_polygon = self.polygonize(state)
        for avoid in self.polygons_avoid_overlap_areas:
            area = state_polygon.intersection(avoid).area
            bad += area**3
        overlap = (state_polygon.intersection(self.polygons_maximize_overlap).area)
        if overlap < state_polygon.area - self.tolerance:
            centroid = self.polygons_maximize_overlap.centroid
            px, py = state
            ox, oy = centroid.x, centroid.y
            bad += ((px - ox)**2 + (py - oy)**2)**5
        else:
            bad -= overlap
        return bad

    def crossover(self, state1, state2):
        x1, y1 = state1
        x2, y2 = state2
        rnd = random.random()
        if rnd < 0.5:
            return x1, y2
        else:
            return x2, y1

    def mutate(self, state):
        return mutant(state, self.polygons_maximize_overlap)

    def generate_random_state(self):
        state_center = generate_random(1, self.polygons_maximize_overlap, centroid=True)[0]
        state = state_center.x, state_center.y
        return state

    def value(self, state):
        # how good is this state?
        return -self.heuristic(state)


class MultiTokenPlacementProblem(SearchProblem):
    def __init__(self, polygons_maximize_overlap, polygons_avoid_overlap_areas, target_radii, tolerance=0.1, initial_state=None):
        self.N = len(target_radii)
        self.polygons_maximize_overlap = polygons_maximize_overlap
        self.polygons_avoid_overlap_areas = polygons_avoid_overlap_areas
        self.target_radii = target_radii
        self.tolerance = tolerance
        if initial_state is None:
            initial_state = self.generate_random_state()
        super().__init__(initial_state=initial_state)

    def polygonize(self, state, radius):
        x, y = state
        state_center = Point(x, y)
        return state_center.buffer(radius)

    # slow, but not meant to be used for more than
    # N=2 or N=3 polygons simultaneously
    def heuristic(self, state):
        # how far are we from the goal?
        bad = 0
        for j in range(self.N):
            px, py = state[2*j], state[2*j+1]
            radius = self.target_radii[j]
            state_polygon = self.polygonize((px, py), radius)
            for avoid in self.polygons_avoid_overlap_areas:
                area = state_polygon.intersection(avoid).area
                bad += area**3
            overlap = (state_polygon.intersection(self.polygons_maximize_overlap).area)
            if overlap < state_polygon.area - self.tolerance:
                centroid = self.polygons_maximize_overlap.centroid
                # ox, oy = centroid.x, centroid.y
                # bad += ((px - ox)**2 + (py - oy)**2)**6
                bad += state_polygon.area - overlap
                # print('punish')
            #else:
            #    bad -= overlap
            for k in range(j+1, self.N):
                pkx, pky = state[2*k], state[2*k+1]
                radiusk = self.target_radii[k]
                state_polygon_k = self.polygonize((pkx, pky), radiusk)
                collision = state_polygon.intersection(state_polygon_k).area
                bad += collision
        return bad

    def crossover(self, mother, father):
        rnd = random.random()
        child = list(mother)
        # how much inherited from father?
        N = random.randint(1, self.N)
        charm = random.sample(list(range(self.N)), N)
        for j in charm:
            child[2*j] = father[2*j]
            child[2*j+1] = father[2*j+1]
        #if N == 0:
        #    N = random.randint(0, self.N)
        #    avgs = random.sample(list(range(self.N)), N)
        #    for j in avgs:
        #        child[2*j] = (father[2*j]+mother[2*j])/2
        #        child[2*j+1] = (father[2*j]+mother[2*j])/2
        return child

    def mutate(self, state):
        N = random.randint(1, self.N)
        xmen = random.sample(list(range(self.N)), N)
        mutated = list(state)
        for j in xmen:
            px, py = state[2*j], state[2*j+1]
            nx, ny = mutant((px, py), self.polygons_maximize_overlap)
            mutated[2*j] = nx
            mutated[2*j+1] = ny
        return mutated

    def generate_random_state(self):
        state_centers = generate_random(self.N, self.polygons_maximize_overlap, centroid=True)
        state = []
        for state_center in state_centers:
            state.append(state_center.x)
            state.append(state_center.y)
        return state

    def value(self, state):
        # how good is this state?
        return -self.heuristic(state)
