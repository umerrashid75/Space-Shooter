import pygame
import random
import sys
import math

# --- Constants ---
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 700
FPS = 60

# Layers (Z-Index)
LAYER_BG = 0
LAYER_STAR = 1
LAYER_PARTICLE = 2
LAYER_ENEMY = 3
LAYER_PLAYER = 4
LAYER_BULLET = 5
LAYER_UI = 6

# Neon Color Palette
COLOR_BG = (10, 10, 20)           # Dark Navy/Black
COLOR_PLAYER = (0, 255, 255)      # Cyan
COLOR_BULLET = (255, 50, 50)      # Red/Orange
COLOR_ENEMY = (255, 0, 255)       # Magenta
COLOR_PARTICLE = (255, 255, 200)  # Yellow/White

# Game Physics (Pixels per Second)
PLAYER_MAX_SPEED = 500
PLAYER_ACCEL = 3000
PLAYER_FRICTION = 10 # Linear friction
BULLET_SPEED = 800
ENEMY_MIN_SPEED = 100
ENEMY_MAX_SPEED = 300

class Star(pygame.sprite.Sprite):
    def __init__(self, groups, layer):
        super().__init__(groups)
        self._layer = layer
        self.size = random.randint(1, 3)
        self.image = pygame.Surface((self.size, self.size))
        shade = random.randint(50, 150)
        self.image.fill((shade, shade, shade + 50))
        self.image = self.image.convert() # Optimization
        self.rect = self.image.get_rect(
            center=(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
        )
        self.speed = self.size * 20 # Parallax speed scaled

    def update(self, dt):
        self.rect.y += self.speed * dt
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.bottom = 0
            self.rect.x = random.randint(0, SCREEN_WIDTH)

class Particle(pygame.sprite.Sprite):
    def __init__(self, groups, x, y, color, size_range=(2,5), speed_range=(50, 200), life_range=(0.5, 1.0)):
        super().__init__(groups)
        self._layer = LAYER_PARTICLE
        size = random.randint(*size_range)
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.image = self.image.convert()
        self.rect = self.image.get_rect(center=(x, y))
        
        angle = random.uniform(0, 360)
        speed = random.uniform(*speed_range)
        self.velocity = pygame.math.Vector2(speed, 0).rotate(angle)
        
        self.life = random.uniform(*life_range)
        self.initial_life = self.life
        self.color = color

    def update(self, dt):
        self.rect.centerx += self.velocity.x * dt
        self.rect.centery += self.velocity.y * dt
        self.life -= dt
        
        if self.life <= 0:
            self.kill()
        
        # Fading (Alpha)
        alpha = int((self.life / self.initial_life) * 255)
        # Note: set_alpha works best on converted surfaces, may need convert_alpha if transparency matters
        # Ideally, we recreate surface or blit with special flags, but simple alpha toggle is okay.
        # For colored squares, fading is tricky without convert_alpha.
        # Let's simple-hack: Shrink it? Or just let it pop.
        # Actually proper alpha fade:
        self.image.set_alpha(alpha)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, groups, x, y):
        super().__init__(groups)
        self._layer = LAYER_BULLET
        self.image = pygame.Surface((6, 15))
        self.image.fill(COLOR_BULLET)
        self.image = self.image.convert()
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.display_y = float(self.rect.y)

    def update(self, dt):
        self.display_y -= BULLET_SPEED * dt
        self.rect.y = round(self.display_y)
        if self.rect.bottom < 0:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, groups, speed_modifier=0):
        super().__init__(groups)
        self._layer = LAYER_ENEMY
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, COLOR_ENEMY, [(15, 0), (30, 15), (15, 30), (0, 15)])
        pygame.draw.polygon(self.image, (255, 200, 255), [(15, 5), (25, 15), (15, 25), (5, 15)])
        self.image = self.image.convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)
        
        self.rect = self.image.get_rect(center=(random.randint(20, SCREEN_WIDTH-20), -20))
        
        speed_max = ENEMY_MAX_SPEED + speed_modifier
        self.speed_y = random.randint(ENEMY_MIN_SPEED, int(speed_max))
        
        # Sine Wave AI
        self.t = random.uniform(0, 360) 
        self.freq = random.uniform(2, 5)
        self.amp = random.uniform(50, 150) # Horizontal range
        self.center_x = float(self.rect.centerx)
        self.display_y = float(self.rect.centery)

    def update(self, dt):
        self.display_y += self.speed_y * dt
        self.t += dt
        
        # Sine wave horizontal movement
        offset_x = math.sin(self.t * self.freq) * self.amp
        self.rect.centerx = round(self.center_x + offset_x)
        self.rect.centery = round(self.display_y)
        
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self, groups, bullets_group):
        super().__init__(groups)
        self._layer = LAYER_PLAYER
        self.image = pygame.Surface((40, 50), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, COLOR_PLAYER, [(20, 0), (40, 50), (20, 40), (0, 50)])
        pygame.draw.polygon(self.image, (200, 255, 255), [(20, 10), (30, 45), (20, 35), (10, 45)])
        self.image = self.image.convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)
        
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        
        self.velocity = pygame.math.Vector2(0, 0)
        self.position = pygame.math.Vector2(self.rect.center)
        
        self.groups_ref = groups # To spawn bullets/particles
        self.bullets_group = bullets_group
        self.last_shot = 0
        self.shoot_delay = 0.2 # Seconds

    def update(self, dt):
        self.handle_input(dt)
        self.apply_physics(dt)
        self.constrain_movement()

    def handle_input(self, dt):
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()
        accel = pygame.math.Vector2(0, 0)
        
        if keys[pygame.K_a]: accel.x = -PLAYER_ACCEL
        if keys[pygame.K_d]: accel.x = PLAYER_ACCEL
        if keys[pygame.K_w]: accel.y = -PLAYER_ACCEL
        if keys[pygame.K_s]: accel.y = PLAYER_ACCEL
        
        # Shooting
        if mouse[0]: # Left Click
            self.shoot()
            
        if accel.length() > 0:
            accel = accel.normalize() * PLAYER_ACCEL
            
             # Thruster Juice
            if keys[pygame.K_w]:
               self.spawn_thrusters()

        self.velocity += accel * dt

    def spawn_thrusters(self):
        # Spawn particles at bottom
        for _ in range(2):
           offset_x = random.randint(-10, 10)
           Particle(self.groups_ref, self.rect.centerx + offset_x, self.rect.bottom, (0, 255, 255), 
                    size_range=(2,4), speed_range=(50, 100), life_range=(0.1, 0.3))

    def shoot(self):
        now = pygame.time.get_ticks() / 1000.0 # Current time in seconds
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            Bullet(self.groups_ref, self.rect.centerx, self.rect.top)
            # TODO: Mixer play sound

    def apply_physics(self, dt):
        # Friction
        self.velocity -= self.velocity * PLAYER_FRICTION * dt
        
        self.position += self.velocity * dt
        self.rect.center = round(self.position.x), round(self.position.y)

    def constrain_movement(self):
        if self.rect.left < 0: self.rect.left = 0; self.position.x = self.rect.centerx; self.velocity.x = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH; self.position.x = self.rect.centerx; self.velocity.x = 0
        if self.rect.top < 0: self.rect.top = 0; self.position.y = self.rect.centery; self.velocity.y = 0
        if self.rect.bottom > SCREEN_HEIGHT: self.rect.bottom = SCREEN_HEIGHT; self.position.y = self.rect.centery; self.velocity.y = 0

