import pandas as pd
from scipy.stats import f_oneway
import statsmodels.stats.multicomp as mc
from modules.prerequisites import read_configuration
import os

ANOVA_RESULTS = read_configuration().get("ANOVA_RESULTS")


def do_anova(df, control_parameter):
    if os.path.exists(ANOVA_RESULTS):
        os.remove(ANOVA_RESULTS)

    def do_anova_for_each_value_of_independent_variable(df, control_parameter):
        for value in df[control_parameter].unique():
            # Filter the DataFrame based on the current unique value
            filtered_df = df[df[control_parameter] == value]
            combine_handshake_and_connection_postfixes_with_each_available_mode(
                filtered_df, value)

    def combine_handshake_and_connection_postfixes_with_each_available_mode(df, value):
        for postfix in ['hs', 'conn']:
            unique_modes = df['mode'].unique()

            if len(unique_modes) < 2:
                return

            results = [
                f"{mode.split('_')[0]}_{postfix}" for mode in unique_modes]
            combined_df = generate_dataframe_with_all_values_combined(
                results, df)
            f_statistic, p_value = perform_anova(combined_df)
            tukey_result = perform_tukey_hsd_test(combined_df)
            store_results_to_file(f_statistic, p_value,
                                  tukey_result, control_parameter, value)

    def generate_dataframe_with_all_values_combined(results, df):
        combined_data = {column: df[column].dropna().tolist()
                         for column in results}
        combined_df = pd.DataFrame(combined_data)
        return combined_df

    def perform_anova(combined_df):
        args = [combined_df[column] for column in combined_df.columns]
        f_statistic, p_value = f_oneway(*args)
        return f_statistic, p_value

    def perform_tukey_hsd_test(combined_df):
        data = pd.melt(combined_df.reset_index(), id_vars=[
                       'index'], value_vars=combined_df.columns)
        data.columns = ['index', 'group', 'value']
        tukey_result = mc.MultiComparison(
            data['value'], data['group']).tukeyhsd()
        return tukey_result

    def store_results_to_file(f_statistic, p_value, tukey_result, control_parameter, value):
        output = f"""
Independent Variable: {control_parameter} = {value}
    F-statistic: {f_statistic}
    P-value: {p_value}
    Tukey: 
        {tukey_result}
        """
        with open(ANOVA_RESULTS, 'a') as file:
            file.write(output)

    do_anova_for_each_value_of_independent_variable(df, control_parameter)
