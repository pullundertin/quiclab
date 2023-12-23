
from tqdm import tqdm


# for i in tqdm(range(0, 100), total = 500,
#               desc ="Text You Want"):
#     sleep(.1)

def get_process_bar_status_cases(case, cases):
    tqdm(case, total=cases, desc="Test Case")


def get_process_bar_status_iterations(iteration, iterations):
    tqdm(iteration, total=iterations, desc="Iteration")
