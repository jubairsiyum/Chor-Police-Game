import pygame
import random
import heapq
import sys
import os

# --- CONFIGURABLE PARAMETERS ---
N = 8  # Board size
NUM_OBJECTS = 5
NUM_HIDING_SPOTS = 2
CELL_SIZE = 64
FPS = 30

# --- FILE NAMES ---
IMG_COP = "cop.png"
IMG_THIEF = "thief.png"
IMG_LOOT = "loot.png"
IMG_EXIT = "exit.png"
IMG_HIDE = "hide.png"

# --- COLORS ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
BG_COLOR = (30, 30, 30)

pygame.init()
font = pygame.font.SysFont("Arial", 24)
screen = pygame.display.set_mode((N * CELL_SIZE, N * CELL_SIZE + 60))
pygame.display.set_caption("Police vs Thief (Turn-based, Visuals)")

clock = pygame.time.Clock()

# --- Load Images ---
def load_and_scale(filename):
    img = pygame.image.load(filename).convert_alpha()
    return pygame.transform.smoothscale(img, (CELL_SIZE, CELL_SIZE))

img_cop = load_and_scale(IMG_COP)
img_thief = load_and_scale(IMG_THIEF)
img_loot = load_and_scale(IMG_LOOT)
img_exit = load_and_scale(IMG_EXIT)
img_hide = load_and_scale(IMG_HIDE)

def draw_board(thief_pos, police_pos, objects, exit_pos, collected, hiding_spots):
    screen.fill(BG_COLOR)
    for y in range(N):
        for x in range(N):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, GRAY if (x + y) % 2 == 0 else WHITE, rect)
            if (x, y) in hiding_spots:
                screen.blit(img_hide, rect)
            if (x, y) in objects:
                screen.blit(img_loot, rect)
            if (x, y) == exit_pos and collected:
                screen.blit(img_exit, rect)
    # Draw thief
    tx, ty = thief_pos
    screen.blit(img_thief, (tx * CELL_SIZE, ty * CELL_SIZE))
    # Draw police
    px, py = police_pos
    screen.blit(img_cop, (px * CELL_SIZE, py * CELL_SIZE))
    # Draw info
    info = f"Objects left: {len(objects)}"
    text = font.render(info, True, BLACK)
    screen.blit(text, (10, N * CELL_SIZE + 10))

def random_empty_cell(exclude):
    while True:
        pos = (random.randint(0, N-1), random.randint(0, N-1))
        if pos not in exclude:
            return pos

def neighbors(pos):
    x, y = pos
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        nx, ny = x+dx, y+dy
        if 0 <= nx < N and 0 <= ny < N:
            yield (nx, ny)

def manhattan(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def a_star(start, goal, obstacles=set()):
    heap = []
    heapq.heappush(heap, (0 + manhattan(start, goal), 0, start, [start]))
    visited = set()
    while heap:
        est, cost, node, path = heapq.heappop(heap)
        if node == goal:
            return path
        if node in visited:
            continue
        visited.add(node)
        for n in neighbors(node):
            if n in obstacles:
                continue
            heapq.heappush(heap, (cost+1+manhattan(n, goal), cost+1, n, path+[n]))
    return [start]

def thief_ai(thief_pos, police_pos, objects, exit_pos, collected, hiding_spots):
    avoid = {police_pos}
    # If on hiding spot, 50% chance to stay
    if thief_pos in hiding_spots and random.random() < 0.5:
        return thief_pos
    # If objects left, go to nearest object
    if objects:
        targets = list(objects)
        targets.sort(key=lambda o: manhattan(thief_pos, o))
        for target in targets:
            path = a_star(thief_pos, target, avoid)
            if len(path) > 1:
                return path[1]
    # If all objects collected, go to exit
    if collected:
        path = a_star(thief_pos, exit_pos, avoid)
        if len(path) > 1:
            return path[1]
    # Otherwise, stay
    return thief_pos

def show_message(msg, color):
    pygame.draw.rect(screen, BG_COLOR, (0, N * CELL_SIZE, N * CELL_SIZE, 60))
    text = font.render(msg, True, color)
    screen.blit(text, (N * CELL_SIZE // 2 - text.get_width() // 2, N * CELL_SIZE + 20))
    pygame.display.flip()
    pygame.time.wait(2000)

def main():
    thief_pos = (N-1, N-1)
    police_pos = (0, 0)
    exit_pos = (N-1, 0)
    objects = set()
    hiding_spots = set()
    exclude = {thief_pos, police_pos, exit_pos}
    while len(objects) < NUM_OBJECTS:
        obj = random_empty_cell(exclude)
        objects.add(obj)
        exclude.add(obj)
    while len(hiding_spots) < NUM_HIDING_SPOTS:
        h = random_empty_cell(exclude)
        hiding_spots.add(h)
        exclude.add(h)
    collected = False
    running = True
    win = None
    turn = "police"  # police moves first

    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        draw_board(thief_pos, police_pos, objects, exit_pos, collected, hiding_spots)
        pygame.display.flip()

        if turn == "police":
            moved = False
            while not moved:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN:
                        dx, dy = 0, 0
                        if event.key in [pygame.K_LEFT, pygame.K_a]:
                            dx = -1
                        elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                            dx = 1
                        elif event.key in [pygame.K_UP, pygame.K_w]:
                            dy = -1
                        elif event.key in [pygame.K_DOWN, pygame.K_s]:
                            dy = 1
                        new_police = (police_pos[0] + dx, police_pos[1] + dy)
                        if 0 <= new_police[0] < N and 0 <= new_police[1] < N and (dx != 0 or dy != 0):
                            police_pos = new_police
                            moved = True
                            break
            # Check win
            if police_pos == thief_pos:
                win = "Police"
                running = False
            turn = "thief"
        elif turn == "thief":
            # Thief move
            if thief_pos in objects:
                objects.remove(thief_pos)
            if len(objects) == 0:
                collected = True
            thief_pos = thief_ai(thief_pos, police_pos, objects, exit_pos, collected, hiding_spots)
            # Check win
            if police_pos == thief_pos:
                win = "Police"
                running = False
            elif collected and thief_pos == exit_pos:
                win = "Thief"
                running = False
            turn = "police"

    # End message
    if win == "Thief":
        show_message("Thief Escaped! You Lose!", (0, 120, 255))
    else:
        show_message("You Caught the Thief! You Win!", (255, 50, 50))
    pygame.time.wait(1000)

if __name__ == "__main__":
    while True:
        main()