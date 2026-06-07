import plotly.graph_objects as go

def plot_punching_shear(x_c, y_c, cx, cy, effective_shear_line, cx_plastic, cy_plastic, slab_bounds, d, stud_rails=None, required_rail_length=None):
    """Plot the punching shear analysis results using Plotly."""
    fig = go.Figure()
    
    # Plot Column
    fig.add_trace(go.Scatter(
        x=[x_c-cx/2, x_c+cx/2, x_c+cx/2, x_c-cx/2, x_c-cx/2],
        y=[y_c-cy/2, y_c-cy/2, y_c+cy/2, y_c+cy/2, y_c-cy/2],
        fill='toself',
        fillcolor='rgba(128, 128, 128, 0.5)',
        line=dict(color='gray'),
        name='Column',
        mode='lines'
    ))
    
    # Plot Perimeter
    show_legend = True
    for line in effective_shear_line.geoms:
        x, y = line.xy
        fig.add_trace(go.Scatter(
            x=list(x),
            y=list(y),
            mode='lines+markers',
            line=dict(color='red', width=2),
            marker=dict(symbol='circle', size=6),
            name='Critical Perimeter',
            showlegend=show_legend
        ))
        show_legend = False
    
    # Plot Stud Rails if provided
    if stud_rails:
        show_legend = True
        for rail in stud_rails:
            rx, ry = zip(*rail)
            fig.add_trace(go.Scatter(
                x=list(rx),
                y=list(ry),
                mode='lines+markers',
                line=dict(color='blue', width=1),
                marker=dict(symbol='x', size=6),
                name='Stud Rails',
                showlegend=show_legend
            ))
            show_legend = False
            
    # Plot Centroid
    fig.add_trace(go.Scatter(
        x=[cx_plastic],
        y=[cy_plastic],
        mode='markers',
        marker=dict(color='black', symbol='x', size=10),
        name='Plastic Centroid'
    ))
    
    # Plot Slab Bounds (dashed box)
    sx1, sy1, sx2, sy2 = slab_bounds
    fig.add_trace(go.Scatter(
        x=[sx1, sx2, sx2, sx1, sx1],
        y=[sy1, sy1, sy2, sy2, sy1],
        mode='lines',
        line=dict(color='blue', dash='dash'),
        opacity=0.5,
        name='Slab Edge'
    ))
    
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

    x_range = [x_min_col - margin, x_max_col + margin]
    y_range = [y_min_col - margin, y_max_col + margin]
    
    fig.update_layout(
        title="CSA A23.3 Edge-Detected Punching Shear",
        xaxis_title="X (mm)",
        yaxis_title="Y (mm)",
        xaxis=dict(range=x_range, constrain='domain'),
        yaxis=dict(range=y_range, scaleanchor="x", scaleratio=1),
        width=800,
        height=800,
        template="plotly_white",
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    return fig

def plot_applied_loads(inputs):
    """Plot the applied loads using Plotly."""
    fig = go.Figure()

    x_c, y_c = inputs.x_c, inputs.y_c
    c1, c2 = inputs.c1, inputs.c2

    # Plot Column
    fig.add_trace(go.Scatter(
        x=[x_c - c1/2, x_c + c1/2, x_c + c1/2, x_c - c1/2, x_c - c1/2],
        y=[y_c - c2/2, y_c - c2/2, y_c + c2/2, y_c + c2/2, y_c - c2/2],
        fill='toself',
        fillcolor='lightgray',
        line=dict(color='black', width=1.5),
        name='Column',
        mode='lines'
    ))

    # Plot Shear Force (Vf) at Centroid
    fig.add_trace(go.Scatter(
        x=[x_c],
        y=[y_c],
        mode='markers+text',
        marker=dict(symbol='x', size=10, color='black'),
        text=[f"Vf = {inputs.Vf:.1f} kN"],
        textposition="top right",
        name='Vf (Into Page)'
    ))

    # Plot Unbalanced Moment (Mf_x) Vector (Right-Hand Rule)
    if inputs.Mf_x != 0:
        dir_x = 1 if inputs.Mf_x > 0 else -1
        end_x = x_c + dir_x * (c1/2 + 300)
        fig.add_annotation(
            x=end_x, y=y_c,
            ax=x_c, ay=y_c,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor="blue"
        )
        fig.add_annotation(
            x=end_x + dir_x * 50, y=y_c,
            text=f"Mfx = {inputs.Mf_x:.1f} kNm",
            showarrow=False,
            font=dict(color="blue", size=11),
            xanchor="left" if dir_x > 0 else "right"
        )

    # Plot Unbalanced Moment (Mf_y) Vector (Right-Hand Rule)
    if inputs.Mf_y != 0:
        dir_y = 1 if inputs.Mf_y > 0 else -1
        end_y = y_c + dir_y * (c2/2 + 300)
        fig.add_annotation(
            x=x_c, y=end_y,
            ax=x_c, ay=y_c,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor="red"
        )
        fig.add_annotation(
            x=x_c, y=end_y + dir_y * 50,
            text=f"Mfy = {inputs.Mf_y:.1f} kNm",
            showarrow=False,
            font=dict(color="red", size=11),
            yanchor="bottom" if dir_y > 0 else "top"
        )

    # Formatting
    margin = max(c1, c2) * 1.5
    x_range = [x_c - margin, x_c + margin]
    y_range = [y_c - margin, y_c + margin]

    fig.update_layout(
        title="Applied Loads on Column (Plan View)",
        xaxis_title="X (mm)",
        yaxis_title="Y (mm)",
        xaxis=dict(range=x_range, constrain='domain'),
        yaxis=dict(range=y_range, scaleanchor="x", scaleratio=1),
        width=700,
        height=700,
        template="plotly_white"
    )

    return fig