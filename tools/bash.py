import asyncio
import concurrent.futures
import os
import sys
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import TOOL_OUTPUT_MAX_CHARS, BASH_TOOL_TIMEOUT

def tool_info():
    return {
        "name": "bash",
        "description": """Run commands in a bash shell\n
* When invoking this tool, the contents of the "command" parameter does NOT need to be XML-escaped.\n
* You don't have access to the internet via this tool.\n
* You do have access to a mirror of common linux and python packages via apt and pip.\n
* State is persistent across command calls and discussions with the user.\n
* To inspect a particular line range of a file, e.g. lines 10-25, try 'sed -n 10,25p /path/to/the/file'.\n
* Please avoid commands that may produce a very large amount of output.\n
* Please run long lived commands in the background, e.g. 'sleep 10 &' or start a server in the background.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to run."
                }
            },
            "required": ["command"]
        }
    }

class BashSession:
    """A session of a bash shell."""
    def __init__(self):
        self._started = False
        self._process = None
        self._timed_out = False
        self._timeout = BASH_TOOL_TIMEOUT
        self._sentinel = "<<exit>>"
        self._output_delay = 0.2  # seconds

    async def start(self):
        if self._started:
            return
        self._process = await asyncio.create_subprocess_shell(
            "/bin/bash -i",
            preexec_fn=os.setsid,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy()
        )
        self._started = True

    def stop(self):
        if not self._started:
            return
        if self._process and self._process.returncode is None:
            self._process.terminate()
        self._process = None
        self._started = False

    async def run(self, command):
        if not self._started:
            raise ValueError("Session has not started.")
        if self._process.returncode is not None:
            raise ValueError(f"Bash has exited with returncode {self._process.returncode}")
        if self._timed_out:
            raise ValueError(
                f"Timed out: bash has not returned in {self._timeout} seconds and must be restarted."
            )
        
        # Send command
        self._process.stdin.write(
            command.encode() + f"; echo '{self._sentinel}'\n".encode()
        )
        await self._process.stdin.drain()

        # Read output until sentinel
        try:
            output = ''
            start_time = asyncio.get_event_loop().time()
            
            while True:
                if asyncio.get_event_loop().time() - start_time > self._timeout:
                    self._timed_out = True
                    raise ValueError(
                        f"Timed out: bash has not returned in {self._timeout} seconds and must be restarted."
                    )
                
                await asyncio.sleep(self._output_delay)
                # Read from the internal buffer
                stdout_data = self._process.stdout._buffer.decode(errors='ignore')
                stderr_data = self._process.stderr._buffer.decode(errors='ignore')
                
                if self._sentinel in stdout_data:
                    output = stdout_data[: stdout_data.index(self._sentinel)]
                    break

            # Clear buffers
            self._process.stdout._buffer.clear()
            self._process.stderr._buffer.clear()

            output = output.strip()
            error = stderr_data.strip()

            return output, error

        except Exception as e:
            self._timed_out = True
            raise ValueError(str(e))


def maybe_truncate(content: str, max_length: int = TOOL_OUTPUT_MAX_CHARS) -> str:
    """Truncate long output, keeping head and tail for context."""
    if len(content) > max_length:
        half = max_length // 2
        return content[:half] + f"\n\n... ({len(content) - max_length} characters truncated) ...\n\n" + content[-half:]
    return content

def filter_error(error):
    filtered_lines = []
    i = 0
    error_lines = error.splitlines()
    while i < len(error_lines):
        line = error_lines[i]

        if "Inappropriate ioctl for device" in line:
            i += 3
            if i < len(error_lines) and '<<exit>>' in error_lines[i]:
                i += 1
            while i < len(error_lines) - 1:
                filtered_lines.append(error_lines[i])
                i += 1
            i += 1
            continue

        filtered_lines.append(line)
        i += 1
    return '\n'.join(filtered_lines).strip()


class _PersistentLoop:
    """Manages a persistent asyncio event loop in a background thread for session reuse."""

    def __init__(self):
        self._loop = None
        self._thread = None
        self._session = None
        self._lock = threading.Lock()

    def _ensure_loop(self):
        if self._loop is None or not self._loop.is_running():
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
            self._thread.start()

    def _run_coro(self, coro):
        """Submit a coroutine to the persistent loop and wait for the result."""
        self._ensure_loop()
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    async def _execute(self, command):
        """Execute a command, creating or reusing the session as needed."""
        if self._session is None or self._session._timed_out or (
            self._session._process is not None and self._session._process.returncode is not None
        ):
            if self._session is not None:
                self._session.stop()
            self._session = BashSession()

        if not self._session._started:
            await self._session.start()

        output, error = await self._session.run(command)
        error = filter_error(error)
        result = ""
        if output:
            result += output
        if error:
            result += "\nError:\n" + error
        return maybe_truncate(result.strip())

    def run(self, command):
        with self._lock:
            try:
                return self._run_coro(self._execute(command))
            except Exception as e:
                # Reset session on failure
                if self._session is not None:
                    try:
                        self._session.stop()
                    except Exception:
                        pass
                    self._session = None
                return f"Error: {str(e)}"


_persistent_loop = _PersistentLoop()


def tool_function(command):
    return _persistent_loop.run(command)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bash.py '<command>'")
    else:
        input_command = ' '.join(sys.argv[1:])
        result = tool_function(input_command)
        print(result)
