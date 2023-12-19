import yaml


def get_test_configuration_of_json_file(json_file):
    # Load the configuration file
    with open('test_cases.yaml', 'r') as file:
        config = yaml.safe_load(file)

    common_fields = config['common_fields']

    modes = config['cases']['mode']
    delays = config['cases']['delay']
    index = 1
    for mode in (modes):
        for delay in (delays):
            if f'case_{index}_' in json_file:
                case_configurations = {
                    'mode': mode,
                    'delay': delay,
                    **common_fields
                }
                return case_configurations
            index = index + 1

