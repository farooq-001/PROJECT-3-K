import pygame
import sys
import tkinter as tk
from tkinter import ttk
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Flying Bird Animation')

# Colors
white = (255, 255, 255)

# Load bird image and resize
bird_image_orig = pygame.image.load('static/bird.png')  # Load bird image from 'static/bird.png'
bird_image = pygame.transform.scale(bird_image_orig, (50, 50))  # Resize bird image
bird_rect = bird_image.get_rect()

# Initial position and speed of the bird
bird_x = screen_width // 2
bird_y = screen_height // 2
bird_speed = 3  # Initial speed of the bird

# Tkinter setup for trackbar
root = tk.Tk()
root.title('Trackbar Control')
trackbar_value = tk.IntVar()
trackbar = ttk.Scale(root, from_=1, to=10, variable=trackbar_value, orient=tk.HORIZONTAL)
trackbar.pack()

# Main loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            pygame.quit()
            sys.exit()

    # Get current position of the trackbar (speed)
    speed = trackbar_value.get()

    # Get current position of the mouse cursor
    mouse_x, mouse_y = pygame.mouse.get_pos()

    # Calculate direction towards the mouse cursor
    direction_x = mouse_x - bird_x
    direction_y = mouse_y - bird_y
    distance = math.sqrt(direction_x ** 2 + direction_y ** 2)

    # Normalize direction vector (unit vector)
    if distance > 0:
        direction_x /= distance
        direction_y /= distance

    # Update bird position based on direction and speed
    bird_x += int(direction_x * speed)
    bird_y += int(direction_y * speed)

    # Draw everything
    screen.fill(white)  # Clear screen with white
    screen.blit(bird_image, (bird_x - bird_image.get_width() // 2, bird_y - bird_image.get_height() // 2))  # Draw bird at updated position

    # Refresh screen
    pygame.display.flip()

    # Control frame rate
    pygame.time.Clock().tick(30)  # Adjust frame rate as needed

    # Update Tkinter events
    root.update()

# Close Tkinter window when Pygame loop ends
root.destroy()

