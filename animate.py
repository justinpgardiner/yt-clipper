from tqdm import tqdm
from PIL import Image, ImageDraw
import os
import ffmpeg

os.makedirs("frames", exist_ok=True)

width, height = 720, 1280
num_frames = 60
circle_radius = 200

for i in tqdm(range(num_frames), desc="Generating frames"):
    frame = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(frame)
    
    x = int((width - 2 * circle_radius) * (i / (num_frames - 1)))
    y = 5 * height // 8 - circle_radius
    draw.arc(xy=(x, y, x + circle_radius, y + circle_radius), start=0, end=325, fill="blue", width=5)
    
    frame.save(f"frames/frame{i:03}.png")



ffmpeg.input('frames/frame%03d.png', framerate=30).output(
    'circle_animation.mp4',
    vcodec='libx264',
    pix_fmt='yuv420p'
).run()