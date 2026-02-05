import pygame
import random
import sys

# --- Constants ---
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 700
FPS = 60

# Neon Color Palette
COLOR_BG = (10, 10, 20)           # Dark Navy/Black
COLOR_PLAYER = (0, 255, 255)      # Cyan
COLOR_BULLET = (255, 50, 50)      # Red/Orange
COLOR_ENEMY = (255, 0, 255)       # Magenta
COLOR_PARTICLE = (255, 255, 200)  # Yellow/White
COLOR_STAR = (200, 200, 255)

# Game Physics
PLAYER_SPEED = 5
PLAYER_FRICTION = 0.9
PLAYER_ACCEL = 0.8
BULLET_SPEED = 10
ENEMY_MIN_SPEED = 2
ENEMY_MAX_SPEED = 6

class Star(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.size = random.randint(1, 3)
        self.image = pygame.Surface((self.size, self.size))
        shade = random.randint(50, 150)
        self.image.fill((shade, shade, shade + 50))
        self.rect = self.image.get_rect(
            center=(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
        )
        self.speed = self.size * 0.5 # Parallax effect

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.rect.bottom = 0
            self.rect.x = random.randint(0, SCREEN_WIDTH)

class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        size = random.randint(2, 5)
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        direction = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        if direction.length() == 0:
            direction = pygame.math.Vector2(1, 0)
        self.velocity = direction.normalize() * random.randint(2, 6)
        self.life = random.randint(20, 40)

    def update(self):
        self.rect.centerx += self.velocity.x
        self.rect.centery += self.velocity.y
        self.life -= 1
        if self.life <= 0:
            self.kill()
        else:
            # Fade out effect (optional, requires per-frame surface creation or alpha blit)
            pass

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((6, 15))
        self.image.fill(COLOR_BULLET)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self):
        self.rect.y -= BULLET_SPEED
        if self.rect.bottom < 0:
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, COLOR_ENEMY, [(15, 0), (30, 15), (15, 30), (0, 15)])
        pygame.draw.polygon(self.image, (255, 200, 255), [(15, 5), (25, 15), (15, 25), (5, 15)])
        
        self.rect = self.image.get_rect(center=(random.randint(20, SCREEN_WIDTH-20), -20))
        self.speed_y = random.randint(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED)
        self.speed_x = random.choice([-1, 0, 1]) * random.random()

    def update(self):
        self.rect.y += self.speed_y
        self.rect.x += self.speed_x
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self, bullets_group):
        super().__init__()
        self.image = pygame.Surface((40, 50), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, COLOR_PLAYER, [(20, 0), (40, 50), (20, 40), (0, 50)])
        pygame.draw.polygon(self.image, (200, 255, 255), [(20, 10), (30, 45), (20, 35), (10, 45)])
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))
        
        self.velocity = pygame.math.Vector2(0, 0)
        self.position = pygame.math.Vector2(self.rect.center)
        self.bullets_group = bullets_group
        self.last_shot = 0
        self.shoot_delay = 200

    def update(self):
        self.handle_input()
        self.apply_physics()
        self.constrain_movement()

    def handle_input(self):
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()
        accel = pygame.math.Vector2(0, 0)
        
        # Movement: WASD
        if keys[pygame.K_a]: accel.x = -PLAYER_ACCEL
        if keys[pygame.K_d]: accel.x = PLAYER_ACCEL
        if keys[pygame.K_w]: accel.y = -PLAYER_ACCEL
        if keys[pygame.K_s]: accel.y = PLAYER_ACCEL
        
        # Shooting: Mouse left Click
        if mouse[0]: # left click
            self.shoot()
            
        if accel.length() > 0:
            accel = accel.normalize() * PLAYER_ACCEL
        self.velocity += accel

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullet = Bullet(self.rect.centerx, self.rect.top)
            self.bullets_group.add(bullet)

    def apply_physics(self):
        self.velocity *= PLAYER_FRICTION
        if self.velocity.length() < 0.1: self.velocity.update(0, 0)
        self.position += self.velocity
        self.rect.center = round(self.position.x), round(self.position.y)

    def constrain_movement(self):
        if self.rect.left < 0: self.rect.left = 0; self.position.x = self.rect.centerx; self.velocity.x = 0
        if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH; self.position.x = self.rect.centerx; self.velocity.x = 0
        if self.rect.top < 0: self.rect.top = 0; self.position.y = self.rect.centery; self.velocity.y = 0
        if self.rect.bottom > SCREEN_HEIGHT: self.rect.bottom = SCREEN_HEIGHT; self.position.y = self.rect.centery; self.velocity.y = 0

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Neon Space Shooter")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.game_over_font = pygame.font.Font(None, 72)
        
        self.reset_game()

    def reset_game(self):
        self.running = True
        self.game_active = True
        self.score = 0
        
        # Groups
        self.all_sprites = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.stars = pygame.sprite.Group()
        
        # Init Stars
        for _ in range(50):
            star = Star()
            self.stars.add(star)
            self.all_sprites.add(star)
            
        self.player = Player(self.bullets)
        self.all_sprites.add(self.player)
        
        self.enemy_timer = 0
        self.enemy_spawn_rate = 60

    def run(self):
        while self.running:
            self.handle_events()
            if self.game_active:
                self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if not self.game_active:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    self.reset_game()

    def update(self):
        self.spawn_enemies()
        self.all_sprites.update()
        self.bullets.update()
        self.enemies.update()
        self.particles.update()
        self.stars.update()
        
        # Bullet hits Enemy
        hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, True)
        for enemy in hits:
            self.score += 100
            for _ in range(10): # Explosion
                p = Particle(enemy.rect.centerx, enemy.rect.centery, COLOR_ENEMY)
                self.particles.add(p)
                self.all_sprites.add(p)

        # Enemy hits Player
        hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
        if hits:
            self.game_active = False # Game Over

    def spawn_enemies(self):
        self.enemy_timer += 1
        if self.enemy_timer >= self.enemy_spawn_rate:
            self.enemy_timer = 0
            enemy = Enemy()
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)
            if self.enemy_spawn_rate > 20: self.enemy_spawn_rate -= 0.1

    def draw(self):
        self.screen.fill(COLOR_BG)
        # Draw Scenery First
        self.stars.draw(self.screen)
        
        # Draw Game Objects
        self.all_sprites.draw(self.screen)
        self.bullets.draw(self.screen)
        self.particles.draw(self.screen)
        
        # Draw UI
        score_surf = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_surf, (10, 10))
        
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
