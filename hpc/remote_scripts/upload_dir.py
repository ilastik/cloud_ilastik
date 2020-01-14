#!/usr/bin/env python
"""
To use:

1. Install deps with conda
conda install -c conda-forge boto3

2. Run
python upload_dir.py <source_directory> <destination_bucket>

NOTE: Number of threads should exceed number of available processors as workload is IO bound
"""
import argparse
import os
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.client import Config
from botocore.exceptions import ReadTimeoutError, ConnectTimeoutError

MB = 1024 ** 2

def walk(directory: str):
    path = pathlib.Path(directory)
    if not path.is_dir():
        raise ValueError("Expected directory")

    for entry in path.iterdir():
        if entry.is_dir():
            yield from walk(entry)
        else:
            yield str(entry)


parser = argparse.ArgumentParser(description='Upload directory to S3')
parser.add_argument('directory', type=str, help='a directory to upload')
parser.add_argument('bucket_destination', type=str, help='a directory to upload')
parser.add_argument('-n', '--num-workers', type=int, default=os.cpu_count() * 4, help="number of upload threads")
parser.add_argument('-t', '--timeout', type=int, default=60, help="timeout")
parser.add_argument('-r', '--retries', type=int, default=2, help="timeout")


def _getenv_or_raise(key):
    val = os.getenv(key)
    if val is None:
        raise RuntimeWarning(f"Please specify environment variable {key}")
    return val


def main():
    args = parser.parse_args()

    key = _getenv_or_raise("S3_KEY")
    secret = _getenv_or_raise("S3_SECRET")

    session = boto3.Session(key, secret)
    transer_config = TransferConfig(multipart_threshold=256 * MB, use_threads=False)

    client_config = Config(
        connect_timeout=args.timeout,
        read_timeout=args.timeout,
        # Swift S3 middleware doesn't support s3v2 signatures
        signature_version="s3",
        # Uploading big files results in multistep operation, retry on CompleteMultipartUpload cat result in error as it's not idempotent
        retries={"max_attempts": 0},
    )

    s3_client = session.client("s3", config=client_config, endpoint_url="https://object.cscs.ch/")

    def _upload(entry):
        ex = None
        for _ in range(args.retries):
            try:
                s3_client.upload_file(entry, args.bucket_destination, entry, Config=transer_config)
                return
            except (ReadTimeoutError, ConnectTimeoutError) as timeout_ex:
                ex = timeout_ex

        raise ex

    with ThreadPoolExecutor(max_workers=args.num_workers) as ex:
        print(f"Uploading {args.directory} to {args.bucket_destination}")
        files_to_upload = list(walk(args.directory))
        total_files = len(files_to_upload)
        uploaded = 0

        def _report():
            sys.stdout.write(f"Upload status: {uploaded}/{total_files} ({100 * uploaded/total_files:.2f}%)\n")
            sys.stdout.flush()

        _report()
        for entry in ex.map(_upload, files_to_upload):
            uploaded += 1
            _report()


if __name__ == "__main__":
    exit(main())