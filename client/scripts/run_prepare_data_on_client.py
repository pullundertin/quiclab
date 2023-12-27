import os
import logging
import argparse
import shutil
from modules.logs import log_config


def arguments():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description='QuicLab Test Environment')

    parser.add_argument('-m', '--mode', type=str,
                        help='modes: tcp, aioquic, quicgo, lsquic')

    parser.add_argument('--parallel', choices=['True', 'False'],
                        help='enable/disable parallel downloads')
    parser.add_argument('--file_name_prefix', type=str,
                        help='prefix for pcap files')

    args = parser.parse_args()
    return args


def check_if_file_exists(lsquic_client_directory, filename):
    file_path = os.path.join(lsquic_client_directory, filename)
    if os.path.exists(file_path):
        return True
    else:
        return False


def move_lsquic_client_files(lsquic_client_directory, file, new_path):
    if not check_if_file_exists(lsquic_client_directory, file):
        logging.error(f"{os.getenv('HOST')}: {file} does not exist!")
    else:
        old_path = (os.path.join(lsquic_client_directory, file))
        shutil.move(old_path, new_path)
        logging.info(
            f"{os.getenv('HOST')}: {lsquic_client_directory}, {file} moved to {new_path}")
    # files = os.listdir(lsquic_client_directory)
    # for file in files:
    #     logging.info(f"{os.getenv('HOST')}: {file}")


def copy_keys_to_client_key_file(lsquic_client_directory, common_client_keys_file):
    # List all files in the directory
    def get_client_key_file_name(lsquic_client_directory):
        files_in_directory = os.listdir(lsquic_client_directory)

        keys_file = None

        for file in files_in_directory:
            if file.endswith('.keys'):
                if keys_file is None:
                    return file
                else:
                    return None  # More than one .keys file found
                    break

    client_key_file = get_client_key_file_name(lsquic_client_directory)

    # Open the source file in read mode
    with open(os.path.join(lsquic_client_directory, client_key_file), 'r') as source_file:
        keys = source_file.read()

    if check_if_file_exists(lsquic_client_directory, common_client_keys_file):
        write_mode = 'a'
    else:
        write_mode = 'w'
    # Open the destination file in append mode
    with open(common_client_keys_file, write_mode) as destination_file:
        # Append the source text to the destination file
        destination_file.write('\n')  # Add a newline for separation (optional)
        destination_file.write(keys)


if __name__ == "__main__":

    log_config()
    args = arguments()
    lsquic_client_directory = '/lsquic/client'
    new_download_path = f"/shared/downloads/{args.file_name_prefix}"
    common_client_keys_file = f"/shared/keys/client.key"

    move_lsquic_client_files(
        lsquic_client_directory, 'data.log', new_download_path)
    copy_keys_to_client_key_file(
        lsquic_client_directory, common_client_keys_file)
