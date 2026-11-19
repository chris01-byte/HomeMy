#!/usr/bin/env python3
"""Offline contract checks for the HomeMy app bridge mock.

The mock implements contracts/api/app-bridge.md. These tests run without
ROS, without a robot, and with synthetic data only.
"""

import base64
import json
import math
import os
import re
import socket
import struct
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mock_rosbridge as mock


class SemanticMockTests(unittest.TestCase):
    def setUp(self):
        self.state = mock.RobotState()

    def test_mock_map_fingerprint_is_stable_and_content_sensitive(self):
        initial = self.state.map_summary()['fingerprint']
        self.assertEqual(
            initial,
            '80c5498f9a8241fee01141dc04189ad814451d284a2f9c8aeaf597e94af9fa55',
        )
        self.state.advance_map()
        self.assertNotEqual(self.state.map_summary()['fingerprint'], initial)

    def test_save_creates_exact_persisted_semantic_reference(self):
        initial = self.state.semantic_status()
        self.assertFalse(initial['ok'])
        self.assertIsNone(initial['semantic_map']['map_ref'])
        response = self.state.save_map_for_rooms({
            'command': 'save',
            'name': 'wohnung',
            'request_id': 'ios-map-1',
        })
        self.assertTrue(response['ok'])
        self.assertEqual(response['event'], 'save_result')
        saved = self.state.last_saved_map
        semantic_reference = self.state.semantic_map['map_ref']
        self.assertEqual(saved['fingerprint'], semantic_reference['fingerprint'])
        self.assertEqual(saved['name'], semantic_reference['name'])
        self.assertEqual(saved['version'], semantic_reference['version'])
        self.assertRegex(
            saved['version'],
            re.compile(
                r'^[0-9]{8}T[0-9]{12}Z-[0-9a-f]{12}(?:-[0-9]{2})?$'
            ),
        )
        self.assertTrue(saved['version'].endswith(saved['fingerprint'][:12]))
        self.assertTrue(self.state.semantic_map['editable'])

    def test_save_request_is_idempotent_but_reuse_conflicts(self):
        command = {
            'command': 'save',
            'name': 'wohnung',
            'request_id': 'ios-map-1',
        }
        first = self.state.save_map_for_rooms(command)
        cached_signature, cached_outcome = self.state.map_request_cache['ios-map-1']
        self.assertRegex(cached_signature, r'^[0-9a-f]{64}$')
        self.assertEqual(set(cached_outcome), {'event', 'ok', 'message'})
        saved_fingerprint = first['storage']['last_saved']['fingerprint']
        self.state.advance_map()
        second = self.state.save_map_for_rooms(dict(command))
        current_fingerprint = self.state.map_summary()['fingerprint']
        self.assertNotEqual(current_fingerprint, saved_fingerprint)
        self.assertEqual(second['event'], first['event'])
        self.assertEqual(second['ok'], first['ok'])
        self.assertEqual(second['message'], first['message'])
        self.assertEqual(second['map']['summary']['fingerprint'], current_fingerprint)
        self.assertEqual(
            second['storage']['last_saved']['fingerprint'],
            saved_fingerprint,
        )
        self.assertNotEqual(second, first)
        conflict = self.state.save_map_for_rooms({
            'command': 'save',
            'name': 'falsch',
            'request_id': 'ios-map-1',
        })
        self.assertFalse(conflict['ok'])

    def test_boundary_only_room_is_saved_without_navigation_goal(self):
        self.state.save_map_for_rooms({
            'command': 'save',
            'name': 'wohnung',
            'request_id': 'ios-map-boundary-only',
        })
        fingerprint = self.state.semantic_map['map_ref']['fingerprint']
        room = {
            'id': 'room-boundary-only',
            'name': 'Abstellraum',
            'polygon': [
                {'x': -2.0, 'y': -1.0},
                {'x': 0.0, 'y': -1.0},
                {'x': 0.0, 'y': 1.0},
            ],
        }
        created = self.state.apply_semantic_command({
            'command': 'upsert_room',
            'request_id': 'ios-room-boundary-only',
            'map_fingerprint': fingerprint,
            'base_revision': 0,
            'room': room,
        })
        self.assertTrue(created['ok'])
        self.assertEqual(created['semantic_map']['rooms'], [room])

        rejected = self.state.apply_semantic_command({
            'command': 'upsert_room',
            'request_id': 'ios-room-null-goal',
            'map_fingerprint': fingerprint,
            'base_revision': 1,
            'room': dict(room, navigation_goal=None),
        })
        self.assertFalse(rejected['ok'])
        self.assertEqual(rejected['event'], 'validation_error')

    def test_room_upsert_silent_revision_conflict_and_delete(self):
        self.state.save_map_for_rooms({
            'command': 'save',
            'name': 'wohnung',
            'request_id': 'ios-map-1',
        })
        fingerprint = self.state.semantic_map['map_ref']['fingerprint']
        room = {
            'id': 'room-1',
            'name': 'Wohnzimmer',
            'color': '#4FB3A5',
            'polygon': [
                {'x': -2.0, 'y': -1.0},
                {'x': 0.0, 'y': -1.0},
                {'x': 0.0, 'y': 1.0},
            ],
            'navigation_goal': {'x': -1.0, 'y': -0.5, 'yaw': 0.0},
        }
        upsert_command = {
            'command': 'upsert_room',
            'request_id': 'ios-room-1',
            'map_fingerprint': fingerprint,
            'base_revision': 0,
            'room': room,
        }
        upsert = self.state.apply_semantic_command(upsert_command)
        cached_signature, cached_outcome = self.state.semantic_request_cache['ios-room-1']
        self.assertRegex(cached_signature, r'^[0-9a-f]{64}$')
        self.assertEqual(set(cached_outcome), {'event', 'ok', 'message'})
        self.assertTrue(upsert['ok'])
        self.assertEqual(upsert['event'], 'room_created')
        self.assertEqual(self.state.semantic_map['revision'], 1)
        self.assertEqual(self.state.semantic_map['rooms'], [room])

        # The HTTP endpoint /semantic-bump-silent performs the same state
        # transition without a status push. The client still believes the
        # acknowledged revision is 1 while the mock has advanced to 2.
        self.assertEqual(self.state.bump_semantic_revision(), 2)
        replay = self.state.apply_semantic_command(dict(upsert_command))
        self.assertEqual(replay['event'], upsert['event'])
        self.assertEqual(replay['ok'], upsert['ok'])
        self.assertEqual(replay['message'], upsert['message'])
        self.assertEqual(replay['semantic_map']['revision'], 2)
        self.assertNotEqual(replay, upsert)

        changed_payload = dict(upsert_command)
        changed_payload['room'] = dict(room, name='Anderer Name')
        conflict = self.state.apply_semantic_command(changed_payload)
        self.assertFalse(conflict['ok'])
        self.assertEqual(conflict['event'], 'request_id_conflict')
        self.assertEqual(conflict['semantic_map']['revision'], 2)

        stale = self.state.apply_semantic_command({
            'command': 'delete_room',
            'request_id': 'ios-room-stale',
            'map_fingerprint': fingerprint,
            'base_revision': 1,
            'room_id': 'room-1',
        })
        self.assertFalse(stale['ok'])
        self.assertEqual(stale['event'], 'revision_conflict')

        deleted = self.state.apply_semantic_command({
            'command': 'delete_room',
            'request_id': 'ios-room-2',
            'map_fingerprint': fingerprint,
            'base_revision': 2,
            'room_id': 'room-1',
        })
        self.assertTrue(deleted['ok'])
        self.assertEqual(deleted['event'], 'room_deleted')
        self.assertEqual(self.state.semantic_map['revision'], 3)
        self.assertEqual(self.state.semantic_map['rooms'], [])

        invalid = self.state.apply_semantic_command({
            'command': 'delete_room',
            'request_id': '../unsafe',
            'map_fingerprint': fingerprint,
            'base_revision': 3,
            'room_id': 'room-1',
        })
        self.assertFalse(invalid['ok'])
        self.assertEqual(invalid['event'], 'validation_error')

    def test_polygon_complexity_matches_backend_contract(self):
        self.state.save_map_for_rooms({
            'command': 'save',
            'name': 'wohnung',
            'request_id': 'ios-map-complexity',
        })
        fingerprint = self.state.semantic_map['map_ref']['fingerprint']

        def room(room_id, points):
            return {
                'id': room_id,
                'name': room_id,
                'color': '#4FB3A5',
                'polygon': [
                    {
                        'x': -0.5 + 0.4 * math.cos(2 * math.pi * index / points),
                        'y': -0.2 + 0.4 * math.sin(2 * math.pi * index / points),
                    }
                    for index in range(points)
                ],
                'navigation_goal': {'x': -0.5, 'y': -0.2, 'yaw': 0.0},
            }

        too_complex = self.state.apply_semantic_command({
            'command': 'upsert_room',
            'request_id': 'ios-room-65-points',
            'map_fingerprint': fingerprint,
            'base_revision': 0,
            'room': room('room-65-points', 65),
        })
        self.assertFalse(too_complex['ok'])

        self.state.semantic_map['rooms'] = [
            room(f'room-existing-{index}', 17) for index in range(240)
        ]
        total_too_complex = self.state.apply_semantic_command({
            'command': 'upsert_room',
            'request_id': 'ios-room-total-complexity',
            'map_fingerprint': fingerprint,
            'base_revision': 0,
            'room': room('room-new', 17),
        })
        self.assertFalse(total_too_complex['ok'])
        self.assertIn('4096', total_too_complex['message'])



