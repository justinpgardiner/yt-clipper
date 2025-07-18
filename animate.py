import math
from tqdm import tqdm
from PIL import Image, ImageDraw
import os
import ffmpeg

width, height = 720, 1280

def mag(vector):
    return math.sqrt((vector[0])**2 + (vector[1])**2)

def hat(vector):
    magv = mag(vector)
    return tuple(i / magv for i in vector)

class Arc:
    def __init__(self, screen_width, screen_height, radius, color="black", rate=1, gap=30, width=5):
        self.radius = radius
        self.x = screen_width // 2 - self.radius
        self.y = 5 * screen_height // 8 - self.radius
        self.color = color
        self.rate = rate
        self.gap = gap
        self.width = width
        self.centerx = self.x + self.radius
        self.centery = self.y + self.radius
        self.destroy = False
        self.particles = []
        # Arranging a list of points that fall on the spinning arc
        # Third entry into the tuple is a unit vector pointing to the center of the circle; this is in order to determine direction ball will bounce on collision
        self.points = []
        for i in range(360-self.gap):
            angle = (i / 360) * (2 * math.pi)
            point = (
                int(self.centerx + self.radius * math.cos(angle)), 
                int(self.centery + self.radius * math.sin(angle)),
                (-math.cos(angle), -math.sin(angle))
            )
            self.points.append(point) 
        self.gap_points = []
        for i in range(360-self.gap, 360):
            angle = (i / 360) * (2 * math.pi)
            point = (
                int(self.centerx + self.radius * math.cos(angle)), 
                int(self.centery + self.radius * math.sin(angle)),
                (-math.cos(angle), -math.sin(angle))
            )
            self.gap_points.append(point) 
        # print(self.gap_points)
        
    def update(self, draw, t):
        if self.destroy:
            if self.particles == []:
                for point in self.points:
                    self.particles.append(Particle(point[0], point[1], 2, color=self.color, vx=-10*point[2][0], vy=-10*point[2][1]))
            else:
                for particle in self.particles:
                    particle.update(draw)
        else:   
            draw.arc(xy=(self.x, self.y, self.x + 2 * self.radius, self.y + 2 * self.radius), start=int(-self.rate*t), end=int(-self.rate*t+(360-self.gap)), fill=self.color, width=self.width)
            for i in range(self.rate):
                self.points.insert(0, self.gap_points.pop())
                self.gap_points.insert(0, self.points.pop())

class Ball:
    def __init__(self, x, y, radius, color="black"):
        self.radius = radius
        self.x = x
        self.y = y
        self.centerx = self.x
        self.centery = self.y
        self.vx = 0
        self.vy = 0
        self.color = color

    def update(self, draw):
        draw.ellipse((self.x - self.radius, self.y - self.radius, self.x + self.radius, self.y + self.radius), fill=self.color)
        self.vy += 1
        self.x += self.vx
        self.y += self.vy
        self.centerx = self.x + self.radius
        self.centery = self.y + self.radius
    

class MainBall(Ball):
    def check_collision(self, arc):
        for point in arc.gap_points:
            diff_vector = (self.centerx-point[0], self.centery-point[1])
            distance = mag(diff_vector)
            if distance <= self.radius:
                arc.destroy = True
        for point in arc.points:
            diff_vector = (self.centerx-point[0], self.centery-point[1])
            distance = mag(diff_vector)
            if distance <= self.radius:
                unit = point[2]
                magv = mag((self.vx, self.vy))
                self.vx = magv * unit[0] 
                self.vy = magv * unit[1]



class Particle(Ball):
    def __init__(self, x, y, radius, color="black", vx=0, vy=0):
        super().__init__(x, y, radius, color=color)
        self.vx = vx
        self.vy = vy

            
os.makedirs("frames", exist_ok=True)

num_frames = 300
arc1 = Arc(width, height, 100, color="yellow", rate=2)
arc2 = Arc(width, height, 110, color="blue", rate=2)
arc3 = Arc(width, height, 120, color="red", rate=2)
radius = 10
x = width // 2 - radius
y = 5 * height // 8 - radius
main_ball = MainBall(x, y, radius)

for i in tqdm(range(num_frames), desc="Generating frames"):
    frame = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(frame)
    
    arc1.update(draw, i)
    arc2.update(draw, i)
    arc3.update(draw, i)
    main_ball.update(draw)
    main_ball.check_intersect(arc1)
    main_ball.check_intersect(arc2)
    main_ball.check_intersect(arc3)

    frame.save(f"frames/frame{i:03}.png")

ffmpeg.input('frames/frame%03d.png', framerate=30).output(
    'circle_animation.mp4',
    vcodec='libx264',
    pix_fmt='yuv420p'
).run()

for root, dirs, files in os.walk("frames"):
    for filename in files:
        file_path = os.path.join(root, filename)
        os.remove(file_path)

os.rmdir("frames")

