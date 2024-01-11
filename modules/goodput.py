import matplotlib.pyplot as plt
from modules.prerequisites import read_configuration



def show_goodput_graph(df, control_parameter):
    GOODPUT_RESULTS = read_configuration().get("GOODPUT_RESULTS")
    # Group the DataFrame by 'mode'
    grouped_by_mode = df.groupby('mode')

    # Create a scatterplot for each mode
    plt.figure(figsize=(10, 6))

    for mode, group_data in grouped_by_mode:
        plt.scatter(group_data[control_parameter],
                    group_data['goodput'], label=mode, alpha=0.7)
        plt.plot(group_data[control_parameter], group_data['goodput'],
                 marker='o', linestyle='-', alpha=0.5)

    plt.xlabel(control_parameter)
    plt.ylabel('Goodput')
    plt.title(f'Scatterplot of {control_parameter} vs Goodput grouped by Mode')
    plt.legend()
    plt.grid(True)
    plt.savefig(GOODPUT_RESULTS, dpi=300, bbox_inches='tight')





