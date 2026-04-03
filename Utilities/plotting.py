import matplotlib.pyplot as plt

def plot_punching_shear(x_c, y_c, cx, cy, effective_shear_line, cx_plastic, cy_plastic, slab_bounds, d, stud_rails=None, required_rail_length=None):
    """Plot the punching shear analysis results."""
    plt.figure(figsize=(8, 8))
    
    # Plot Column
    plt.fill([x_c-cx/2, x_c+cx/2, x_c+cx/2, x_c-cx/2], 
             [y_c-cy/2, y_c-cy/2, y_c+cy/2, y_c+cy/2], color='gray', alpha=0.5, label='Column')
    
    # Plot Perimeter
    for i, line in enumerate(effective_shear_line.geoms):
        x, y = line.xy
        label = 'Critical Perimeter' if i == 0 else ""
        plt.plot(x, y, color='red', linewidth=2, marker='o', label=label)
    
    # Plot Stud Rails if provided
    if stud_rails:
        for i, rail in enumerate(stud_rails):
            rx, ry = zip(*rail)
            label = 'Stud Rails' if i == 0 else ""
            plt.plot(rx, ry, color='blue', linewidth=1, marker='x', markersize=6, linestyle='-', label=label)
            
    # Plot Centroid
    plt.plot(cx_plastic, cy_plastic, 'kx', markersize=10, label='Plastic Centroid')
    
    # Plot Slab Bounds (dashed box)
    sx1, sy1, sx2, sy2 = slab_bounds
    plt.plot([sx1, sx2, sx2, sx1, sx1], [sy1, sy1, sy2, sy2, sy1], 'b--', alpha=0.5, label='Slab Edge')
    
    # Set the aspect ratio first
    plt.gca().set_aspect('equal', adjustable='box')
    
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend()
    plt.title("CSA A23.3 Edge-Detected Punching Shear")
    plt.xlabel("X (mm)")
    plt.ylabel("Y (mm)")
    
    # Zoom to area near the column
    x_min_col = x_c - cx/2
    x_max_col = x_c + cx/2
    y_min_col = y_c - cy/2
    y_max_col = y_c + cy/2
    
    # Adjust margin based on rail length if it exists
    if required_rail_length:
        margin = required_rail_length + 2 * d
    else:
        margin = 5 * d

    # Apply limits
    plt.xlim(x_min_col - margin, x_max_col + margin)
    plt.ylim(y_min_col - margin, y_max_col + margin)
    
    plt.show()