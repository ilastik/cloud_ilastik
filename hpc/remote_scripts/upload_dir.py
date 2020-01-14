#!/usr/bin/env python

"""Upload directory to S3.

Number of upload threads should exceed number of available processors as workload is IO bound.
"""

import argparse
import os
import pathlib
from concurrent.futures import ThreadPoolExecutor

import boto3
import tqdm
from boto3.s3.transfer import TransferConfig
from botocore.client import Config
from botocore.exceptions import ReadTimeoutError, ConnectTimeoutError

MB = 1024 ** 2


parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('directory', type=pathlib.Path, help='directory to upload')
parser.add_argument('bucket_destination', type=str, help='destination bucket')
parser.add_argument('-n', '--num-workers', type=int, default=os.cpu_count() * 4, help="number of upload threads")
parser.add_argument('-t', '--timeout', type=int, default=60, help="timeout")
parser.add_argument('-r', '--retries', type=int, default=2, help="number of retries")
parser.add_argument('-i', '--interactive', action='store_true', help='show progress bar')


def _getenv_or_raise(key):
    val = os.getenv(key)
    if val is None:
        raise RuntimeWarning(f"Please specify environment variable {key}")
    return val


def main():
    args = parser.parse_args()
    if not args.directory.is_dir():
        raise ValueError(f"{args.directory} is not a directory")

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

    def _upload(path: pathlib.Path) -> None:
        entry = str(path)
        ex = None
        for _ in range(args.retries):
            try:
                s3_client.upload_file(entry, args.bucket_destination, entry, Config=transer_config)
                return
            except (ReadTimeoutError, ConnectTimeoutError) as timeout_ex:
                ex = timeout_ex

        raise ex

    files_to_upload = list(filter(pathlib.Path.is_file, args.directory.rglob("*")))

    with ThreadPoolExecutor(max_workers=args.num_workers) as ex:
        it = tqdm.tqdm(
            ex.map(_upload, files_to_upload),
            desc=f"Uploading {args.directory} to {args.bucket_destination}",
            total=len(files_to_upload),
            disable=not args.interactive,
            unit="files",
        )
        for _ in it:
            pass


if __name__ == "__main__":
    exit(main())
