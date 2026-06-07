import pygame
import random
import cv2
import os

import src.vision.camera as camera
import src.vision.body_tracking as body_tracking
import src.game.player as player

# ==========================================
# SETTINGS
# ==========================================
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
SCALE = 2

# ==========================================
# INIT
# ==========================================
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("CV Dino Run")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)

GROUND_COLOR = (83, 83, 83)
BG_COLOR = (255, 255, 255)

# ==========================================
# HELPERS
# ==========================================
def scale_img(img):
    if img is None:
        return None
    w, h = img.get_size()
    return pygame.transform.scale(img, (w * SCALE, h * SCALE))

def trim_image(img):
    """
    Removes transparent empty space around a sprite so it sits flush on ground.
    """
    if img is None:
        return None
    try:
        rect = img.get_bounding_rect(min_alpha=1)
    except TypeError:
        rect = img.get_bounding_rect()
    
    trimmed = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    trimmed.blit(img, (0, 0), rect)
    return trimmed

# ==========================================
# LOAD ASSETS
# ==========================================
# Cacti (trimmed so no floating gaps)
cactus_images = []
for i in range(1, 7):
    path = f"assets/cacti/cactus{i}.png"
    if os.path.exists(path):
        raw = pygame.image.load(path).convert_alpha()
        trimmed = trim_image(raw)
        cactus_images.append(scale_img(trimmed))

# Birds
bird_images = []
for name in ["Ptero1.png", "Ptero2.png"]:
    path = f"assets/{name}"
    if os.path.exists(path):
        bird_images.append(scale_img(pygame.image.load(path).convert_alpha()))

# Cloud
cloud_img = None
if os.path.exists("assets/cloud.png"):
    cloud_img = scale_img(pygame.image.load("assets/cloud.png").convert_alpha())

# Sounds
jump_sound = None
score_sound = None
die_sound = None

try:
    jump_sound = pygame.mixer.Sound("assets/sfx/jump.mp3")
except:
    pass
try:
    score_sound = pygame.mixer.Sound("assets/sfx/100points.mp3")
except:
    pass
try:
    die_sound = pygame.mixer.Sound("assets/sfx/loose.mp3")
except:
    pass

# ==========================================
# SYSTEMS
# ==========================================
camera.init_camera()
body_tracking.setup_tracker()
player.load_dino_assets()
player.init_dino(x=80, ground_y=SCREEN_HEIGHT - 80)

# ==========================================
# GAME VARIABLES
# ==========================================
score = 0
high_score = 0
game_speed = 6
obstacles = []
clouds = []
spawn_timer = 0
bird_timer = 0
running = True
game_over = False
keyboard_duck = False

# ==========================================
# DRAW HELPERS
# ==========================================
def draw_ground():
    pygame.draw.line(screen, GROUND_COLOR,
                     (0, SCREEN_HEIGHT - 80),
                     (SCREEN_WIDTH, SCREEN_HEIGHT - 80), 4)

def draw_camera_preview(frame):
    small = cv2.resize(frame, (240, 180))
    small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    surf = pygame.image.frombuffer(small.tobytes(), (240, 180), 'RGB')
    screen.blit(surf, (SCREEN_WIDTH - 260, 10))

    line_y = int(body_tracking.jump_line_y * 180)
    pygame.draw.line(screen, (255, 0, 0),
                     (SCREEN_WIDTH - 260, 10 + line_y),
                     (SCREEN_WIDTH - 20, 10 + line_y), 2)

def spawn_cloud():
    if cloud_img and random.randint(0, 100) < 5:
        clouds.append({
            'x': SCREEN_WIDTH + random.randint(0, 200),
            'y': random.randint(20, 150),
            'speed': random.randint(1, 3)
        })

def can_spawn(gap):
    """Don't spawn if the last obstacle is still too close."""
    if len(obstacles) == 0:
        return True
    last = obstacles[-1]
    return last['x'] < SCREEN_WIDTH - gap  # min 350px gap

def spawn_cactus():
    if len(cactus_images) > 0 and can_spawn(350):
        img = random.choice(cactus_images)
        h = img.get_height()
        w = img.get_width()
        y = SCREEN_HEIGHT - 80 - h
        obstacles.append({
            'type': 'cactus',
            'img': img,
            'x': SCREEN_WIDTH,
            'y': y,
            'w': w,
            'h': h
        })

def spawn_bird():
    if len(bird_images) > 0 and can_spawn(500):
        img = bird_images[0]
        h = img.get_height()
        w = img.get_width()
        fly_y = random.choice([
            SCREEN_HEIGHT - 120,
            SCREEN_HEIGHT - 160,
            SCREEN_HEIGHT - 200
        ])
        obstacles.append({
            'type': 'bird',
            'imgs': bird_images,
            'x': SCREEN_WIDTH,
            'y': fly_y,
            'w': w,
            'h': h,
            'frame': 0,
            'timer': 0
        })

def reset_game():
    global score, game_speed, obstacles, clouds, spawn_timer, bird_timer, game_over
    score = 0
    game_speed = 6
    obstacles = []
    clouds = []
    spawn_timer = 0
    bird_timer = 0
    game_over = False
    player.init_dino(80, SCREEN_HEIGHT - 80)

