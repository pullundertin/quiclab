import statsmodels.stats.multicomp as mc
import pandas as pd
from sci_analysis import analyze
import scikit_posthocs as sp
import matplotlib.pyplot as plt
from scipy.stats import f_oneway, kruskal
import numpy as np
import pyarrow.parquet as pq
import warnings
import sys
from modules.prerequisites import read_configuration

# Ignore FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)

STATISTICS_DIR = read_configuration().get('STATISTICS_DIR')

# def perform_grouped_test(df, grouping_columns, test_function):
#     grouped_data = [group_data[data_column] for _,
#                     group_data in df.groupby(grouping_columns)]
#     result = test_function(*grouped_data)
#     return result


def run_statistics(df, test):
    data_columns = ['goodput', 'hs', 'conn']
    group_column = 'mode'
    parameter_column = test.control_parameter
    for data_column in data_columns:
        for parameter in df[parameter_column].unique():
            filtered_df = df[df[parameter_column] == parameter]
            for mode in filtered_df[group_column].unique():
                df_by_mode = filtered_df[filtered_df[group_column] == mode]
                get_explorative_analysis(
                    df_by_mode, mode, data_column, parameter_column, parameter)
            get_boxplot(filtered_df, data_column,
                        group_column, parameter_column, parameter)

            get_posthoc_dunn(filtered_df, data_column,
                             group_column, parameter_column, parameter)


def get_explorative_analysis(df, mode, data_column, parameter_column, parameter):
    with open(f"{STATISTICS_DIR}/eda.log", 'a') as file:
        file.write(
            f'Mode: {mode}    Metric: {data_column}, {parameter_column} = {parameter}')

        # Redirect the standard output to the file
        original_stdout = sys.stdout
        sys.stdout = file

        analyze(
            df[data_column],
            percent=True,
            title=f'Distribution for {mode}     {data_column}: {parameter_column} = {parameter}',
            save_to=f'{STATISTICS_DIR}/eda_{mode}_{data_column}_{parameter}.png'
        )

        # Restore the standard output
        sys.stdout = original_stdout


def get_boxplot(df, data_column, group_column, parameter_column, parameter):
    with open(f"{STATISTICS_DIR}/variance_analysis.log", 'a') as file:
        file.write(f'Metric: {data_column}, {parameter_column} = {parameter}')

        # Redirect the standard output to the file
        original_stdout = sys.stdout
        sys.stdout = file

        analyze(
            df[data_column],
            groups=df[group_column],
            alpha=0.05,
            name='Time',
            xname='Implementation',
            title=f'{data_column}: {parameter_column} = {parameter}',
            circles=False,
            nqp=False,
            save_to=f'{STATISTICS_DIR}/boxplot_{data_column}_{parameter}.png'
        )

        # Restore the standard output
        sys.stdout = original_stdout


def get_posthoc_dunn(df, data_column, group_column, parameter_column, parameter):
    heatmap_args = {'cmap': ['1', '#fb6a4a',  '#08306b',  '#4292c6', '#c6dbef'],
                    'linewidths': 0.25,
                    'linecolor': '0.5',
                    'clip_on': False,
                    'square': True,
                    'cbar_ax_bbox': [0.9, 0.35, 0.04, 0.3],
                    }
    post_hoc = sp.posthoc_dunn(df, val_col=data_column, group_col=group_column,
                               p_adjust='holm')
    with open(f"{STATISTICS_DIR}/posthoc.log", 'a') as file:
        file.write(
            f'\n\nMetric: {data_column}, {parameter_column} = {parameter}')
        file.write('\n' + str(post_hoc))

    # Print Significance Plot

    _ = sp.sign_plot(post_hoc, **heatmap_args)

    plt.savefig(f'{STATISTICS_DIR}/significance_plot_{data_column}_{parameter}.png',
                dpi=80, bbox_inches='tight')
    plt.close()
