import math

from simpleai.search import SearchProblem

from poly import generate_random


class TokenPlacementProblem(SearchProblem):
    def __init__(self, polygons_maximize_overlap, polygons_avoid_overlap_areas, target_radius, tolerance=0.1, initial_state=None):
        self.polygons_maximize_overlap = polygons_maximize_overlap
        self.polygons_avoid_overlap_areas = polygons_avoid_overlap_areas
        self.target_radius = target_radius
        self.tolerance = tolerance
        if initial_state is None:
            initial_state = self.generate_random_state()
        super().__init__(initial_state=initial_state)

    def actions(self, state):
        possible_actions = []
        state_polygon = self.polygonize(state)
        centroid = self.polygons_maximize_overlap.centroid
        ox, oy = centroid.x, centroid.y
        px, py = state
        angles = [math.pi*i/12 for i in range(1, 25)]
        rotations = [
            tuple([math.cos(angle)*(px-ox)-math.sin(angle)*(py-oy), math.sin(angle)*(px-ox)+math.cos(angle)*(py-oy)]) for angle in angles]
        if px-ox > 1:
            m = (py-oy)/(px-ox)
            trs = [-60, -40, -20, -10, -5, 5, 10, 20, 40, 60]
            translations = [(x, m*x+oy) for x in trs]
            return rotations + translations
        return rotations

    def result(self, state, action):
        xoff, yoff = action
        centroid = self.polygons_maximize_overlap.centroid
        x, y = centroid.x, centroid.y
        return x+xoff, y+yoff

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
        # cross both strings, at a random point
        actions = self.actions(state)
        action = random.sample(actions, 1)[0]
        mutated = self.result(state, action)
        return mutated

    def generate_random_state(self):
        state_center = generate_random(1, self.polygons_maximize_overlap, centroid=True)[0]
        state = state_center.x, state_center.y
        return state

    def value(self, state):
        # how good is this state?
        return -self.heuristic(state)
