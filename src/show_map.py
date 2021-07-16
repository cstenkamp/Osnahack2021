from matplotlib import pyplot as plt
from matplotlib_scalebar.scalebar import ScaleBar

def show_map(start_coords, goal_coords, stop_coords, fixed_lims=None):
    fig, ax = plt.subplots(1, 1)
    ax.scatter(*start_coords, color="blue")
    ax.text(*start_coords, "Start")
    ax.scatter(*goal_coords, color="blue")
    ax.text(*goal_coords, "Goal")
    ax.scatter(*list(zip(*[i[:2] for i in stop_coords])), color=[i[2] for i in stop_coords])
    scalebar = ScaleBar(130, "km", length_fraction=0.25)
    ax.add_artist(scalebar)
    if fixed_lims:
        ax.set_xlim(fixed_lims[0], fixed_lims[1])
        ax.set_ylim(fixed_lims[2], fixed_lims[3])
    plt.show()

if __name__ == "__main__":
    start_coords, goal_coords = (52.28807, 8.0145), (52.27291, 8.06157)
    stop_coords = ((52.28617, 8.012498, "green"),)
    show_map(start_coords, goal_coords, stop_coords)