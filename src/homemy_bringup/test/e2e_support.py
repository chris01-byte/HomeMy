"""Shared helpers of the end-to-end tests: an app-like WebSocket client,
launching a profile in its own ROS domain, and setting parameters.

Everything is simulated. No hardware is used.
"""

from __future__ import annotations

import base64
import json
import os
import random
import signal
import socket
import struct
import subprocess
import tempfile
import time
from contextlib import contextmanager

import rclpy
from rcl_interfaces.msg import Parameter as ParameterMsg, ParameterType, ParameterValue
from rcl_interfaces.srv import SetParameters
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node

# With HOMEMY_RECORD_FIXTURES=<dir> the tests write the frames they received
# to that directory (see test_app_bridge_e2e.py).
FIXTURE_DIR = os.environ.get("HOMEMY_RECORD_FIXTURES")


def record(name: str, frame: dict) -> None:
    if not FIXTURE_DIR:
        return
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    with open(os.path.join(FIXTURE_DIR, f"{name}.json"), "w", encoding="utf-8") as target:
        json.dump(frame, target, ensure_ascii=False, sort_keys=True, indent=1)
        target.write("\n")


# --------------------------------------------------------------------- client


class WebSocketClient:
    """Minimal RFC 6455 text client, enough to act like the app."""

    def __init__(self, port: int) -> None:
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=10)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        self.sock.sendall(
            (
                "GET / HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{port}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                "Sec-WebSocket-Version: 13\r\n\r\n"
            ).encode("ascii")
        )
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(1024)
            if not chunk:
                raise AssertionError("handshake closed")
            response += chunk
        head, _, rest = response.partition(b"\r\n\r\n")
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise AssertionError(f"unexpected handshake: {head!r}")
        self.buffer = rest
        self.inbox: list[dict] = []

    def send(self, payload: dict) -> None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        mask = os.urandom(4)
        header = bytearray([0x81])
        if len(data) < 126:
            header.append(0x80 | len(data))
        elif len(data) < 65536:
            header.append(0x80 | 126)
            header += struct.pack("!H", len(data))
        else:
            header.append(0x80 | 127)
            header += struct.pack("!Q", len(data))
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
        self.sock.sendall(bytes(header) + mask + masked)

    def _read_exact(self, size: int) -> bytes:
        while len(self.buffer) < size:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise AssertionError("socket closed")
            self.buffer += chunk
        data, self.buffer = self.buffer[:size], self.buffer[size:]
        return data

    def _receive_frame(self) -> dict | None:
        first, second = self._read_exact(2)
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._read_exact(8))[0]
        payload = self._read_exact(length)
        opcode = first & 0x0F
        if opcode != 0x1:
            return None
        return json.loads(payload.decode("utf-8"))

    def wait_for(self, predicate, timeout: float = 15.0) -> dict:
        """Return the first message (old or new) that matches the predicate."""

        for index, message in enumerate(self.inbox):
            if predicate(message):
                return self.inbox.pop(index)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.sock.settimeout(max(0.05, deadline - time.monotonic()))
            try:
                message = self._receive_frame()
            except socket.timeout:
                break
            if message is None:
                continue
            if predicate(message):
                return message
            self.inbox.append(message)
            del self.inbox[:-200]
        raise AssertionError("expected message not received")

    def wait_status(self, topic: str, predicate=lambda s: True, timeout: float = 15.0,
                    record_as: str | None = None) -> dict:
        def matches(message):
            if message.get("op") != "publish" or message.get("topic") != topic:
                return False
            return predicate(json.loads(message["msg"]["data"]))

        frame = self.wait_for(matches, timeout)
        if record_as:
            record(record_as, frame)
        return json.loads(frame["msg"]["data"])

    def drain(self) -> None:
        self.inbox.clear()

    def close(self) -> None:
        self.sock.close()


def publish_json(client: WebSocketClient, topic: str, payload: dict) -> None:
    """The app's StringPublishFrame: JSON text inside std_msgs/String."""

    client.send({"op": "publish", "topic": topic, "msg": {"data": json.dumps(payload)}})




def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]




@contextmanager
def launched(launch_file: str, arguments: list[str], ready_timeout: float = 40.0):
    """Start ``ros2 launch homemy_bringup <launch_file>`` in its own domain.

    Yields a dict with the bridge port, a probe node in the same domain, its
    context, and the log path. Stops the whole process group afterwards.
    """

    domain = random.randint(101, 199)
    port = _free_port()
    storage = tempfile.TemporaryDirectory(prefix="homemy-e2e-")
    env = dict(os.environ, ROS_DOMAIN_ID=str(domain), ROS_AUTOMATIC_DISCOVERY_RANGE="LOCALHOST")
    env.pop("ROS_LOCALHOST_ONLY", None)
    log = tempfile.NamedTemporaryFile(prefix="homemy-e2e-launch-", suffix=".log", delete=False)
    process = subprocess.Popen(
        ["ros2", "launch", "homemy_bringup", launch_file,
         f"bridge_port:={port}", f"storage_root:={storage.name}", *arguments],
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    deadline = time.monotonic() + ready_timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        try:
            socket.create_connection(("127.0.0.1", port), timeout=1).close()
            break
        except OSError:
            time.sleep(0.5)
    else:
        process.kill()
    if process.poll() is not None:
        log.seek(0)
        raise AssertionError("launch ended early:\n" + open(log.name).read()[-4000:])

    context = rclpy.Context()
    rclpy.init(context=context, domain_id=domain)
    node = Node("homemy_e2e_probe", context=context)
    try:
        yield {"port": port, "node": node, "context": context, "log": log.name, "storage": storage.name}
    finally:
        node.destroy_node()
        rclpy.shutdown(context=context)
        os.killpg(process.pid, signal.SIGINT)
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        storage.cleanup()


def set_parameter(stack, node_name: str, name: str, value) -> None:
    """Set one parameter of a running node.

    Uses its own short-lived node and executor, so that a probe node spun by
    the test keeps its executor.
    """

    node = Node(f"homemy_e2e_param_{random.randint(0, 10**9)}", context=stack["context"])
    executor = SingleThreadedExecutor(context=stack["context"])
    executor.add_node(node)
    try:
        client = node.create_client(SetParameters, f"/{node_name}/set_parameters")
        assert client.wait_for_service(timeout_sec=10), f"{node_name} has no parameter service"
        parameter_value = ParameterValue()
        if isinstance(value, bool):
            parameter_value.type = ParameterType.PARAMETER_BOOL
            parameter_value.bool_value = value
        elif isinstance(value, float):
            parameter_value.type = ParameterType.PARAMETER_DOUBLE
            parameter_value.double_value = value
        else:
            parameter_value.type = ParameterType.PARAMETER_STRING
            parameter_value.string_value = str(value)
        request = SetParameters.Request(parameters=[ParameterMsg(name=name, value=parameter_value)])
        future = client.call_async(request)
        executor.spin_until_future_complete(future, timeout_sec=10)
        result = future.result()
        assert result is not None and all(item.successful for item in result.results)
    finally:
        executor.remove_node(node)
        executor.shutdown()
        node.destroy_node()
