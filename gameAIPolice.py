import pygame
import random
import heapq
import sys
import math

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
GRAY1 = (220, 220, 230)
GRAY2 = (180, 180, 200)
BG_GRAD1 = (40, 50, 80)
BG_GRAD2 = (20, 25, 40)
RED_ALERT = (255, 60, 60)
ALERT_ALPHA = 120

pygame.init()
font = pygame.font.SysFont("Segoe UI", 24, bold=True)
bigfont = pygame.font.SysFont("Segoe UI", 48, bold=True)
screen = pygame.display.set_mode((N * CELL_SIZE, N * CELL_SIZE + 90))
pygame.display.set_caption("Chor vs Police (Modern UI)")

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

def draw_gradient_background():
    for y in range(N * CELL_SIZE):
        color = [
            BG_GRAD1[i] + (BG_GRAD2[i] - BG_GRAD1[i]) * y // (N * CELL_SIZE)
            for i in range(3)
        ]
        pygame.draw.line(screen, color, (0, y), (N * CELL_SIZE, y))

def draw_board(thief_pos, police_pos, objects, exit_pos, collected, hiding_spots, looted, patrol_mode, alert_pulse):
    draw_gradient_background()
    # Draw grid with rounded cells
    for y in range(N):
        for x in range(N):
            rect = pygame.Rect(x * CELL_SIZE + 4, y * CELL_SIZE + 4, CELL_SIZE - 8, CELL_SIZE - 8)
            color = GRAY1 if (x + y) % 2 == 0 else GRAY2
            pygame.draw.rect(screen, color, rect, border_radius=16)
            # Hiding spot
            if (x, y) in hiding_spots:
                screen.blit(img_hide, (x * CELL_SIZE, y * CELL_SIZE))
            # Loot
            if (x, y) in objects and (x, y) not in looted:
                screen.blit(img_loot, (x * CELL_SIZE, y * CELL_SIZE))
            # Exit
            if (x, y) == exit_pos and collected:
                screen.blit(img_exit, (x * CELL_SIZE, y * CELL_SIZE))
    # Highlight cells
    pygame.draw.rect(screen, (0, 200, 255, 80), (thief_pos[0]*CELL_SIZE, thief_pos[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE), 5, border_radius=12)
    pygame.draw.rect(screen, (255, 80, 80, 80), (police_pos[0]*CELL_SIZE, police_pos[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE), 5, border_radius=12)
    # Draw thief and police
    screen.blit(img_thief, (thief_pos[0]*CELL_SIZE, thief_pos[1]*CELL_SIZE))
    screen.blit(img_cop, (police_pos[0]*CELL_SIZE, police_pos[1]*CELL_SIZE))

    # --- DARK OVERLAY BEFORE CHORI ---
    if not patrol_mode:
        dark_overlay = pygame.Surface((N * CELL_SIZE, N * CELL_SIZE), pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, 120))
        screen.blit(dark_overlay, (0, 0))
        suspense = font.render("Steal a loot to trigger the alarm!", True, (220, 220, 220))
        screen.blit(suspense, (N * CELL_SIZE // 2 - suspense.get_width() // 2, N * CELL_SIZE // 2 - 30))
    else:
        # --- RED ALERT EFFECT ---
        alert_overlay = pygame.Surface((N * CELL_SIZE, N * CELL_SIZE), pygame.SRCALPHA)
        alert_overlay.fill((255, 0, 0, int(40 + 40 * alert_pulse)))
        screen.blit(alert_overlay, (0, 0))
        # Police glow
        glow = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 0, 0, int(120 + 80 * alert_pulse)), [0, 0, CELL_SIZE, CELL_SIZE])
        screen.blit(glow, (police_pos[0]*CELL_SIZE, police_pos[1]*CELL_SIZE))
        # RED ALERT banner (animated)
        alert_text = bigfont.render("RED ALERT!", True, (255, 0, 0))
        y_offset = int(10 + 10 * math.sin(pygame.time.get_ticks() / 200))
        screen.blit(alert_text, (N * CELL_SIZE // 2 - alert_text.get_width() // 2, 10 + y_offset))

    # --- INFO BAR ---
    info_bar = pygame.Surface((N * CELL_SIZE, 90), pygame.SRCALPHA)
    info_bar.fill((30, 30, 40, 220))
    screen.blit(info_bar, (0, N * CELL_SIZE))
    # Icons
    screen.blit(img_loot, (10, N * CELL_SIZE + 10))
    loot_text = font.render(f"{len(objects) - len(looted)}", True, WHITE)
    screen.blit(loot_text, (50, N * CELL_SIZE + 18))
    screen.blit(img_exit, (100, N * CELL_SIZE + 10))
    # Status
    if patrol_mode:
        status = font.render("Police is chasing you!", True, RED_ALERT)
    else:
        status = font.render("Police is patrolling...", True, (180, 180, 180))
    screen.blit(status, (160, N * CELL_SIZE + 25))

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

def police_ai(police_pos, thief_pos, patrol_mode, patrol_path, looted, objects):
    if not patrol_mode:
        moves = list(neighbors(police_pos))
        return random.choice(moves), patrol_path
    else:
        path = a_star(police_pos, thief_pos)
        if len(path) > 1:
            return path[1], path
        else:
            return police_pos, path

def show_message(msg, color):
    overlay = pygame.Surface((N * CELL_SIZE, N * CELL_SIZE + 90), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    screen.blit(overlay, (0, 0))
    text = bigfont.render(msg, True, color)
    screen.blit(text, (N * CELL_SIZE // 2 - text.get_width() // 2, N * CELL_SIZE // 2 - 24))
    pygame.display.flip()
    pygame.time.wait(2000)

def main():
    thief_pos = (0, 0)
    police_pos = (N-1, N-1)
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
    looted = set()
    patrol_mode = False
    patrol_path = []
    alert_pulse = 0

    while running:
        clock.tick(FPS)
        alert_pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 300)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        draw_board(thief_pos, police_pos, objects, exit_pos, collected, hiding_spots, looted, patrol_mode, alert_pulse)
        pygame.display.flip()

        # --- Thief (user) move ---
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
                    new_thief = (thief_pos[0] + dx, thief_pos[1] + dy)
                    if 0 <= new_thief[0] < N and 0 <= new_thief[1] < N and (dx != 0 or dy != 0):
                        thief_pos = new_thief
                        moved = True
                        break
        # Loot collect
        if thief_pos in objects and thief_pos not in looted:
            looted.add(thief_pos)
        if len(looted) == len(objects):
            collected = True

        # --- Police (AI) move ---
        if not patrol_mode and len(looted) > 0:
            patrol_mode = True  # Police saw a looted object, start chasing

        police_pos, patrol_path = police_ai(police_pos, thief_pos, patrol_mode, patrol_path, looted, objects)

        # --- Check win/lose ---
        if patrol_mode and police_pos == thief_pos:
            win = "Police"
            running = False
        elif collected and thief_pos == exit_pos:
            win = "Thief"
            running = False

    # End message
    if win == "Thief":
        show_message("You Escaped! You Win!", (0, 220, 255))
    else:
        show_message("Police Caught You! You Lose!", (255, 60, 60))
    pygame.time.wait(1000)

if __name__ == "__main__":
    while True:
        main()