class MappingModeMockTests(unittest.TestCase):
    """Mapping mode and stop as defined in contracts/api/app-bridge.md."""

    MODE_KEYS = {
        'state',
        'controller_connected',
        'auto_end_timeout_s',
        'auto_end_remaining_s',
        'last_end_reason',
        'enable_block_reason',
    }
    ENVELOPE_KEYS = {
        'schema_version', 'event', 'ok', 'request_id', 'message',
        'mapping_mode', 'time',
    }

    def setUp(self):
        self.state = mock.RobotState()

    def command(self, kind, request_id):
        return self.state.apply_mapping_command({
            'command': kind,
            'request_id': request_id,
        })

    def test_mapping_mode_starts_off_with_complete_status(self):
        status = self.state.mapping_mode_status()
        self.assertEqual(set(status), self.ENVELOPE_KEYS)
        self.assertEqual(set(status['mapping_mode']), self.MODE_KEYS)
        self.assertEqual(status['schema_version'], 1)
        self.assertEqual(status['event'], 'status')
        self.assertTrue(status['ok'])
        self.assertIsNone(status['request_id'])
        mode = status['mapping_mode']
        self.assertEqual(mode['state'], 'off')
        self.assertGreater(mode['auto_end_timeout_s'], 0)
        self.assertIsNone(mode['auto_end_remaining_s'])
        self.assertIsNone(mode['last_end_reason'])
        self.assertIsNone(mode['enable_block_reason'])

    def test_enable_and_disable_report_results_and_end_reason(self):
        enabled = self.command('enable', 'ios-mode-1')
        self.assertTrue(enabled['ok'])
        self.assertEqual(enabled['event'], 'enable_result')
        self.assertEqual(enabled['request_id'], 'ios-mode-1')
        mode = enabled['mapping_mode']
        self.assertEqual(mode['state'], 'active')
        self.assertIsNotNone(mode['auto_end_remaining_s'])
        self.assertLessEqual(mode['auto_end_remaining_s'], mode['auto_end_timeout_s'])
        self.assertGreaterEqual(mode['auto_end_remaining_s'], 0)

        again = self.command('enable', 'ios-mode-2')
        self.assertTrue(again['ok'])
        self.assertEqual(again['mapping_mode']['state'], 'active')

        disabled = self.command('disable', 'ios-mode-3')
        self.assertTrue(disabled['ok'])
        self.assertEqual(disabled['event'], 'disable_result')
        self.assertEqual(disabled['mapping_mode']['state'], 'off')
        self.assertEqual(disabled['mapping_mode']['last_end_reason'], 'app_disable')
        self.assertIsNone(disabled['mapping_mode']['auto_end_remaining_s'])

        already_off = self.command('disable', 'ios-mode-4')
        self.assertTrue(already_off['ok'])
        self.assertEqual(already_off['mapping_mode']['state'], 'off')

    def test_stop_is_accepted_in_every_state_and_is_idempotent(self):
        while_off = self.command('stop', 'ios-stop-1')
        self.assertTrue(while_off['ok'])
        self.assertEqual(while_off['event'], 'stop_result')
        self.assertEqual(while_off['mapping_mode']['state'], 'off')
        self.assertIsNone(while_off['mapping_mode']['last_end_reason'])

        self.command('enable', 'ios-mode-1')
        stopped = self.command('stop', 'ios-stop-2')
        self.assertTrue(stopped['ok'])
        self.assertEqual(stopped['mapping_mode']['state'], 'off')
        self.assertEqual(stopped['mapping_mode']['last_end_reason'], 'app_stop')

        # The app repeats the same stop until it sees "off".
        repeated = self.command('stop', 'ios-stop-2')
        self.assertTrue(repeated['ok'])
        self.assertEqual(repeated['request_id'], 'ios-stop-2')
        self.assertEqual(repeated['mapping_mode']['state'], 'off')
        self.assertEqual(repeated['mapping_mode']['last_end_reason'], 'app_stop')

    def test_stop_is_accepted_even_while_enable_is_blocked(self):
        self.command('enable', 'ios-mode-1')
        self.state.mapping_block_reason = 'fault'
        stopped = self.command('stop', 'ios-stop-1')
        self.assertTrue(stopped['ok'])
        self.assertEqual(stopped['mapping_mode']['state'], 'off')

    def test_enable_is_refused_while_blocked(self):
        self.state.mapping_block_reason = 'not_ready'
        refused = self.command('enable', 'ios-mode-1')
        self.assertFalse(refused['ok'])
        self.assertEqual(refused['event'], 'enable_result')
        self.assertEqual(refused['request_id'], 'ios-mode-1')
        self.assertEqual(refused['mapping_mode']['state'], 'off')
        self.assertEqual(refused['mapping_mode']['enable_block_reason'], 'not_ready')

        self.state.mapping_block_reason = None
        self.assertTrue(self.command('enable', 'ios-mode-2')['ok'])

    def test_invalid_commands_are_refused_without_state_change(self):
        invalid_commands = [
            None,
            'enable',
            {'command': 'drive', 'request_id': 'ios-1'},
            {'command': 'enable'},
            {'command': 'enable', 'request_id': '../unsafe'},
            {'command': 'enable', 'request_id': 'ios-1', 'speed': 1.0},
            {'command': 'enable', 'request_id': 'a' * 65},
        ]
        for command in invalid_commands:
            with self.subTest(command=command):
                response = self.state.apply_mapping_command(command)
                self.assertFalse(response['ok'])
                self.assertEqual(response['mapping_mode']['state'], 'off')
                self.assertEqual(set(response), self.ENVELOPE_KEYS)

    def test_mapping_mode_ends_by_itself_without_controller_input(self):
        self.state.mapping_timeout_s = 20.0
        self.command('enable', 'ios-mode-1')
        self.state.controller_in_use = False

        self.state.mapping_last_input = time.monotonic() - 5.0
        self.assertIsNone(self.state.tick_mapping())
        remaining = self.state.mapping_mode_status()['mapping_mode']['auto_end_remaining_s']
        self.assertGreater(remaining, 14.0)
        self.assertLess(remaining, 15.5)

        self.state.mapping_last_input = time.monotonic() - 21.0
        self.assertEqual(self.state.tick_mapping(), 'ended')
        mode = self.state.mapping_mode_status()['mapping_mode']
        self.assertEqual(mode['state'], 'off')
        self.assertEqual(mode['last_end_reason'], 'inactivity_timeout')
        self.assertIsNone(mode['auto_end_remaining_s'])

    def test_disconnected_controller_does_not_keep_mapping_mode_alive(self):
        self.state.mapping_timeout_s = 20.0
        self.command('enable', 'ios-mode-1')
        self.state.controller_connected = False
        self.state.controller_in_use = True

        status = self.state.mapping_mode_status()
        self.assertEqual(status['mapping_mode']['state'], 'active')
        self.assertFalse(status['mapping_mode']['controller_connected'])

        self.state.mapping_last_input = time.monotonic() - 21.0
        self.assertEqual(self.state.tick_mapping(), 'ended')

    def test_controller_input_keeps_mode_alive_and_grows_the_map(self):
        self.state.mapping_timeout_s = 20.0
        before_run = self.state.map_summary()['fingerprint']
        self.command('enable', 'ios-mode-1')
        start_of_run = self.state.map_summary()['fingerprint']
        self.assertNotEqual(start_of_run, before_run)
        unknown_at_start = self.state.map_snapshot()['data'].count(-1)

        self.state.mapping_last_input = time.monotonic() - 30.0
        self.state.mapping_last_drive_step = time.monotonic() - 30.0
        self.assertEqual(self.state.tick_mapping(), 'map')
        self.assertEqual(self.state.mapping_mode_status()['mapping_mode']['state'], 'active')
        self.assertLess(self.state.map_snapshot()['data'].count(-1), unknown_at_start)
        self.assertNotEqual(self.state.map_summary()['fingerprint'], start_of_run)

    def test_map_stays_available_after_mapping_mode_ends(self):
        self.command('enable', 'ios-mode-1')
        fingerprint = self.state.map_summary()['fingerprint']
        self.command('disable', 'ios-mode-2')
        self.assertIsNone(self.state.tick_mapping())
        self.assertEqual(self.state.map_summary()['fingerprint'], fingerprint)
        self.assertTrue(self.state.map_manager_status()['map']['snapshot_available'])

        saved = self.state.save_map_for_rooms({
            'command': 'save',
            'name': 'wohnung',
            'request_id': 'ios-map-after-run',
        })
        self.assertTrue(saved['ok'])
        self.assertEqual(self.state.last_saved_map['fingerprint'], fingerprint)

    def test_fault_ends_mapping_mode(self):
        self.command('enable', 'ios-mode-1')
        self.assertTrue(self.state.end_mapping('fault'))
        mode = self.state.mapping_mode_status()['mapping_mode']
        self.assertEqual(mode['state'], 'off')
        self.assertEqual(mode['last_end_reason'], 'fault')
        self.assertFalse(self.state.end_mapping('fault'))


