
from tqdm import tqdm

# Maximum width of desc
max_desc_width = 40


# Create a format string with the desired fixed width for desc
bar_default = f" | {{n_fmt}}/{{total_fmt}}:  {{percentage:3.0f}}%    [{{bar}}]"
bar_format_program = f"  {{desc:<{max_desc_width - 2}}}" + bar_default
bar_format_test_cases = f"        {{desc:<{max_desc_width - 8}}}" + bar_default
bar_format_iterations = f"            {{desc:<{max_desc_width - 12}}}" + bar_default
program_step = 0
ascii = ' ='


def update_program_progress_bar(current_step_name):
    global program_step
    program_step += 1
    total_program_steps = 11
    with tqdm(total=total_program_steps, desc="Program", unit="step", bar_format=bar_format_program, ascii=ascii) as pbar:
        pbar.set_description(current_step_name)
        pbar.update(program_step)


def update_test_progress_bar(test_case, number_of_test_cases, iteration, number_of_iterations):
    if iteration == 1:
        get_progress_bar_status_cases(test_case, number_of_test_cases)
    get_progress_bar_status_iterations(iteration, number_of_iterations)


def get_progress_bar_status_cases(test_case, number_of_test_cases):
    with tqdm(total=number_of_test_cases, desc="Test Cases", unit="step", bar_format=bar_format_test_cases, ascii=ascii) as pbar:
        pbar.update(test_case)


def get_progress_bar_status_iterations(iteration, number_of_iterations):
    with tqdm(total=number_of_iterations, desc="Iterations", unit="step", bar_format=bar_format_iterations, ascii=ascii) as pbar:
        pbar.update(iteration)
