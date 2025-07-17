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
        self.points = [(
            int(self.centerx + self.radius * math.cos((i / 100) * 2 * math.pi)), 
            int(self.centery + self.radius * math.sin((i / 100) * 2 * math.pi)),
            (-math.cos((i / 100) * 2 * math.pi), -math.sin((i / 100) * 2 * math.pi))) 
            for i in range(100)]
        self.gap_points = [(int(self.centerx + self.radius * math.cos((i / self.gap) * 2 * math.pi)), int(self.centery + self.radius * math.sin((i / self.gap) * 2 * math.pi))) for i in range(self.gap)]
        print(self.gap_points)
    def update(self, draw, t):
        draw.arc(xy=(self.x, self.y, self.x + 2 * self.radius, self.y + 2 * self.radius), start=int(self.rate*t), end=int(self.rate*t+(360-self.gap)), fill=self.color, width=self.width)
        self.gap_points = [(int(self.centerx + self.radius * math.cos((i / self.gap) * 2 * math.pi)), int(self.centery + self.radius * math.sin((i / self.gap) * 2 * math.pi))) for i in range(int(self.rate*t)-360, int(self.rate*t) + self.gap - 360)]

class Ball:
    def __init__(self, screen_width, screen_height, radius, color="black"):
        self.radius = radius
        self.x = screen_width // 2 - self.radius
        self.y = 5 * screen_height // 8 - self.radius
        self.centerx = self.x
        self.centery = self.y
        self.vx = 0
        self.vy = 0
        self.color = color

    def update(self, draw):
        draw.ellipse((self.x, self.y, self.x + 2 * self.radius, self.y + 2 * self.radius), fill=self.color)
        self.vy += 2
        self.x += self.vx
        self.y += self.vy
        self.centerx = self.x + self.radius
        self.centery = self.y + self.radius
    
    def check_intersect(self, arc):
        for point in arc.points:
            diff_vector = (self.centerx-point[0], self.centery-point[1])
            distance = mag(diff_vector)
            if distance <= self.radius and not ((point[0], point[1]) in arc.gap_points):
                unit = point[2]
                magv = mag((self.vx, self.vy))
                self.vx = magv * unit[0] 
                self.vy = magv * unit[1]
            
os.makedirs("frames", exist_ok=True)

num_frames = 100
arc1 = Arc(width, height, 200, color="yellow")
# arc2 = Arc(width, height, 210, color="blue", rate=1.5)
# arc3 = Arc(width, height, 220, color="red", rate=2)
ball1 = Ball(width, height, 30)

# for i in tqdm(range(num_frames), desc="Generating frames"):
#     frame = Image.new("RGB", (width, height), color="white")
#     draw = ImageDraw.Draw(frame)
    
#     arc1.update(draw, i)
#     # arc2.update(draw, i)
#     # arc3.update(draw, i)
#     ball1.update(draw)
#     ball1.check_intersect(arc1)
#     # ball1.check_intersect(arc1)
#     # ball1.check_intersect(arc1)

#     frame.save(f"frames/frame{i:03}.png")

# ffmpeg.input('frames/frame%03d.png', framerate=30).output(
#     'circle_animation.mp4',
#     vcodec='libx264',
#     pix_fmt='yuv420p'
# ).run()

# for root, dirs, files in os.walk("frames"):
#     for filename in files:
#         file_path = os.path.join(root, filename)
#         os.remove(file_path)

# os.rmdir("frames")

