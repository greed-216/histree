import hashlib
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import tempfile
import threading
import unittest

spec = importlib.util.spec_from_file_location('artifact_download', Path(__file__).resolve().parents[2] / 'deploy/ecs/download-artifact.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ArtifactDownloadTests(unittest.TestCase):
    def setUp(self):
        self.payload = bytes(range(256)) * 128
        self.requests = {}
        self.lock = threading.Lock()
        self.fail_first = False
        self.support_ranges = True
        test = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                header = self.headers.get('Range', '')
                with test.lock:
                    test.requests[header] = test.requests.get(header, 0) + 1
                    fail = test.fail_first and header == 'bytes=0-1023' and test.requests[header] == 1
                if fail:
                    self.send_error(503)
                    return
                match = re.fullmatch(r'bytes=(\d+)-(\d+)', header)
                if not test.support_ranges or not match:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(test.payload)
                    return
                start, end = map(int, match.groups())
                self.send_response(206)
                self.send_header('Content-Range', 'bytes {}-{}/{}'.format(start, end, len(test.payload)))
                self.end_headers()
                self.wfile.write(test.payload[start:end + 1])

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.directory = tempfile.TemporaryDirectory()
        self.destination = Path(self.directory.name) / 'bundle.zip'
        self.url = 'http://127.0.0.1:' + str(self.server.server_port) + '/artifact'
        self.digest = hashlib.sha256(self.payload).hexdigest()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def download(self, digest=None):
        module.download(self.url, self.destination, digest or self.digest, workers=4,
                        chunk_bytes=1024, retry_sleep=0, allow_http=True)

    def test_parallel_ranges_preserve_exact_bytes(self):
        self.download()
        self.assertEqual(self.destination.read_bytes(), self.payload)
        self.assertGreater(len(self.requests), 2)

    def test_transient_range_failure_is_retried(self):
        self.fail_first = True
        self.download()
        self.assertEqual(self.destination.read_bytes(), self.payload)
        self.assertEqual(self.requests['bytes=0-1023'], 2)

    def test_digest_failure_preserves_previous_file(self):
        self.destination.write_bytes(b'previous verified file')
        with self.assertRaisesRegex(RuntimeError, 'digest mismatch'):
            self.download('0' * 64)
        self.assertEqual(self.destination.read_bytes(), b'previous verified file')
        self.assertFalse(Path(str(self.destination) + '.partial').exists())

    def test_unsupported_ranges_are_rejected(self):
        self.support_ranges = False
        with self.assertRaisesRegex(RuntimeError, 'support byte ranges'):
            self.download()
        self.assertFalse(self.destination.exists())


if __name__ == '__main__':
    unittest.main()
