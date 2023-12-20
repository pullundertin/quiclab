
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from modules.tests import find_keys_with_list_values
from modules.prerequisites import read_test_cases
from modules.prerequisites import read_configuration

HEATMAPS_DIR = read_configuration().get("HEATMAPS_DIR")


def calculate_percentage(df, new_column_name, quic_column, tcp_column, dependend_variable):
    df[new_column_name] = df.apply(lambda row: row[quic_column] / df.loc[(df['mode'] == 'http') & (
        df[dependend_variable] == row[dependend_variable]), tcp_column].values[0] * 100 if row['mode'] not in ['http'] else np.nan, axis=1)
    return df


def exclude_http_mode_from_heatmap(df):
    return df[df['mode'] != 'http']


def generate_heatmap(metric, df, dependend_variable):
    return df.pivot(
        index=dependend_variable, columns='mode', values=metric)


def save_heatmap(z_value, name, metric):
    # Plotting the heatmap
    plt.figure(figsize=(8, 6))
    sns.heatmap(z_value, annot=True, cmap='YlGnBu', fmt='.2f', cbar=True)
    plt.title(f'QUIC vs TCP {name}')
    plt.xlabel('Implementations')
    plt.ylabel(metric)
    plt.show()

    plt.savefig(f"{HEATMAPS_DIR}/{name}.png", dpi=300, bbox_inches='tight')

def tests_contain_http_only(test_case_settings):
    # Check if the list contains only 'http' and this is the only element
    modes = test_case_settings['cases']['mode']
    return len(modes) == 1 and modes[0] == 'http'

def show_heatmaps(df):
    test_case_settings = read_test_cases()
    if tests_contain_http_only(test_case_settings):
        return
    
    metric = find_keys_with_list_values(test_case_settings)
    
    if metric is None:
        metric = 'generic_heatmap'

    df = calculate_percentage(df, 'percentage_hs', 'quic_hs', 'tcp_hs', metric)
    df = calculate_percentage(df, 'percentage_conn',
                            'quic_conn', 'tcp_conn', metric)
    print(df)
    filtered_df = exclude_http_mode_from_heatmap(df)
    percentage_hs = generate_heatmap('percentage_hs', filtered_df, metric)
    percentage_conn = generate_heatmap('percentage_conn', filtered_df, metric)

    save_heatmap(percentage_hs, 'Handshake', metric)
    save_heatmap(percentage_conn, 'Connection', metric)
