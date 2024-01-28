import matplotlib.pyplot as plt
from modules.prerequisites import read_configuration


def show_goodput_graph(df, control_parameter):
    GOODPUT_RESULTS = read_configuration().get("GOODPUT_RESULTS")

    parameter_column = control_parameter
    group_column = 'mode'
    data_column = 'goodput_50%'

    # Create a scatterplot for each mode
    plt.figure(figsize=(10, 6))

    for mode in df[group_column].unique():
        mode_df = df[df[group_column] == mode]

        plt.plot(mode_df[parameter_column],
                 mode_df[data_column],
                 marker='o', linestyle='-', alpha=0.5, label=mode)

    plt.xlabel(parameter_column)
    plt.ylabel('Goodput')
    plt.title(f'Scatterplot of {parameter_column} vs Goodput grouped by Mode')
    plt.legend()
    plt.grid(True)
    plt.savefig(GOODPUT_RESULTS, dpi=300, bbox_inches='tight')
