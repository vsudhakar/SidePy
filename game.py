import pygame
from pygame.locals import *
import sys

SCREEN_SIZE = (1280, 720) #resolution of the game
global HORIZ_MOV_INCR
HORIZ_MOV_INCR = 10 #speed of movement
global FPS
global clock
global time_spent

def RelRect(actor, camera):
    return pygame.Rect(actor.rect.x-camera.rect.x, actor.rect.y-camera.rect.y, actor.rect.w, actor.rect.h)

class Camera(object):
    '''Class for center screen on the player'''
    def __init__(self, screen, player, level_width, level_height):
        self.player = player
        self.rect = screen.get_rect()
        self.rect.center = self.player.center
        self.world_rect = Rect(0, 0, level_width, level_height)

    def update(self):
      if self.player.centerx > self.rect.centerx + 25:
          self.rect.centerx = self.player.centerx - 25
      if self.player.centerx < self.rect.centerx - 25:
          self.rect.centerx = self.player.centerx + 25
      if self.player.centery > self.rect.centery + 25:
          self.rect.centery = self.player.centery - 25
      if self.player.centery < self.rect.centery - 25:
          self.rect.centery = self.player.centery + 25
      self.rect.clamp_ip(self.world_rect)

    def draw_sprites(self, surf, sprites):
        for s in sprites:
            if s.rect.colliderect(self.rect):
                surf.blit(s.image, RelRect(s, self))


class Obstacle(pygame.sprite.Sprite):
    '''Class for create obstacles'''
    def __init__(self, x, y, moving = False):
        self.x = x
        self.y = y
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("world/backgroundInv.png").convert()
        self.rect = self.image.get_rect()
        self.rect.topleft = [self.x, self.y]
        self.direction = -1
        self.contactTop = False
        self.contactBottom = True
        self.moving = moving
        
    def update(self, level, world):
        if self.moving:
            if self.rect.top <= self.y-350:  #0
                self.direction = 1
            if self.rect.top >= self.y: #224
                self.direction = -1

            speed = 2
            self.rect.top += speed * self.direction

    def type(self):
        if self.moving:
            return "Moving Obstacle"
        else:
            return "Obstacle"

class Spike(pygame.sprite.Sprite):
    '''Class for creating spikes'''
    def __init__(self, x, y):
        self.x = x
        self.y = y
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("world/spike.png").convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.topleft = [self.x, self.y]

    def type(self):
        return "Spike"

class Mushroom(pygame.sprite.Sprite):
    ''' Class for instantiating mushrooms '''
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("world/mushroomInv.png").convert_alpha()
        self.x = x
        self.y = y
        self.rect = self.image.get_rect()
        self.rect.topleft = [x,y]

    def update(self, level, world):
        level.all_sprite.remove(self)
        world.remove(self)

    def type(self):
        return "Mushroom"

class FlameBall(pygame.sprite.Sprite):
    ''' Class for instantiating flame balls '''
    def __init__(self, x, y, world, direct = "R"):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load("world/flameBall.png").convert_alpha()
        self.x = x
        self.y = y
        self.rect = self.image.get_rect()
        self.rect.topleft = [x, y]
        self.active = True
        self.countdownTimer = 0
        self.contact = False
        self.direction = direct
        world.append(self)
        self.hit = False

    def update(self, level, world):
        if self.countdownTimer > 0:
            if self.countdownTimer == 10:
                # Remove self
                level.all_sprite.remove(self)
                self.active = False
            self.countdownTimer += 1
        else:
            world.remove(self)
            self.collide(level, world)
            # Move to the right or left
            direct = 1
            if self.direction == "L":
                direct = -1
            self.rect.right += 15 * direct
            print "Moved"
            world.append(self)

    def collide(self, level, world):
        # Check collision
        for o in world:
            if self.rect.colliderect(o):
                if o.type() == "Spike":
                    # Remove spike
                    level.all_sprite.remove(o)
                    world.remove(o) # Check this
                if o.type() == "Boss":
                    o.hurt()
                if o.type() == "Crashman":
                    print "Collide"
                    o.spikeRestart()
                self.image = pygame.image.load("world/flameCollide.png").convert_alpha()
                print "Collision!"
                self.countdownTimer += 1

    def type(self):
        if not self.hit:
            return "FlameBall"
        else:
            return "NaN"

