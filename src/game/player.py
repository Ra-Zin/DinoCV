import pygame

# CHANGE THIS if you want bigger/smaller sprites
SCALE = 2

# State
dino_x = 0
dino_y = 0
dino_vel_y = 0
dino_is_jumping = False
dino_ground_y = 0
gravity = 0.6
jump_power = -16

dino_state = "run"
dino_frame = 0
dino_anim_timer = 0
dino_anim_speed = 5

img_run = [None, None]
img_jump = None
img_duck = [None, None]

def scale_img(img):
    if img is None:
        return None
    w, h = img.get_size()
    return pygame.transform.scale(img, (w * SCALE, h * SCALE))

def load_dino_assets():
    global img_run, img_jump, img_duck
    img_run[0] = scale_img(pygame.image.load("../assets/Dino1.png").convert_alpha())
    img_run[1] = scale_img(pygame.image.load("../assets/Dino2.png").convert_alpha())
    img_jump = scale_img(pygame.image.load("../assets/DinoJumping.png").convert_alpha())
    img_duck[0] = scale_img(pygame.image.load("../assets/DinoDucking1.png").convert_alpha())
    img_duck[1] = scale_img(pygame.image.load("../assets/DinoDucking2.png").convert_alpha())

def init_dino(x, ground_y):
    global dino_x, dino_y, dino_vel_y, dino_is_jumping, dino_ground_y
    global dino_state, dino_frame, dino_anim_timer
    dino_x = x
    dino_ground_y = ground_y
    dino_state = "run"
    dino_frame = 0
    dino_anim_timer = 0
    dino_vel_y = 0
    dino_is_jumping = False
    h = img_run[0].get_height() if img_run[0] else 46 * SCALE
    dino_y = ground_y - h

def jump_dino():
    global dino_vel_y, dino_is_jumping, dino_state
    if not dino_is_jumping:
        dino_vel_y = jump_power
        dino_is_jumping = True
        dino_state = "jump"
        return True      # ← actually jumped
    return False         # ← was already in the air, no jump

def duck_dino():
    global dino_state, dino_y
    if dino_state != "jump":
        dino_state = "duck"
        img = get_current_image()
        if img:
            dino_y = dino_ground_y - img.get_height()

def stop_duck():
    global dino_state, dino_y
    if dino_state == "duck":
        dino_state = "run"
        img = get_current_image()
        if img:
            dino_y = dino_ground_y - img.get_height()

def get_current_image():
    if dino_state == "jump":
        return img_jump
    elif dino_state == "duck":
        return img_duck[dino_frame]
    else:
        return img_run[dino_frame]

def update_dino():
    global dino_y, dino_vel_y, dino_is_jumping, dino_state
    global dino_frame, dino_anim_timer

    dino_vel_y += gravity
    dino_y += dino_vel_y

    img = get_current_image()
    img_h = img.get_height() if img else 46 * SCALE

    if dino_y >= dino_ground_y - img_h:
        dino_y = dino_ground_y - img_h
        dino_vel_y = 0
        if dino_is_jumping:
            dino_is_jumping = False
            dino_state = "run"

    if dino_state in ("run", "duck"):
        dino_anim_timer += 1
        if dino_anim_timer >= dino_anim_speed:
            dino_anim_timer = 0
            dino_frame = 1 - dino_frame

def draw_dino(screen):
    img = get_current_image()
    if img:
        # Push sprite down a few pixels so feet touch the line
        offset = 4 * SCALE
        screen.blit(img, (dino_x, dino_y + offset))


def get_dino_rect():
    img = get_current_image()
    if img:
        w, h = img.get_size()
        # Shrink hitbox so you don't die from empty space around the sprite
        margin = 8 * SCALE
        offset = 4 * SCALE
        return pygame.Rect(dino_x + margin, dino_y + margin + offset, w - margin * 2, h - margin * 2)
    else:
        return pygame.Rect(dino_x, dino_y, 44 * SCALE, 46 * SCALE)