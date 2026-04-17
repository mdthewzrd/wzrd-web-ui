"""WebSocket-based PTY terminal endpoint."""

from __future__ import annotations

import asyncio
import fcntl
import json
import logging
import os
import pty
import struct
import sys
import termios
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    """WebSocket endpoint for terminal I/O via PTY."""
    await websocket.accept()

    master_fd: Optional[int] = None
    pid: Optional[int] = None
    reader_task: Optional[asyncio.Task] = None

    try:
        # Spawn a PTY with bash
        pid, master_fd = pty.fork()
        if pid == 0:
            # Child process — exec bash
            shell = os.environ.get("SHELL", "/bin/bash")
            os.execvp(shell, [shell])

        # Set initial terminal size
        cols, rows = 80, 24
        _set_pty_size(master_fd, cols, rows)

        # Set master fd to non-blocking
        flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
        fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        loop = asyncio.get_event_loop()

        async def read_pty():
            """Read output from PTY and send to WebSocket."""
            while True:
                try:
                    data = await loop.run_in_executor(None, _read_fd, master_fd)
                    if data is None:
                        # PTY closed
                        if websocket.client_state == WebSocketState.CONNECTED:
                            await websocket.close()
                        break
                    if isinstance(data, bytes):
                        text = data.decode("utf-8", errors="replace")
                    else:
                        text = data
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_json({"type": "output", "data": text})
                except Exception:
                    break

        reader_task = asyncio.create_task(read_pty())

        # Main loop: read from WebSocket and write to PTY
        while True:
            try:
                raw = await websocket.receive_text()
            except WebSocketDisconnect:
                break

            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                # Plain text input
                if isinstance(raw, str):
                    _write_fd(master_fd, raw.encode("utf-8"))
                continue

            msg_type = msg.get("type")

            if msg_type == "input":
                data = msg.get("data", "")
                _write_fd(master_fd, data.encode("utf-8"))

            elif msg_type == "resize":
                cols = msg.get("cols", 80)
                rows = msg.get("rows", 24)
                _set_pty_size(master_fd, cols, rows)

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.debug("Terminal WebSocket error", exc_info=True)
    finally:
        if reader_task and not reader_task.done():
            reader_task.cancel()
        if master_fd is not None:
            try:
                os.close(master_fd)
            except OSError:
                pass
        if pid is not None and pid > 0:
            try:
                os.kill(pid, 9)  # SIGKILL the child shell
            except OSError:
                pass


def _read_fd(fd: int) -> Optional[bytes]:
    """Blocking read from file descriptor."""
    try:
        return os.read(fd, 65536)
    except OSError:
        return None


def _write_fd(fd: int, data: bytes):
    """Write to file descriptor."""
    try:
        os.write(fd, data)
    except OSError:
        pass


def _set_pty_size(fd: int, cols: int, rows: int):
    """Set PTY window size."""
    try:
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
    except OSError:
        pass
