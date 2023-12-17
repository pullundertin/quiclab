import yaml

def get_mode_of_file(json_file):
    # Load the configuration file
    with open('test_cases.yaml', 'r') as file:
        config = yaml.safe_load(file)

    # Mapping configuration to json_files
    for index, case in enumerate(config['cases'], start=1):
        if f'case_{index}_' in json_file:
            return case['mode']