class MissionMockTests(unittest.TestCase):
    """Drive to a room and cancel, as defined in contracts/api/app-bridge.md."""

    def setUp(self):
        self.state = mock.RobotState()

    def prepare_room(self, with_goal=True):
        self.state.save_map_for_rooms({'command': 'save', 'name': 'wohnung', 'request_id': 'ios-map-1'})
        room = {
            'id': 'kueche',
            'name': 'Küche',
            'polygon': [{'x': -2.0, 'y': -1.0}, {'x': 0.0, 'y': -1.0}, {'x': 0.0, 'y': 1.0}],
        }
        if with_goal:
            room['navigation_goal'] = {'x': -1.0, 'y': -0.5, 'yaw': 0.0}
        result = self.state.apply_semantic_command({
            'command': 'upsert_room', 'request_id': 'ios-room-1',
            'map_fingerprint': self.state.semantic_map['map_ref']['fingerprint'],
            'base_revision': 0, 'room': room,
        })
        self.assertTrue(result['ok'], result)

    def go(self, request_id='ios-go-1', room_id='kueche'):
        return self.state.apply_mission_command(
            {'command': 'go_to_room', 'room_id': room_id, 'request_id': request_id})

    def test_idle_status_says_why_driving_is_not_possible(self):
        status = self.state.mission_status()
        self.assertEqual(status['mission']['state'], 'idle')
        self.assertEqual(status['start_block_reason'], 'no_map')
        self.assertEqual(set(status), {'schema_version', 'event', 'ok', 'request_id', 'message',
                                       'mission', 'start_block_reason', 'time'})

    def test_drive_to_a_room_runs_and_arrives(self):
        self.prepare_room()
        self.assertIsNone(self.state.mission_start_block_reason())
        started = self.go()
        self.assertTrue(started['ok'])
        self.assertEqual(started['event'], 'go_to_room_result')
        self.assertEqual(started['mission']['state'], 'running')
        self.assertEqual(started['start_block_reason'], 'busy')
        self.state.mission_started_at -= mock.MOCK_MISSION_DURATION_S / 2
        self.state.tick_mission()
        self.assertLess(self.state.mission['distance_remaining_m'], mock.MOCK_MISSION_DISTANCE_M)
        self.state.mission_started_at -= mock.MOCK_MISSION_DURATION_S
        self.state.tick_mission()
        self.assertEqual(self.state.mission_status()['mission']['state'], 'succeeded')

    def test_cancel_is_always_accepted_and_idempotent(self):
        self.prepare_room()
        self.go()
        for request_id in ('ios-cancel-1', 'ios-cancel-2'):
            result = self.state.apply_mission_command({'command': 'cancel', 'request_id': request_id})
            self.assertTrue(result['ok'])
            self.assertEqual(result['mission']['state'], 'canceled')
            self.assertEqual(result['mission']['result'], 'app_cancel')

    def test_refused_while_mapping_or_blocked_or_without_goal(self):
        self.prepare_room(with_goal=False)
        refused = self.go()
        self.assertFalse(refused['ok'])
        self.assertEqual(refused['start_block_reason'], 'room_invalid')

        self.state.mission_block_override = 'not_localized'
        refused = self.go('ios-go-2')
        self.assertFalse(refused['ok'])
        self.assertEqual(refused['start_block_reason'], 'not_localized')

        self.state.mission_block_override = None
        self.state.apply_mapping_command({'command': 'enable', 'request_id': 'ios-mode-1'})
        refused = self.go('ios-go-3')
        self.assertEqual(refused['start_block_reason'], 'mapping_active')

    def test_starting_mapping_cancels_a_running_mission(self):
        self.prepare_room()
        self.go()
        self.state.apply_mapping_command({'command': 'enable', 'request_id': 'ios-mode-1'})
        self.state.tick_mission()
        self.assertEqual(self.state.mission['state'], 'canceled')
        self.assertEqual(self.state.mission['result'], 'mapping_started')

    def test_invalid_mission_commands_are_refused(self):
        for command in (None, {'command': 'explore', 'request_id': 'ios-1'},
                        {'command': 'cancel', 'request_id': 'bad id'},
                        {'command': 'go_to_room', 'request_id': 'ios-1', 'room_id': 'k', 'speed': 2}):
            result = self.state.apply_mission_command(command)
            self.assertFalse(result['ok'])
        self.assertIsNone(self.state.mission)