# ==========================================
# GAME LOOP
# ==========================================
while running:
    # --- INPUT ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_SPACE:
                if game_over:
                    reset_game()
                else:
                    did_jump = player.jump_dino()
                    if did_jump and jump_sound:
                        jump_sound.play()

            elif event.key == pygame.K_UP:
                if not game_over:
                    did_jump = player.jump_dino()
                    if did_jump and jump_sound:
                        jump_sound.play()

            elif event.key == pygame.K_DOWN:
                if not game_over:
                    keyboard_duck = True      # <-- just set the flag

            # Blue jump line
            elif event.key == pygame.K_w:
                body_tracking.adjust_line(-0.02)
            elif event.key == pygame.K_s:
                body_tracking.adjust_line(0.02)

            # Red duck line
            elif event.key == pygame.K_a:
                body_tracking.adjust_duck_line(-0.02)
            elif event.key == pygame.K_d:
                body_tracking.adjust_duck_line(0.02)

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_DOWN:
                keyboard_duck = False         # <-- just clear the flag

    # ==========================================
    # GAME OVER SCREEN
    # ==========================================
    if game_over:
        screen.fill(BG_COLOR)
        draw_ground()

        for obs in obstacles:
            if obs['type'] == 'cactus':
                screen.blit(obs['img'], (obs['x'], obs['y']))
            else:
                screen.blit(obs['imgs'][obs['frame']], (obs['x'], obs['y']))

        player.draw_dino(screen)

        text = big_font.render("GAME OVER", True, (0, 0, 0))
        screen.blit(text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 50))

        restart = font.render("Press SPACE to restart", True, (100, 100, 100))
        screen.blit(restart, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 30))

        score_text = font.render(f"Score: {score}  High: {high_score}", True, GROUND_COLOR)
        screen.blit(score_text, (20, 20))

        pygame.display.flip()
        clock.tick(60)
        continue

    # ==========================================
    # COMPUTER VISION
    # ==========================================
    success, frame = camera.read_frame()
    jump_detected = False

    if success:
        jump_detected, duck_active, hip_y, _, frame = body_tracking.process_frame(frame)
        if jump_detected:
            did_jump = player.jump_dino()
            if did_jump and jump_sound:
                jump_sound.play()
        
        if duck_active or keyboard_duck:
            player.duck_dino()
        else:
            player.stop_duck()

    # ==========================================
    # UPDATE GAME
    # ==========================================
    player.update_dino()

    # Clouds
    spawn_cloud()
    for c in clouds:
        c['x'] -= c['speed']
    clouds = [c for c in clouds if c['x'] > -200]

    # Obstacles
    spawn_timer += 1
    bird_timer += 1

    # Cacti spawn farther apart (100-180 frames + 350px gap)
    if spawn_timer > random.randint(100, 180):
        spawn_cactus()
        spawn_timer = 0

    # Birds also spawn farther
    if bird_timer > random.randint(400, 800) and can_spawn(500):
        spawn_bird()
        bird_timer = 0

    # Move obstacles
    for obs in obstacles:
        obs['x'] -= game_speed

        if obs['type'] == 'bird':
            obs['timer'] += 1
            if obs['timer'] > 10:
                obs['timer'] = 0
                obs['frame'] = 1 - obs['frame']

    # Collision (tight hitboxes)
    dino_rect = player.get_dino_rect()
    margin = 5 * SCALE

    for obs in obstacles:
        obs_rect = pygame.Rect(
            obs['x'] + margin,
            obs['y'] + margin,
            obs['w'] - margin * 2,
            obs['h'] - margin * 2
        )

        if dino_rect.colliderect(obs_rect):
            game_over = True
            if score > high_score:
                high_score = score
            if die_sound:
                die_sound.play()
            break

    # Remove off-screen
    obstacles = [obs for obs in obstacles if obs['x'] > -150]

    # Score
    score += 1
    if score % 500 == 0:
        game_speed += 1

    if score % 500 == 0 and score > 0:
        if score_sound:
            score_sound.play()

    # ==========================================
    # DRAW
    # ==========================================
    screen.fill(BG_COLOR)

    # Clouds
    if cloud_img:
        for c in clouds:
            screen.blit(cloud_img, (c['x'], c['y']))

    draw_ground()

    # Obstacles
    for obs in obstacles:
        if obs['type'] == 'cactus':
            screen.blit(obs['img'], (obs['x'], obs['y']))
        else:
            screen.blit(obs['imgs'][obs['frame']], (obs['x'], obs['y']))

    # Dino
    player.draw_dino(screen)

    # UI
    score_text = font.render(f"Score: {score}  High: {high_score}", True, GROUND_COLOR)
    screen.blit(score_text, (20, 20))

    line_text = font.render(f"Line: {body_tracking.jump_line_y:.2f}", True, GROUND_COLOR)
    screen.blit(line_text, (20, 50))

    if success:
        draw_camera_preview(frame)

    pygame.display.flip()
    clock.tick(60)

# ==========================================
# CLEANUP
# ==========================================
camera.release_camera()
pygame.quit()