class Game:
    def __init__(self):
        pygame.init()
        # TODO: Mixer Init
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Neon Space Shooter Redux")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.game_over_font = pygame.font.Font(None, 72)
        
        self.high_score = 0
        self.reset_game()

    def reset_game(self):
        self.running = True
        self.game_active = True
        self.score = 0
        self.shake_timer = 0
        
        # Use LayeredUpdates for automatic Z-sorting
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        
        # Init Stars
        for _ in range(50):
            Star(self.all_sprites, LAYER_STAR)
            
        self.player = Player(self.all_sprites, self.bullets)
        
        self.enemy_timer = 0
        self.enemy_spawn_rate = 1.0 # Seconds

    def run(self):
        while self.running:
            # Delta Time Calculation (in seconds)
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            if self.game_active:
                self.update(dt)
            self.draw()
            
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if not self.game_active:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.reset_game()

    def update(self, dt):
        self.spawn_enemies(dt)
        self.all_sprites.update(dt)
        
        # Screen Shake decay
        if self.shake_timer > 0:
            self.shake_timer -= dt
        
        # Collision: Bullet -> Enemy
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True, pygame.sprite.collide_mask)
        for enemy in hits:
            self.score += 100
            self.trigger_shake(0.2)
            # TODO: Play explosion sound
            
            # Explosion Particles
            for _ in range(15):
                Particle(self.all_sprites, enemy.rect.centerx, enemy.rect.centery, COLOR_ENEMY)
        
        # Collision: Enemy -> Player
        hits = pygame.sprite.spritecollide(self.player, self.enemies, False, pygame.sprite.collide_mask)
        if hits:
            self.game_over()

    def spawn_enemies(self, dt):
        self.enemy_timer += dt
        if self.enemy_timer >= self.enemy_spawn_rate:
            self.enemy_timer = 0
            
            # Increase difficulty
            speed_mod = (self.score // 1000) * 50
            Enemy(self.all_sprites, speed_modifier=speed_mod)
            
            # Spawn rate cap
            target_rate = max(0.2, 1.0 - (self.score / 5000.0))
            self.enemy_spawn_rate = target_rate

    def trigger_shake(self, duration):
        self.shake_timer = duration

    def game_over(self):
        self.game_active = False
        if self.score > self.high_score:
            self.high_score = self.score

    def draw(self):
        # Screen Shake Offset
        offset_x = 0
        offset_y = 0
        if self.shake_timer > 0:
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            
        # Clear screen (could be optimized with dirty rects, but fill is fine for this scale)
        self.screen.fill(COLOR_BG)
        
        # We need to draw all sprites with the offset.
        # LayeredUpdates.draw() draws to surface directly.
        # To shake, we can create a temporary surface or just iterate and blit manually?
        # Or simpler: blit everything to a 'world_surf' then blit world_surf to screen with offset.
        
        # Optimziation: Just blit the screen normally, then blit a copy? No, that's heavy.
        # Let's simple-hack: Use loop for drawing if shaking, or just accept that background shakes too.
        # Actually, standard pygame.sprite.Group.draw defaults to (0,0).
        # We can implement a custom draw or just blit a persistent surface.
        
        # Easiest way for "Juice":
        if self.shake_timer > 0:
            shake_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            shake_surf.fill(COLOR_BG)
            self.all_sprites.draw(shake_surf)
            self.screen.blit(shake_surf, (offset_x, offset_y))
        else:
            self.all_sprites.draw(self.screen)

        # UI (Draw after shake so it stays static? or Shake it too? Static is better for readability)
        score_surf = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        high_surf = self.font.render(f"High Score: {self.high_score}", True, (255, 215, 0))
        
        self.screen.blit(score_surf, (10, 10))
        self.screen.blit(high_surf, (10, 50))
        
        if not self.game_active:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            go_surf = self.game_over_font.render("GAME OVER", True, (255, 50, 50))
            go_rect = go_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            self.screen.blit(go_surf, go_rect)
            
            restart_surf = self.font.render("Press 'R' to Restart", True, (200, 200, 200))
            restart_rect = restart_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
            self.screen.blit(restart_surf, restart_rect)
            
        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()
