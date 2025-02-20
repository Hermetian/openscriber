#This doesn't really belong here, or anywhere, but it's just cool.

#!/usr/bin/env python3
import random
from collections import deque
from PIL import Image

# Define a set of GitHub-like green colors.
greens = [
    (155, 233, 168),  # Light green
    (64, 196, 99),    # Medium green
    (48, 161, 78),    # Dark green
    (33, 110, 57)     # Darker green
]

# Open the image and ensure it's in RGB mode.
img = Image.open('frame.png').convert('RGB')
pixels = img.load()
width, height = img.size

# Create a visited 2D array to mark processed pixels.
visited = [[False for _ in range(width)] for _ in range(height)]


def neighbors(x, y):
    # Return 4-connected neighboring coordinates.
    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            yield nx, ny


# Process the image: whenever we hit an unvisited black pixel, perform flood fill.
for y in range(height):
    for x in range(width):
        if not visited[y][x] and pixels[x, y] == (0, 0, 0):
            # Choose a random green from our palette for this contiguous region.
            chosen_color = random.choice(greens)
            queue = deque()
            queue.append((x, y))
            while queue:
                cur_x, cur_y = queue.popleft()
                if visited[cur_y][cur_x]:
                    continue
                # Only fill if it's black.
                if pixels[cur_x, cur_y] == (0, 0, 0):
                    pixels[cur_x, cur_y] = chosen_color
                    visited[cur_y][cur_x] = True
                    for nx, ny in neighbors(cur_x, cur_y):
                        if not visited[ny][nx] and pixels[nx, ny] == (0, 0, 0):
                            queue.append((nx, ny))
                else:
                    visited[cur_y][cur_x] = True

# Save the modified image under a new filename.
img.save('frame_github.png')
print("Processing complete. The new image is saved as frame_github.png")