class Boss(pygame.sprite.Sprite):
    ''' class for boss '''
    def __init__(self, x, y, world):
        pygame.sprite.Sprite.__init__(self)
        self.movy = 0
        self.movx = 0
        self.x = x
        self.y = y - 160
        self.image = pygame.image.load('world/boss.png').convert_alpha()
        self.rect = self.image.get_rect()
        self.direction = "right"
        self.frame = 0
        self.dead = False

        world.append(self)
        self.world = world

        scale = 0.5
        
        self.dimx = int(514 * scale)
        self.dimy = int(384 * scale)

        self.image = pygame.transform.scale(self.image, (self.dimx, self.dimy))
        self.rect = self.image.get_rect()
        self.rect.topleft = [self.x, self.y]

        print self.x

        #State
        self.states = ["shake", "leftCharge", "shake", "rightCharge", "shake", "leftCharge", "shake", "rightCharge", "leftFlame", "end"]
        self.state = 0

        self.shakeCounter = 0
        self.flameCounter = 0
        self.inc = 0

        self.hurting = 0
        self.damage = 0

    def update(self, level, world):
        if self.hurting > 0:
            if self.hurting >= 15:
                pos = self.rect.topleft
                self.image = pygame.image.load('world/boss.png').convert_alpha()
                self.image = pygame.transform.scale(self.image, (self.dimx, self.dimy))
                self.rect = self.image.get_rect()
                self.rect.topleft = pos
                self.hurting = 0
            else:
                self.hurt()
        
        elif self.states[self.state] == "shake":
            if self.shakeCounter < 25:
                if self.shakeCounter % 2 == 0:
                    self.rect.left += 3
                else:
                    self.rect.left -= 3
                self.shakeCounter += 1
            else:
                self.state += 1
                self.shakeCounter = 0
        
        elif self.states[self.state] == "leftCharge":
            pos = self.rect.topleft
            self.image = pygame.image.load('world/boss.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.dimx, self.dimy))
            self.rect = self.image.get_rect()
            self.rect.topleft = pos
            if self.rect.left > 35:
                self.rect.left -= 10
            else:
                self.state += 1

        elif self.states[self.state] == "rightCharge":
            pos = self.rect.topleft
            self.image = pygame.image.load('world/boss_rev.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.dimx, self.dimy))
            self.rect = self.image.get_rect()
            self.rect.topleft = pos
            if self.rect.left < 1175:
                self.rect.left += 10
            else:
                self.state += 1

        elif self.states[self.state] == "leftFlame":
            flameNumber = 6
            increment = 15

            if self.flameCounter < flameNumber and self.inc % increment == 0:
                flame = FlameBall(self.rect.left-100, self.rect.top + 30, world, "L")     
                level.all_sprite.add(flame)
                level.flameballs.append(flame)
                self.flameCounter += 1
                self.inc += 1
            elif self.flameCounter < flameNumber:
                self.inc += 1
            else:
                self.state += 1

        elif self.states[self.state] == "end":
            print "End"

    def hurt(self):
        if self.hurting == 0:
            self.damage += 1
            pos = self.rect.topleft
            self.image = pygame.image.load('world/boss_hurt.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.dimx, self.dimy))
            self.rect = self.image.get_rect()
            self.rect.topleft = pos
            self.hurting += 1
        else:
            self.hurting += 1
                

    def type(self):
        return "Boss"

class Crashman(pygame.sprite.Sprite):
    '''class for player and collision'''
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.movy = 0
        self.movx = 0
        self.x = x
        self.y = y
        self.contact = False
        self.jump = False
        self.image = pygame.image.load('actions/idle_right.png').convert()
        self.rect = self.image.get_rect()
        self.run_left = ["actions/run_left000.png","actions/run_left001.png",
                         "actions/run_left002.png", "actions/run_left003.png",
                         "actions/run_left004.png", "actions/run_left005.png",
                         "actions/run_left006.png", "actions/run_left007.png"]
        self.run_right = ["actions/run_right000.png","actions/run_right001.png",
                         "actions/run_right002.png", "actions/run_right003.png",
                         "actions/run_right004.png", "actions/run_right005.png",
                         "actions/run_right006.png", "actions/run_right007.png"]

        self.direction = "right"
        self.rect.topleft = [x, y]
        self.frame = 0
        self.dead = False

        self.crouching = False
        self.mushroom = False

        self.mushroomCountdown = 0

        self.health = 10

    def update(self, up, down, left, right, level, world):
        if not self.dead:
            if up:
                if self.contact:
                    if self.direction == "right":
                        self.image = pygame.image.load("actions/jump_right.png")
                    self.jump = True
                    self.movy -= 20
            if down:
                if self.contact and self.direction == "right":
                    self.image = pygame.image.load('actions/down_right.png').convert_alpha()
                if self.contact and self.direction == "left":
                    self.image = pygame.image.load('actions/down_left.png').convert_alpha()
                self.crouching = True

            if not down and self.direction == "right":
                    self.crouching = False
                    self.image = pygame.image.load('actions/idle_right.png').convert_alpha()

            if not down and self.direction == "left":
                self.crouching = False
                self.image = pygame.image.load('actions/idle_left.png').convert_alpha()

            if left:
                self.direction = "left"
                self.movx = -HORIZ_MOV_INCR
                if self.contact:
                    self.frame += 1
                    self.image = pygame.image.load(self.run_left[self.frame]).convert_alpha()
                    if self.frame == 6: self.frame = 0
                else:
                    self.image = self.image = pygame.image.load("actions/jump_left.png").convert_alpha()

            if right:
                self.direction = "right"
                self.movx = +HORIZ_MOV_INCR
                if self.contact:
                    self.frame += 1
                    self.image = pygame.image.load(self.run_right[self.frame]).convert_alpha()
                    if self.frame == 6: self.frame = 0
                else:
                    self.image = self.image = pygame.image.load("actions/jump_right.png").convert_alpha()

            if not (left or right):
                self.movx = 0
            self.rect.right += self.movx

            self.collide(self.movx, 0, level, world)

            if not self.contact:
                self.movy += 0.3
                if self.movy > 10:
                    self.movy = 10
                self.rect.top += self.movy

            if self.jump:

                self.movy += 2
                self.rect.top += self.movy
                if self.contact == True:
                    self.jump = False

            self.contact = False
            self.collide(0, self.movy, level, world)

            if self.mushroom:
                self.image = pygame.transform.scale(self.image, (43, 77))


            if self.mushroomCountdown > 0:
                self.mushroomCountdown += 1
            elif self.mushroomCountdown >= 6:
                self.mushroom = False

            if self.health <= 0:
                self.spikeRestart()

    def collide(self, movx, movy, level, world):
        self.contact = False
        for o in world:
            if self.rect.colliderect(o):
                if o.type() == "Spike":
                    if self.mushroom:
                        self.mushroom = False
                        level.all_sprite.remove(o)
                        world.remove(o) # Check this
                    else:
                        self.spikeRestart()
                if o.type() == "Boss":
                    if self.mushroom:
                        self.mushroom = False
                        self.mushroomCountdown += 10
                        o.hurt()
                    else:
                        self.health -= 1
                    
                if o.type() == "Mushroom":
                    o.update(level, world)
                    self.mushroom = True
                    self.mushroomResize()
                if o.type() == "FlameBall":
                    if self.mushroom:
                        self.mushroom = False
                        level.all_sprite.remove(o)
                        world.remove(o) # Check this
                    else:
                        o.image = pygame.image.load("world/flameCollide.png").convert_alpha()
                        print "Collision!"
                        self.health -= 1
                        o.hit = True
                    o.countdownTimer += 1
                if movx > 0 and o.type() != "Moving Obstacle":
                    self.rect.right = o.rect.left
                if movx < 0 and o.type() != "Moving Obstacle":
                    self.rect.left = o.rect.right
                if movy > 0:
                    self.rect.bottom = o.rect.top
                    self.movy = 0
                    self.contact = True
                if movy < 0:
                    self.rect.top = o.rect.bottom
                    self.movy = 0

    def spikeRestart(self):
        self.image = self.image = pygame.image.load("actions/jump_right.png").convert_alpha()

        self.dead = True

        if self.rect.top > -50:
            self.rect.top -= 10

        else:
           self.image = self.image = pygame.image.load("actions/idle_left.png").convert_alpha()
           self.image = self.image = pygame.image.load("actions/idle_right.png").convert_alpha()

    def shoot(self, level, world):
        if level.crashman.crouching:
            if level.crashman.direction == "left":
                flame = FlameBall(self.rect.right - 105, self.rect.top + 30, "L")
            else:
                flame = FlameBall(self.rect.right - 15, self.rect.top + 30)
        else:
            if level.crashman.direction == "left":
                flame = FlameBall(self.rect.right - 105, self.rect.top + 30, world, "L")
            else:
                flame = FlameBall(self.rect.right - 15, self.rect.top + 30, world)
        level.all_sprite.add(flame)
        level.flameballs.append(flame)

    def mushroomResize(self):
        self.rect.bottom -= 10

    def type(self):
        return "Crashman"

class Level(object):
    '''Read a map and create a level'''
    def __init__(self, open_level):
        self.level2 = []
        self.world = []
        self.all_sprite = pygame.sprite.Group()
        self.level = open(open_level, "r")
        self.obstacles = []
        self.flameballs = []
        self.mushrooms = []
        self.boss = None


    def create_level(self, x, y):
        for l in self.level:
            self.level2.append(l)

        for row in self.level2:
            for col in row:
                if col == "X":
                    obstacle = Obstacle(x, y)
                    self.world.append(obstacle)
                    self.all_sprite.add(self.world)
                if col == "Q":
                    obstacle = Obstacle(x, y, True)
                    self.world.append(obstacle)
                    self.all_sprite.add(self.world)
                    self.obstacles.append(obstacle)
                if col == "P":
                    self.crashman = Crashman(x,y)
                    self.all_sprite.add(self.crashman)
                if col == "S":
                    spike = Spike(x, y)
                    self.world.append(spike)
                    self.all_sprite.add(self.world)
                if col == "M":
                    mushroom = Mushroom(x, y)
                    self.world.append(mushroom)
                    self.mushrooms.append(mushroom)
                    self.all_sprite.add(self.world)
                if col == "B":
                    self.boss = Boss(x, y, self.world)
                    self.world.append(self.boss)
                    self.all_sprite.add(self.world)
                x += 25
            y += 25
            x = 0

    def get_size(self):
        lines = self.level2
        #line = lines[0]
        line = max(lines, key=len)
        self.width = (len(line))*25
        self.height = (len(lines))*25
        return (self.width, self.height)



def tps(orologio,fps):
    temp = orologio.tick(fps)
    tps = temp / 1000.
    return tps

def game():
    pygame.init()
    ##screen = pygame.display.set_mode(SCREEN_SIZE, FULLSCREEN, 32)
    screen = pygame.display.set_mode(SCREEN_SIZE)
    screen_rect = screen.get_rect()
    background = pygame.image.load("world/white.png").convert_alpha()
    background_rect = background.get_rect()


    level = Level("level/level5.txt")
    level.create_level(0,0)
    world = level.world
    crashman = level.crashman
    obstacles = level.obstacles
    boss = level.boss

    pygame.mouse.set_visible(0)

    camera = Camera(screen, crashman.rect, level.get_size()[0], level.get_size()[1])
    all_sprite = level.all_sprite

    FPS = 30
    clock = pygame.time.Clock()

    up = down = left = right = False
    x, y = 0, 0

    pygame.font.init()
    
    while True:


        for event in pygame.event.get():
            if event.type == QUIT or event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()

            if event.type == KEYDOWN and event.key == K_UP:
                up = True
            if event.type == KEYDOWN and event.key == K_DOWN:
                down = True
            if event.type == KEYDOWN and event.key == K_LEFT:
                left = True
            if event.type == KEYDOWN and event.key == K_RIGHT:
                right = True
            if event.type == KEYDOWN and event.key == K_SPACE:
                crashman.shoot(level, world)

            if event.type == KEYUP and event.key == K_UP:
                up = False
            if event.type == KEYUP and event.key == K_DOWN:
                down = False
            if event.type == KEYUP and event.key == K_LEFT:
                left = False
            if event.type == KEYUP and event.key == K_RIGHT:
                right = False

        asize = ((screen_rect.w // background_rect.w + 1) * background_rect.w, (screen_rect.h // background_rect.h + 1) * background_rect.h)
        bg = pygame.Surface(asize)

        for x in range(0, asize[0], background_rect.w):
            for y in range(0, asize[1], background_rect.h):
                screen.blit(background, (x, y))

        time_spent = tps(clock, FPS)
        camera.draw_sprites(screen, all_sprite)

        for obj in obstacles:
            obj.update(level, world)

        for fb in level.flameballs:
            if fb.active:
                fb.update(level, world)

        if not crashman.dead:
            crashman.update(up, down, left, right, level, world)

        camera.update()

        if not boss is None:
            boss.update(level, world)
            font = pygame.font.Font(None, 20)
            text = font.render("Health: " + str(crashman.health), 1, (10, 0, 0))
            screen.blit(text, (10, 10))

        pygame.display.flip()

        if crashman.dead:
            crashman.spikeRestart()
            break

    game()

game()
