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
    def __init__(self, x, y, radius, color="black", rate=1, gap=30, width=5):
        self.radius = radius
        self.x = x
        self.y = y
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
        
    def update(self):
        if self.destroy:
            if self.particles == []:
                for point in self.points:
                    self.particles.append(Particle(point[0], point[1], 2, color=self.color, vx=-10*point[2][0], vy=-10*point[2][1]))
                self.points = []
                self.gap_points = []
        else:   
            for i in range(self.rate):
                self.points.insert(0, self.gap_points.pop())
                self.gap_points.insert(0, self.points.pop())
    
    def draw(self, draw, t):
        if self.destroy:
            for particle in self.particles:
                particle.update()
                particle.draw(draw)
        else:
            draw.arc(xy=(self.x, self.y, self.x + 2 * self.radius, self.y + 2 * self.radius), start=int(-self.rate*t), end=int(-self.rate*t+(360-self.gap)), fill=self.color, width=self.width)
            

class Ball:
    def __init__(self, x, y, radius, color="black"):
        self.radius = radius
        self.x = x
        self.y = y
        self.vx = 3
        self.vy = -5
        self.color = color

    def update(self):
        self.vy += 1
        self.x += self.vx
        self.y += self.vy

    def draw(self, draw):
        draw.ellipse((self.x - self.radius, self.y - self.radius, self.x + self.radius, self.y + self.radius), fill=self.color, outline='white', width=2)
    

class MainBall(Ball):
    def update(self, objects):
        super().update()
        for object in objects:
            if (self.check_collision(object)):
                break

    def check_collision(self, arc):
        start = (self.x - self.vx, self.y - self.vy)
        interval = int(mag((self.vx, self.vy)) / self.radius) + 1
        for point in arc.gap_points:
            collision, point_of_collision = self.ccd(start, interval, point)
            if collision:
                arc.destroy = True
                return False
        for point in arc.points:
            collision, point_of_collision = self.ccd(start, interval, point)
            if collision:
                unit = point[2]
                magv = mag((self.vx, self.vy))
                self.vx = magv * unit[0] 
                self.vy = magv * unit[1]
                self.x = int(point_of_collision[0] + 1 * self.radius * unit[0])
                self.y = int(point_of_collision[1] + 1 * self.radius * unit[1])
                return True
        return False
    
    def ccd(self, start, interval, point):
        cx = start[0]
        cy = start[1]
        for t in range(interval):
            cx = start[0] + int(t/interval * self.vx)
            cy = start[1] + int(t/interval * self.vy)
            diff_vector = (cx-point[0], cy-point[1])
            distance = mag(diff_vector)
            if distance <= self.radius:
                return True, (cx, cy)
        return False, (-1, -1)



class Particle(Ball):
    def __init__(self, x, y, radius, color="black", vx=0, vy=0):
        super().__init__(x, y, radius, color=color)
        self.vx = vx
        self.vy = vy

            
def add_asmr(clip_name):
    os.makedirs('frames', exist_ok=True)
    (
        ffmpeg
        .input(clip_name + ".mp4")
        .filter('fps', fps=30)
        .output(os.path.join('frames', 'frame_%05d.png'))
        .run(overwrite_output=True)
    )
    (
        ffmpeg
        .input(clip_name + ".mp4")
        .output(clip_name + ".mp3", vn=None, acodec='libmp3lame', audio_bitrate='192k')
        .run(overwrite_output=True)
    )
    frames = sorted(
        ['frames' + '/' + f for f in os.listdir("frames") if f.endswith('.png')]
    )
    colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
    objects = []
    for i in range(11):
        radius =  100 + i * 10
        x = width // 2 - radius
        y = 3 * height // 4 - radius
        objects.append(Arc(x, y, radius, color=colors[i % len(colors)], rate=i % 3 + 1))
    radius = 10
    x = width // 2 - radius
    y = 3 * height // 4 - radius
    main_ball = MainBall(x, y, radius)

    for i, path in tqdm(enumerate(frames), desc="Generating frames"):
        frame = Image.open(path).convert("RGBA")
        draw = ImageDraw.Draw(frame)
        
        for object in objects:
            object.update()
        main_ball.update(objects)
        for object in objects:
            object.draw(draw, i)
        main_ball.draw(draw)
        frame.save(path)

    ffmpeg.input('frames/frame_%05d.png', framerate=30).output(
        clip_name + 'temp.mp4',
        vcodec='libx264',
        pix_fmt='yuv420p'
    ).run()

    video = ffmpeg.input(clip_name + 'temp.mp4')
    audio = ffmpeg.input(clip_name + '.mp3')

    ffmpeg.output(video.video, audio.audio, clip_name + 'asmr.mp4', vcodec='copy', acodec='aac', audio_bitrate='192k', shortest=None).run(overwrite_output=True)
    for root, dirs, files in os.walk("frames"):
        for filename in files:
            file_path = os.path.join(root, filename)
            os.remove(file_path)
    os.rmdir("frames")
    os.remove(clip_name + 'temp.mp4')
    os.remove(clip_name + '.mp3')

def make_gif_for_site():
    os.makedirs('frames', exist_ok=True)
    colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple']
    objects = []
    for i in range(11):
        radius =  100 + i * 10
        x = width // 2 - radius
        y = 3 * height // 4 - radius
        objects.append(Arc(x, y, radius, color=colors[i % len(colors)], rate=i % 3 + 1))
    radius = 10
    x = width // 2 - radius
    y = 3 * height // 4 - radius
    framerate = 30
    main_ball = MainBall(x, y, radius)

    for i in tqdm(range(framerate*30), desc='Generating frames...'):
        frame = Image.new('RGB', (720, 1280), color='white')
        draw = ImageDraw.Draw(frame)
        
        for object in objects:
            object.update()
        main_ball.update(objects)
        for object in objects:
            object.draw(draw, i)
        main_ball.draw(draw)
        frame.save(f'frames/frame_{i:05d}.png')

    ffmpeg.input('frames/frame_%05d.png', framerate=30).output(
        'output.gif',
        vf='scale=480:-1:flags=lanczos',
        loop=0
    ).run()
    for root, dirs, files in os.walk("frames"):
        for filename in files:
            file_path = os.path.join(root, filename)
            os.remove(file_path)
    os.rmdir("frames")
if __name__ == '__main__':
    make_gif_for_site()

