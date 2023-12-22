import pandas as pd
from scipy.stats import f_oneway
import statsmodels.stats.multicomp as mc
from modules.prerequisites import read_configuration
import os

ANOVA_RESULTS = read_configuration().get("ANOVA_RESULTS")


def do_anova(df):
    if os.path.exists(ANOVA_RESULTS):
        os.remove(ANOVA_RESULTS)

    def combine_handshake_and_connection_postfixes_with_each_available_mode(df):
        for postfix in ['hs', 'conn']:
            unique_modes = df['mode'].unique()
            results = [
                f"{mode.split('_')[0]}_{postfix}" for mode in unique_modes]
            combined_df = generate_dataframe_with_all_values_combined(
                results, df)
            f_statistic, p_value = perform_anova(combined_df, results)
            tukey_result = perform_tukey_hsd_test(combined_df, results)
            store_results_to_file(f_statistic, p_value, tukey_result)

    def generate_dataframe_with_all_values_combined(results, df):
        combined_data = {}
        for column in results:
            combined_data[column] = df[column].dropna().tolist()

        combined_df = pd.DataFrame(combined_data)

        return combined_df

    def perform_anova(combined_df, results):

        f_statistic, p_value = f_oneway(
            combined_df[results[0]], combined_df[results[1]], combined_df[results[2]])
        return f_statistic, p_value

    def perform_tukey_hsd_test(combined_df, results):

        data = pd.melt(combined_df.reset_index(), id_vars=['index'], value_vars=[
            results[0], results[1], results[2]])
        data.columns = ['index', 'group', 'value']

        tukey_result = mc.MultiComparison(
            data['value'], data['group']).tukeyhsd()
        return tukey_result

    def store_results_to_file(f_statistic, p_value, tukey_result):
        output = f"""
        F-statistic: {f_statistic}
        P-value: {p_value}
        Tukey: 
        {tukey_result}
        """
        with open(ANOVA_RESULTS, 'a') as file:
            file.write(output)

    combine_handshake_and_connection_postfixes_with_each_available_mode(
        df)
