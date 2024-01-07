import pandas as pd
import matplotlib.pyplot as plt
from modules.prerequisites import read_configuration
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns  # Import seaborn for KDE

def show_histogram(df, control_parameter):
    HISTOGRAMS_DIR = read_configuration().get('HISTOGRAMS_DIR')
    TEST_RESULT_COLUMNS = read_configuration().get('TEST_RESULT_COLUMNS')
    stream_columns = [col for col in df.columns if col.startswith('Stream_ID_') and col.endswith('_goodput')]

    parameters = TEST_RESULT_COLUMNS + stream_columns

    unique_control_parameter_values = df[control_parameter].unique()

    fig, axs = plt.subplots(len(parameters), len(unique_control_parameter_values), figsize=(50, 100))

    for i, param in enumerate(parameters):
        for j, ctrl_param_value in enumerate(unique_control_parameter_values):
            grouped = df[(~df[param].isnull()) & (df[control_parameter] == ctrl_param_value)].groupby('mode')[param]
            for mode, group in grouped:
                # Plot histogram
                axs[i, j].hist(group, bins='auto', alpha=0.5, rwidth=0.55, label=mode, density=True)
                # Plot KDE (PDA)
                # sns.kdeplot(group, ax=axs[i, j], label=f'{mode} KDE', linewidth=2)

            axs[i, j].set_title(f'Histogram for {param} - {control_parameter}: {ctrl_param_value}')
            axs[i, j].set_xlabel(param)
            axs[i, j].set_ylabel('Density')
            # axs[i, j].text(23, 45, r'$\mu=15, b=3$')
            if param in ['goodput', 'quic_hs', 'quic_conn'] or param.startswith("Stream_ID_"):
                axs[i, j].legend()

    plt.tight_layout()
    plt.savefig(f'{HISTOGRAMS_DIR}/histogram.png')
    plt.show()