class WebSocketClient:
    """Minimal RFC 6455 text client, enough to drive the mock in a test."""

    def __init__(self, port):
        self.sock = socket.create_connection(('127.0.0.1', port), timeout=5)
        key = base64.b64encode(os.urandom(16)).decode('ascii')
        self.sock.sendall((
            'GET / HTTP/1.1\r\n'
            f'Host: 127.0.0.1:{port}\r\n'
            'Upgrade: websocket\r\n'
            'Connection: Upgrade\r\n'
            f'Sec-WebSocket-Key: {key}\r\n'
            'Sec-WebSocket-Version: 13\r\n\r\n'
        ).encode('ascii'))
        response = b''
        while b'\r\n\r\n' not in response:
            response += self.sock.recv(1024)
        if b' 101 ' not in response.split(b'\r\n', 1)[0]:
            raise AssertionError(f'unexpected handshake: {response!r}')

    def send(self, payload):
        data = json.dumps(payload).encode('utf-8')
        mask = os.urandom(4)
        header = bytearray([0x81])
        if len(data) < 126:
            header.append(0x80 | len(data))
        else:
            header.append(0x80 | 126)
            header += struct.pack('!H', len(data))
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
        self.sock.sendall(bytes(header) + mask + masked)

    def _read_exact(self, size):
        data = b''
        while len(data) < size:
            chunk = self.sock.recv(size - len(data))
            if not chunk:
                raise AssertionError('socket closed')
            data += chunk
        return data

    def receive(self):
        first, second = self._read_exact(2)
        length = second & 0x7F
        if length == 126:
            length = struct.unpack('!H', self._read_exact(2))[0]
        elif length == 127:
            length = struct.unpack('!Q', self._read_exact(8))[0]
        payload = self._read_exact(length)
        if first & 0x0F != 0x1:
            return None
        return json.loads(payload.decode('utf-8'))

    def receive_status(self, topic, predicate, timeout=5.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            frame = self.receive()
            if frame is None or frame.get('topic') != topic:
                continue
            status = json.loads(frame['msg']['data'])
            if predicate(status):
                return status
        raise AssertionError('expected status not received')

    def close(self):
        self.sock.close()


class MappingModeWireTests(unittest.TestCase):
    """The same contract over a real WebSocket connection to the mock."""

    def setUp(self):
        mock.STATE.reset()
        self.server = mock.WebSocketServer(('127.0.0.1', 0), mock.WebSocketHandler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = WebSocketClient(self.port)

    def tearDown(self):
        self.client.close()
        mock.STATE.close_clients()
        self.server.shutdown()
        self.server.server_close()
        mock.STATE.reset()

    def publish_command(self, kind, request_id):
        self.client.send({
            'op': 'publish',
            'topic': mock.MAPPING_MODE_COMMAND_TOPIC,
            'msg': {'data': json.dumps({'command': kind, 'request_id': request_id})},
        })

    def test_app_flow_enable_stop_over_websocket(self):
        topic = mock.MAPPING_MODE_STATUS_TOPIC
        self.client.send({
            'op': 'advertise',
            'topic': mock.MAPPING_MODE_COMMAND_TOPIC,
            'type': 'std_msgs/String',
        })
        self.client.send({'op': 'subscribe', 'topic': topic, 'type': 'std_msgs/String'})

        latched = self.client.receive_status(topic, lambda status: True)
        self.assertEqual(latched['mapping_mode']['state'], 'off')

        self.publish_command('enable', 'ios-mode-1')
        enabled = self.client.receive_status(
            topic, lambda status: status['request_id'] == 'ios-mode-1')
        self.assertTrue(enabled['ok'])
        self.assertEqual(enabled['event'], 'enable_result')
        self.assertEqual(enabled['mapping_mode']['state'], 'active')

        self.publish_command('stop', 'ios-stop-1')
        stopped = self.client.receive_status(
            topic, lambda status: status['request_id'] == 'ios-stop-1')
        self.assertTrue(stopped['ok'])
        self.assertEqual(stopped['event'], 'stop_result')
        self.assertEqual(stopped['mapping_mode']['state'], 'off')
        self.assertEqual(stopped['mapping_mode']['last_end_reason'], 'app_stop')

    def test_malformed_command_is_refused_over_websocket(self):
        topic = mock.MAPPING_MODE_STATUS_TOPIC
        self.client.send({'op': 'subscribe', 'topic': topic, 'type': 'std_msgs/String'})
        self.client.receive_status(topic, lambda status: True)

        self.client.send({
            'op': 'publish',
            'topic': mock.MAPPING_MODE_COMMAND_TOPIC,
            'msg': {'data': '{kaputt'},
        })
        refused = self.client.receive_status(topic, lambda status: not status['ok'])
        self.assertEqual(refused['mapping_mode']['state'], 'off')


if __name__ == '__main__':
    unittest.main()
