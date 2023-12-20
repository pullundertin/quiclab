import yaml


def get_test_configuration_of_json_file(json_file):
    # Load the configuration file
    with open('test_cases.yaml', 'r') as file:
        test_case_settings = yaml.safe_load(file)

    # Function to search for keys with list values
    def find_keys_with_list_values(data):
        key_with_list = None
        for key, value in data['cases'].items():
            if isinstance(value, list) and key != 'mode':
                key_with_list = key
        return key_with_list

    # Search for keys with list values
    independent_variable = find_keys_with_list_values(test_case_settings)
    if independent_variable != None:
        independent_variables = test_case_settings['cases'][independent_variable]
    cases = test_case_settings['cases']
    modes = test_case_settings['cases']['mode']
    index = 1
    if independent_variable != None:
        for mode in (modes):
            for element in (independent_variables):
                if f'case_{index}_' in json_file:
                    test_case = {
                        **cases,
                        'mode': mode,
                        independent_variable: element,
                    }
                    return test_case
                index += 1
    else:
        for mode in (modes):
            if f'case_{index}_' in json_file:
                test_case = {
                    **cases,
                    'mode': mode,
                }
                return test_case
            index += 1

