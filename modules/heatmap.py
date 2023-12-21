
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from modules.prerequisites import get_test_object, read_configuration, get_control_parameter

HEATMAPS_DIR = read_configuration().get("HEATMAPS_DIR")


def calculate_percentage(df, new_column_name, quic_column, tcp_column, dependend_variable):
    df[new_column_name] = df.apply(lambda row: row[quic_column] / df.loc[(df['mode'] == 'tcp') & (
        df[dependend_variable] == row[dependend_variable]), tcp_column].values[0] * 100 if row['mode'] not in ['tcp'] else np.nan, axis=1)
    return df


def exclude_tcp_mode_from_heatmap(df):
    return df[df['mode'] != 'tcp']


def generate_heatmap(control_parameter, df, dependend_variable):
    return df.pivot(
        index=dependend_variable, columns='mode', values=control_parameter)


def save_heatmap(z_value, name, control_parameter):
    # Plotting the heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(z_value, annot=True, cmap='YlGnBu', fmt='.2f', cbar=True)
    plt.title(f'QUIC vs TCP {name}')
    plt.xlabel('Implementations')
    plt.ylabel(control_parameter)
    plt.show()

    plt.savefig(f"{HEATMAPS_DIR}/{name}.png", dpi=300, bbox_inches='tight')


def tests_contain_tcp_only(median_dataframe):
    return (median_dataframe['mode'] == 'tcp').all()


def show_heatmaps(median_dataframe, control_parameter, args):
    if tests_contain_tcp_only(median_dataframe):
        return

    if control_parameter is None:
        control_parameter = 'generic_heatmap'

    median_dataframe = calculate_percentage(
        median_dataframe, 'percentage_hs', 'quic_hs', 'tcp_hs', control_parameter)
    median_dataframe = calculate_percentage(median_dataframe, 'percentage_conn',
                                            'quic_conn', 'tcp_conn', control_parameter)
    if args.results:
        print(median_dataframe)
    filtered_median_dataframe = exclude_tcp_mode_from_heatmap(
        median_dataframe)
    percentage_hs = generate_heatmap(
        'percentage_hs', filtered_median_dataframe, control_parameter)
    percentage_conn = generate_heatmap(
        'percentage_conn', filtered_median_dataframe, control_parameter)

    save_heatmap(percentage_hs, 'Handshake', control_parameter)
    save_heatmap(percentage_conn, 'Connection', control_parameter)
