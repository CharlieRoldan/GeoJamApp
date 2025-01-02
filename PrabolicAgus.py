import math
import matplotlib.pyplot as plt
import random

# Function to calculate trajectory
def calculate_trajectory(v0, angle, g, x0, y0):
    angle_rad = math.radians(angle)
    t_flight = (2 * v0 * math.sin(angle_rad)) / g
    t = [i * 0.01 for i in range(int(t_flight / 0.01) + 1)]
    x = [x0 + v0 * math.cos(angle_rad) * i for i in t]
    y = [y0 + v0 * math.sin(angle_rad) * i - 0.5 * g * i**2 for i in t]
    return x, y

# Function to plot the game state
def plot_game(player_positions, target_position, trajectories=None):
    plt.figure(figsize=(10, 5))
    plt.title('Parabolic Shot Game')
    plt.xlabel('Distance (m)')
    plt.ylabel('Height (m)')
    plt.grid()
    
    for i, pos in enumerate(player_positions):
        plt.plot(pos[0], pos[1], 'o', label=f'Player {i+1}')
    
    plt.plot(target_position[0], target_position[1], 'rx', label='Target', markersize=12)
    
    if trajectories:
        for trajectory in trajectories:
            plt.plot(trajectory[0], trajectory[1])
    
    plt.legend()
    plt.show()

# Main game function
def main():
    g = 9.8  # Gravity on Earth
    
    # Random initial positions for players
    player_positions = [(random.randint(0, 50), 0), (random.randint(50, 100), 0)]
    target_position = (random.randint(25, 75), 0)
    
    while True:
        for i in range(2):
            print(f"\nPlayer {i+1}'s turn")
            v0 = float(input("Enter the initial velocity (m/s): "))
            angle = float(input("Enter the launch angle (degrees): "))
            
            x, y = calculate_trajectory(v0, angle, g, player_positions[i][0], player_positions[i][1])
            plot_game(player_positions, target_position, [(x, y)])
            
            if any(abs(xi - target_position[0]) < 1 and yi <= target_position[1] for xi, yi in zip(x, y)):
                print("You won!")
                return
            else:
                print("You missed, moron!")
        
if __name__ == "__main__":
    main()