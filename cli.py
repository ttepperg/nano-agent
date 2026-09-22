import argparse

def parse_args():
    """ Parse CLI input arguments """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--max-iters",
        type=int,
        default=5,
        help="Maximum number of LLM iterations per task",
        required=False
    )
    return parser.parse_args()
