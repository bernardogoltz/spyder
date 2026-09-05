# -*- coding: utf-8 -*-
"""QThread que segura um ClaudeSDKClient num loop asyncio próprio."""

from __future__ import annotations

import asyncio
from typing import Optional

from qtpy.QtCore import QThread, Signal

from setup_spyder.render import format_assistant_blocks, format_result_line


class ClaudeWorker(QThread):
    """Uma sessão = uma thread. Não reinicie: crie outra instância."""

    sig_text = Signal(str)
    sig_tool = Signal(str)
    sig_thinking = Signal()
    sig_result = Signal(str)
    sig_error = Signal(str)
    sig_busy = Signal(bool)
    sig_ready = Signal()

    def __init__(self, options, parent=None):
        super().__init__(parent)
        self._options = options
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue: Optional[asyncio.Queue] = None
        self._client = None

    def run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._amain())
        except Exception as exc:  # pragma: no cover
            self.sig_error.emit(str(exc))
        finally:
            try:
                self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            except Exception:
                pass
            self._loop.close()
            self._loop = None
            self._client = None
            self._queue = None

    async def _amain(self):
        try:
            from claude_agent_sdk import ClaudeSDKClient
        except ImportError:
            self.sig_error.emit(
                "claude-agent-sdk não está instalado neste venv "
                "(Python >= 3.10)."
            )
            return

        self._queue = asyncio.Queue()
        try:
            options = self._options
            async with ClaudeSDKClient(options=options) as client:
                self._client = client
                self.sig_ready.emit()
                while True:
                    item = await self._queue.get()
                    if item is None:
                        break
                    await self._run_query(client, item)
        except Exception as exc:
            self.sig_error.emit(str(exc))
        finally:
            self._client = None

    async def _run_query(self, client, prompt: str):
        from claude_agent_sdk import AssistantMessage, ResultMessage

        self.sig_busy.emit(True)
        try:
            await client.query(prompt)
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for linha in format_assistant_blocks(message.content):
                        if linha == "⋯ pensamento":
                            self.sig_thinking.emit()
                        elif linha.startswith("● "):
                            self.sig_tool.emit(linha)
                        else:
                            self.sig_text.emit(linha)
                elif isinstance(message, ResultMessage):
                    self.sig_result.emit(
                        format_result_line(
                            duration_ms=message.duration_ms,
                            cost_usd=message.total_cost_usd,
                            is_error=message.is_error,
                            num_turns=message.num_turns,
                        )
                    )
        except Exception as exc:
            self.sig_error.emit(str(exc))
        finally:
            self.sig_busy.emit(False)

    def submit(self, prompt: str) -> None:
        if self._loop is None or self._queue is None:
            self.sig_error.emit("sessão do Claude ainda não está pronta")
            return
        asyncio.run_coroutine_threadsafe(self._queue.put(prompt), self._loop)

    def interrupt(self) -> None:
        client = self._client
        loop = self._loop
        if client is None or loop is None:
            return
        asyncio.run_coroutine_threadsafe(client.interrupt(), loop)

    def shutdown(self, timeout_ms: int = 8000) -> None:
        loop = self._loop
        queue = self._queue
        client = self._client
        if loop is None:
            return

        async def _stop():
            if client is not None:
                try:
                    await client.disconnect()
                except Exception:
                    pass
            if queue is not None:
                await queue.put(None)

        asyncio.run_coroutine_threadsafe(_stop(), loop)
        self.wait(timeout_ms)
        if self.isRunning():
            self.terminate()
            self.wait(1000)
