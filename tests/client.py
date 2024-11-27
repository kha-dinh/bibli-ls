from lsprotocol.types import ClientCapabilities, InitializeParams, InitializedParams
from pygls.lsp.client import BaseLanguageClient
import sys
import os

from tests import PROJECT_ROOT, TEST_ROOT
from tests.utils import as_uri


class BibliClient(BaseLanguageClient):
    def __init__(self, test_root=TEST_ROOT):
        super().__init__("bibli-test", "0.1")
        self._test_root = test_root

    async def __aenter__(self):
        await self.start_io(
            sys.executable,
            os.path.join(PROJECT_ROOT, "bibli_ls/cli.py"),
            "--log-file",
            os.path.join(self._test_root, "test_lsp.log"),
            "-vvv",
        )

        response = await self.initialize_async(
            InitializeParams(
                capabilities=ClientCapabilities(),
                root_uri=as_uri(self._test_root),
                root_path=str(self._test_root),
            )
        )
        assert response

        self.initialized(InitializedParams())
        # response = await self.initialize_async(
        #     InitializeParams(
        #         capabilities=ClientCapabilities(),
        #         root_uri=as_uri(TEST_ROOT),
        #         root_path=str(TEST_ROOT),
        #     )
        # )
        # assert response
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown_async(None)
        pass
        # await self.stop()
