import pygame
import sounddevice as sd
import numpy as np
pygame.init()
font=pygame.font.SysFont(None,48)
small_font=pygame.font.SysFont(None,24)
width, height = 800, 400
screen= pygame.display.set_mode((width, height))
pygame.display.set_caption("GoGo")
clock= pygame.time.Clock()
ground_y=300
def get_decibel(duration=0.04):
    recording=sd.rec(
        int(duration*44100),
        samplerate=44100,
        channels=1,
        dtype='float64'
    )
    sd.wait()
    rms=np.sqrt(np.mean(recording**2))
    if rms==0:
        return -60
    return 20*np.log10(rms)

class Player:
    def __init__(self):
        self.x=120
        self.y=ground_y+20
        self.radius=20
        self.velocity_y=0
        self.gravity=0.8
        self.jump_strength=-12
        self.speed_x=3
    def jump(self):
        if self.on_ground():
            self.velocity_y=self.jump_strength
    def on_ground(self):
        return self.y >= ground_y + self.radius
    def update(self):
        self.velocity_y+=self.gravity
        self.y+=self.velocity_y
        if self.y>=ground_y + self.radius:
            self.y=ground_y + self.radius
            self.velocity_y=0
        self.x=120
    def draw(self, screen):
        pygame.draw.circle(
    screen,
    (0, 220, 255),
    (int(self.x), int(self.y)),
    self.radius
)
player=Player()

class Obstacle:
    def __init__(self,x,width,height,speed):
        self.x=x
        self.width=width
        self.height=height
        self.speed=speed
        self.y=ground_y+40 - height
        self.passed=False
    def update(self):
        self.x-=self.speed
    def draw(self,screen):
        pygame.draw.rect(
    screen,
    (255,60,60),
    (self.x,self.y,self.width,self.height)
)
    def collides_with(self,player):
        closest_x=max(self.x,min(player.x,self.x+self.width))
        closest_y=max(self.y,min(player.y,self.y+self.height))
        dx=player.x - closest_x
        dy=player.y - closest_y
        return (dx*dx + dy*dy) < (player.radius * player.radius)
obstacles=[]
obstacles.append(Obstacle(900,40,40,4))
current_db=-60

def audio_callback(indata, frames, time, status):
    global current_db
    if status:
        print(status)
    rms=np.sqrt(np.mean(indata**2))
    current_db=20*np.log10(rms) if rms>0 else -60
    current_db=max(-60,min(current_db,-10))
stream= sd.InputStream(channels=1, callback=audio_callback,samplerate=44100,blocksize=1024)
stream.start()

smoothed_db=-60
alpha=0.1
jump_threshold=-38
game_over= False
running=True
score=0
jump_cooldown=0.4
jump_timer=0.0
def reset_game():
    global game_over, obstacles, jump_timer, smoothed_db, score
    game_over = False
    jump_timer = 0.0
    smoothed_db = -60
    score=0
    player.y = ground_y + player.radius
    player.velocity_y = 0
    score_text = small_font.render(f"Score: {int(score)}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    obstacles.clear()
    obstacles.append(Obstacle(900, 40, 40, 4))

while running:
    dt=clock.tick(60)/1000
    jump_timer+=dt
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            running=False
            game_over=False
        if event.type== pygame.KEYDOWN:
            if event.key==pygame.K_r and game_over:
                reset_game()
    display_db=alpha*current_db+(1-alpha)*smoothed_db
    smoothed_db=display_db
    display_db= round(display_db,1)
    display_db=max(-60,display_db)
    if not game_over:
     if smoothed_db> jump_threshold and jump_timer>=jump_cooldown:
        player.jump()
        jump_timer=0.0
    if not game_over:
        player.update()

    if obstacles and obstacles[0].x<-50:
        obstacles.pop(0)
        obstacles.append(Obstacle(900,40,40,4))
    screen.fill((20,20,20))
    pygame.draw.line(screen,(120,120,120),(0,ground_y+40),(width,ground_y+40),2)
    for obs in obstacles:
        if not game_over:
         obs.update()
        obs.draw(screen)
        if not obs.passed and obs.x + obs.width < player.x:
                obs.passed=True
                score+=1
        if not game_over and obs.collides_with(player):
            print("Game Over!")
            print("PRESS R TO RESTART")
            game_over=True
    player.draw(screen)
    score_text = small_font.render(f"Score: {int(score)}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))
    if game_over:
        over_text=font.render("Game Over!",True,(255,80,80))
        screen.blit(over_text,(width//2 - over_text.get_width()//2,height//2 - over_text.get_height()//2))
        restart_text=font.render("Press R to Restart",True,(255,80,80))
        screen.blit(restart_text,(width//2 - restart_text.get_width()//2,height//2 + 30))
    pygame.display.flip()
stream.stop()
stream.close()
pygame.quit()