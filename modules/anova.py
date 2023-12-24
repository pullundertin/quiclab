import pandas as pd
from scipy.stats import f_oneway
import statsmodels.stats.multicomp as mc
from modules.prerequisites import read_configuration
import os

ANOVA_RESULTS = read_configuration().get("ANOVA_RESULTS")


def do_anova(test_results_dataframe, control_parameter):
    if os.path.exists(ANOVA_RESULTS):
        os.remove(ANOVA_RESULTS)

    def filter_test_results_based_on_values_of_control_parameter(test_results_dataframe, control_parameter, value):
        return test_results_dataframe[test_results_dataframe[control_parameter] == value]

    def do_anova_for_each_value_of_independent_variable(test_results_dataframe, control_parameter):
        for value in test_results_dataframe[control_parameter].unique():
            additional_values_to_do_anova_on = ['goodput']

            filtered_by_value_dataframe = filter_test_results_based_on_values_of_control_parameter(
                test_results_dataframe, control_parameter, value)

            anova_dataframe = combine_handshake_and_connection_postfixes_with_each_available_mode(
                filtered_by_value_dataframe, value)

            anova_dataframe = add_additional_columns_to_do_anova_on(
                filtered_by_value_dataframe, anova_dataframe, additional_values_to_do_anova_on)

            anova_results = perform_anova(anova_dataframe)
            tukey_result = perform_tukey_hsd_test(anova_dataframe)
            store_results_to_file(anova_results,
                                  tukey_result, control_parameter, value)

    def combine_handshake_and_connection_postfixes_with_each_available_mode(df, value):
        combined_df = None

        for postfix in ['hs', 'conn']:
            unique_modes = df['mode'].unique()

            if len(unique_modes) < 2:
                return

            results = [
                f"{mode.split('_')[0]}_{postfix}" for mode in unique_modes]

            combined_df = update_dataframe_with_new_data(
                combined_df, df, results)

        return combined_df

    def update_dataframe_with_new_data(combined_df, df, results):
        if combined_df is None:
            combined_df = generate_dataframe_with_all_values_combined(
                results, df)
        else:
            temp_df = generate_dataframe_with_all_values_combined(
                results, df)
            combined_df = pd.concat([combined_df, temp_df], axis=1)
        return combined_df

    def generate_dataframe_with_all_values_combined(results, df):
        combined_data = {column: df[column].dropna().tolist()
                         for column in results}
        combined_df = pd.DataFrame(combined_data)
        return combined_df

    def add_additional_columns_to_do_anova_on(test_results_dataframe, anova_df, additional_values_to_do_anova_on):
        dataframe_with_additional_values = pd.DataFrame()
        for additional_value in additional_values_to_do_anova_on:
            additional_value_df = generate_dataframe_of_additional_value_based_on_mode(
                test_results_dataframe, additional_value)
            dataframe_with_additional_values = pd.concat(
                [anova_df, additional_value_df], axis=1)
        return dataframe_with_additional_values

    def generate_dataframe_of_additional_value_based_on_mode(df, additional_value):
        # Create a unique identifier for each row
        indices = df.groupby('mode').cumcount()
        df = df.assign(index=indices)

        # Pivot the DataFrame to have separate columns for 'goodput' values based on 'mode'
        pivot_df = df.pivot_table(
            index='index', columns='mode', values='goodput', aggfunc='first')

        # Rename columns to have the mode concatenated with 'goodput'
        pivot_df.columns = [f"{col}_goodput" for col in pivot_df.columns]

        # Reset the index if necessary
        pivot_df.reset_index(drop=True, inplace=True)
        return pivot_df

    def perform_anova(anova_dataframe):
        results = {}
        f_statistic = None
        p_value = None
        unique_postfixes = set(col.split('_')[-1]
                               for col in anova_dataframe.columns)
        for postfix in unique_postfixes:
            columns_with_postfix = [
                col for col in anova_dataframe.columns if col.endswith(postfix)]
            if len(columns_with_postfix) > 1:
                args = [anova_dataframe[col] for col in columns_with_postfix]
                f_statistic, p_value = f_oneway(*args)
                results[postfix] = {
                    'f_statistic': f_statistic, 'p_value': p_value}

        return results

    def perform_tukey_hsd_test(anova_dataframe):
        tukey_results = {}
        unique_postfixes = set(col.split('_')[-1]
                               for col in anova_dataframe.columns)
        for postfix in unique_postfixes:
            columns_with_postfix = [
                col for col in anova_dataframe.columns if col.endswith(postfix)]

            if len(columns_with_postfix) > 1:
                data = pd.melt(anova_dataframe[columns_with_postfix].reset_index(), id_vars=[
                               'index'], value_vars=columns_with_postfix)
                data.columns = ['index', 'group', 'value']
                tukey_result = mc.MultiComparison(
                    data['value'], data['group']).tukeyhsd()
                tukey_results[postfix] = tukey_result.summary()

        return tukey_results

    def store_results_to_file(anova_results, tukey_results, control_parameter, value):
        def get_keys_from_anova_and_tukey(anova_results, tukey_results):
            anova_keys = list(anova_results.keys())
            tukey_keys = list(tukey_results.keys())
            return anova_keys, tukey_keys

        def iterate_over_combined_keys_and_write_to_file(anova_keys, tukey_keys):
            for anova_key, tukey_key in zip(anova_keys, tukey_keys):
                # Write ANOVA result
                output = f"""
    Metric: {anova_key}
    Independent Variable: {control_parameter} = {value}
        F-statistic: {anova_results[anova_key]['f_statistic']}
        P-value: {anova_results[anova_key]['p_value']}
        Tukey:
            {tukey_results[tukey_key]}
                """
                file.write(output)

        with open(ANOVA_RESULTS, 'a') as file:
            anova_keys, tukey_keys = get_keys_from_anova_and_tukey(
                anova_results, tukey_results)
            iterate_over_combined_keys_and_write_to_file(
                anova_keys, tukey_keys)

    do_anova_for_each_value_of_independent_variable(
        test_results_dataframe, control_parameter)
