
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from modules.prerequisites import read_configuration

BOXPLOTS_DIR = read_configuration().get("BOXPLOTS_DIR")


def combine_quic_and_tcp_values_for(df, column_postfix, value):
    """Combine QUIC and TCP values into a single column."""
    melted_df = pd.melt(df, id_vars=['mode'], value_vars=[
                        f'quic_{column_postfix}', f'tcp_{column_postfix}'], value_name=f'time_{value}')
    return melted_df


def plot_boxplot(df, ax, x_data, y_data, title, xlabel, ylabel):
    """Plot a boxplot on the specified axes."""
    sns.boxplot(ax=ax, x=x_data, y=y_data, data=df.dropna())
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)


def create_boxplot(df, ax, x_data, y_data, title, xlabel, ylabel):
    """Create a single boxplot for the specified axes."""
    sns.boxplot(ax=ax, x=x_data, y=y_data, data=df.dropna())
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

def create_boxplots_for_each_single_stream(df, test):
     
    
    # Find columns that match the pattern 'Stream_ID_<number>_goodput' and have non-null values
    stream_columns = [col for col in df.columns if col.startswith('Stream_ID_') and col.endswith('_goodput') and df[col].notnull().any()]

    # Create subplots for each mode
    modes = df['mode'].unique()
    num_plots = len(modes)

    fig, axes = plt.subplots(nrows=1, ncols=num_plots, figsize=(15, 6), sharey=True)

    for idx, mode in enumerate(modes):
        mode_df = df[df['mode'] == mode]
        mode_df_melted = mode_df.melt(id_vars='mode', value_vars=stream_columns, var_name='Stream_ID')

        non_nan_columns = [col for col in stream_columns if mode_df[col].notnull().any()]
        x_labels = [col.replace('_goodput', '') for col in non_nan_columns]

        sns.boxplot(data=mode_df_melted.dropna(), x='Stream_ID', y='value', ax=axes[idx], palette='Set3')
        axes[idx].set_title(f'Mode: {mode}')
        axes[idx].set_xlabel('Streams')  
        axes[idx].set_ylabel('Goodput')
        axes[idx].set_xticks(range(len(non_nan_columns))) 
        axes[idx].set_xticklabels(x_labels, rotation=90)  
        axes[idx].legend().set_visible(False)

    fig.suptitle('Goodput per Stream', y=1.05)
    plt.tight_layout()
    plt.savefig(f"{BOXPLOTS_DIR}/boxplots_single_stream.png",
                        dpi=300, bbox_inches='tight')
    plt.show()

def create_boxplots_for_each_value_of_independent_variable(df, test):

    def check_if_test_performs_on_a_series_of_control_parameter(control_parameter_values):
         if isinstance(control_parameter_values, list) and len(control_parameter_values) > 1:
              return True
         else:
              return False
         
    def check_if_tests_have_one_mode_only_and_return_that_mode(df):
        unique_modes = df['mode'].unique()

        if len(unique_modes) == 1:
            return unique_modes[0]
        else:
            return None
    

    def filter_dataframe_based_on_mode_and_control_parameter(df, mode, control_parameter):
            filtered_df = df[df['mode'] == mode]
            filtered_df = (filtered_df[[control_parameter, f'{mode}_hs', f'{mode}_conn', 'goodput']])
            return filtered_df
    
    def create_boxplot_for_single_mode(filtered_df, mode, control_parameter):
            fig, axes = plt.subplots(3, 1, figsize=(8, 10))

            create_boxplot(filtered_df, axes[0], control_parameter, f'{mode}_hs',
                        f'{mode} handshake with different values for {control_parameter}', control_parameter, 'time')
            
            create_boxplot(filtered_df, axes[1], control_parameter, f'{mode}_conn',
                        f'{mode} connection with different values for {control_parameter}', control_parameter, 'time')
            
            create_boxplot(filtered_df, axes[2], control_parameter, 'goodput',
                        f'{mode} goodput with different values for {control_parameter}', control_parameter, 'B/s')

            plt.tight_layout()
            plt.savefig(f"{BOXPLOTS_DIR}/boxplot_{mode}_{control_parameter}.png",
                        dpi=300, bbox_inches='tight')
            plt.show()
    
    control_parameter = test.control_parameter
    control_parameter_values = test.control_parameter_values
    single_mode_test = check_if_tests_have_one_mode_only_and_return_that_mode(df)

    if single_mode_test:
        if check_if_test_performs_on_a_series_of_control_parameter(control_parameter_values):
            filtered_df = filter_dataframe_based_on_mode_and_control_parameter(df, single_mode_test, control_parameter)
            create_boxplot_for_single_mode(filtered_df, single_mode_test, control_parameter)
        else:
            print("no boxplot")

    elif control_parameter is not None:
        for value in df[control_parameter].unique():
            filtered_df = df[df[control_parameter] == value]

            hs_df = combine_quic_and_tcp_values_for(filtered_df, 'hs', value)
            conn_df = combine_quic_and_tcp_values_for(filtered_df, 'conn', value)

            fig, axes = plt.subplots(2, 1, figsize=(8, 10))
            plot_boxplot(hs_df, axes[0], 'mode', f'time_{value}',
                         f'QUIC vs TCP Handshake | {control_parameter} = {value}', 'Implementations', 'Time')
            plot_boxplot(conn_df, axes[1], 'mode', f'time_{value}',
                         f'QUIC vs TCP Connection | {control_parameter} = {value}', 'Implementations', 'Time')

            plt.tight_layout()
            plt.savefig(f"{BOXPLOTS_DIR}/boxplots_{value}.png",
                        dpi=300, bbox_inches='tight')
            plt.show()


def show_boxplot(test_results_dataframe, test):
    create_boxplots_for_each_value_of_independent_variable(
        test_results_dataframe, test)
    create_boxplots_for_each_single_stream(test_results_dataframe, test)
