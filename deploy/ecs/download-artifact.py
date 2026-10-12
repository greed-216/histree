#!/usr/bin/env python3
"""Download a GitHub artifact in bounded ranges, then verify and install it atomically."""
import concurrent.futures
import hashlib
import os
from pathlib import Path
import re
import sys
import time
import urllib.request


def download(url, destination, digest, workers=12, chunk_bytes=2 * 1024 * 1024,
             attempts=3, retry_sleep=1, allow_http=False):
    schemes = ('http://', 'https://') if allow_http else ('https://',)
    if not url.startswith(schemes):
        raise ValueError('HTTPS artifact URL required')
    if not re.fullmatch('[a-f0-9]{64}', digest):
        raise ValueError('Invalid artifact digest')
    with urllib.request.urlopen(urllib.request.Request(url, headers={'Range': 'bytes=0-0'}), timeout=30) as response:
        match = re.fullmatch(r'bytes 0-0/(\d+)', response.headers.get('Content-Range', ''))
        if response.status != 206 or not match or len(response.read(2)) != 1:
            raise RuntimeError('Artifact server must support byte ranges')
        total = int(match.group(1))
    if not 0 < total <= 1024 * 1024 * 1024:
        raise ValueError('Unexpected artifact size')
    destination = Path(destination)
    partial = Path(str(destination) + '.partial')
    fd = os.open(str(partial), os.O_CREAT | os.O_RDWR | os.O_TRUNC | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    try:
        os.ftruncate(fd, total)

        def fetch_range(start, end):
            for attempt in range(attempts):
                try:
                    header = 'bytes={}-{}'.format(start, end - 1)
                    request = urllib.request.Request(url, headers={'Range': header})
                    with urllib.request.urlopen(request, timeout=120) as response:
                        expected = 'bytes {}-{}/{}'.format(start, end - 1, total)
                        if response.status != 206 or response.headers.get('Content-Range') != expected:
                            raise RuntimeError('Unexpected range response')
                        data = response.read(end - start + 1)
                    if len(data) != end - start:
                        raise RuntimeError('Incomplete artifact range')
                    offset = 0
                    while offset < len(data):
                        offset += os.pwrite(fd, data[offset:], start + offset)
                    return len(data)
                except Exception:
                    if attempt == attempts - 1:
                        raise RuntimeError('Artifact range failed at byte ' + str(start)) from None
                    time.sleep(retry_sleep * (attempt + 1))

        done, reported = 0, 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(fetch_range, start, min(start + chunk_bytes, total))
                       for start in range(0, total, chunk_bytes)]
            for future in concurrent.futures.as_completed(futures):
                done += future.result()
                if done - reported >= 20 * 1024 * 1024 or done == total:
                    print('Downloaded {} / {} bytes'.format(done, total), flush=True)
                    reported = done
        os.fsync(fd)
    except Exception:
        partial.unlink()
        raise
    finally:
        os.close(fd)
    checksum = hashlib.sha256()
    with partial.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(block)
    if checksum.hexdigest() != digest:
        partial.unlink()
        raise RuntimeError('Artifact digest mismatch')
    os.replace(str(partial), str(destination))
    print('Verified artifact SHA-256: ' + digest, flush=True)


if __name__ == '__main__':
    try:
        if len(sys.argv) != 4:
            raise ValueError('Expected artifact URL, destination and digest')
        download(*sys.argv[1:])
    except Exception as error:
        # Do not expose a signed artifact URL through an HTTP exception or traceback.
        reason = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print('Artifact download failed: ' + reason, file=sys.stderr)
        sys.exit(1)
