import Foundation
import Testing
@testable import HomeMy

struct MissionProtocolTests {
    private func jsonObject(_ text: String) throws -> [String: Any] {
        let object = try JSONSerialization.jsonObject(with: Data(text.utf8))
        return try #require(object as? [String: Any])
    }

    private func innerCommand(_ frame: String) throws -> [String: Any] {
        let outer = try jsonObject(frame)
        let msg = try #require(outer["msg"] as? [String: Any])
        let data = try #require(msg["data"] as? String)
        return try jsonObject(data)
    }

    private func statusFrame(_ payload: [String: Any]) throws -> String {
        let inner = String(data: try JSONSerialization.data(withJSONObject: payload), encoding: .utf8)!
        let outer: [String: Any] = [
            "op": "publish",
            "topic": "/homemy/mission/status_json",
            "msg": ["data": inner]
        ]
        return String(data: try JSONSerialization.data(withJSONObject: outer), encoding: .utf8)!
    }

    private func payload(
        state: String = "running",
        event: String = "status",
        ok: Bool = true,
        requestID: Any = NSNull(),
        blockReason: Any = NSNull(),
        attempt: Int = 1,
        maxAttempts: Int = 3,
        distance: Any = 2.5
    ) -> [String: Any] {
        let idle = state == "idle"
        return [
            "schema_version": 1,
            "event": event,
            "ok": ok,
            "request_id": requestID,
            "message": "Auftrag läuft.",
            "mission": [
                "state": state,
                "command": idle ? NSNull() : "go_to_room",
                "room_id": idle ? NSNull() : "kueche",
                "room_name": idle ? NSNull() : "Küche",
                "phase": idle ? NSNull() : "driving",
                "attempt": idle ? 0 : attempt,
                "max_attempts": idle ? 0 : maxAttempts,
                "distance_remaining_m": idle ? NSNull() : distance,
                "result": NSNull()
            ] as [String: Any],
            "start_block_reason": blockReason,
            "time": 1_731_790_000.0
        ]
    }

    private func decode(_ payload: [String: Any]) throws -> MissionStatus {
        guard case let .missionStatus(status) = try RosbridgeProtocol.decodeEvent(from: statusFrame(payload)) else {
            Issue.record("kein Auftragsstatus")
            throw RosbridgeProtocolError.invalidMissionStatus
        }
        return status
    }

    // MARK: - Befehle

    @Test
    func goToRoomFrameCarriesRoomAndRequest() throws {
        let frame = try RosbridgeProtocol.missionCommandFrame(.goToRoom(roomID: "kueche"), requestID: "ios-go-1")
        let outer = try jsonObject(frame)
        #expect(outer["op"] as? String == "publish")
        #expect(outer["topic"] as? String == "/homemy/mission/command_json")
        let inner = try innerCommand(frame)
        #expect(inner["command"] as? String == "go_to_room")
        #expect(inner["room_id"] as? String == "kueche")
        #expect(inner["request_id"] as? String == "ios-go-1")
        #expect(inner.count == 3)
    }

    @Test
    func cancelFrameHasNoRoom() throws {
        let inner = try innerCommand(
            RosbridgeProtocol.missionCommandFrame(.cancel, requestID: "ios-cancel-1")
        )
        #expect(inner["command"] as? String == "cancel")
        #expect(inner["room_id"] == nil)
        #expect(inner.count == 2)
    }

    @Test(arguments: ["", " kueche", String(repeating: "x", count: 129)])
    func invalidRoomIDsAreRefused(roomID: String) {
        #expect(throws: RosbridgeProtocolError.invalidCommand) {
            try RosbridgeProtocol.missionCommandFrame(.goToRoom(roomID: roomID), requestID: "ios-go-1")
        }
    }

    @Test
    func invalidRequestIDIsRefused() {
        #expect(throws: RosbridgeProtocolError.invalidCommand) {
            try RosbridgeProtocol.missionCommandFrame(.cancel, requestID: "bad id")
        }
    }

    // MARK: - Status

    @Test
    func runningAndIdleStatusesDecode() throws {
        let running = try decode(payload())
        #expect(running.mission.state == .running)
        #expect(running.mission.roomName == "Küche")
        #expect(running.mission.distanceRemainingMeters == 2.5)

        let idle = try decode(payload(state: "idle", blockReason: "not_localized"))
        #expect(idle.mission.state == .idle)
        #expect(idle.startBlockReason == "not_localized")
    }

    @Test
    func implausibleStatusesAreRejected() throws {
        var unknownState = payload()
        var mission = unknownState["mission"] as! [String: Any]
        mission["state"] = "flying"
        unknownState["mission"] = mission
        for bad in [
            unknownState,
            payload(event: "explore_result"),
            payload(attempt: 4, maxAttempts: 3),
            payload(distance: -1.0),
            payload(blockReason: "")
        ] {
            #expect(throws: RosbridgeProtocolError.invalidMissionStatus) {
                _ = try RosbridgeProtocol.decodeEvent(from: statusFrame(bad))
            }
        }
    }

    // MARK: - Bedienregeln

    @Test
    func goToRoomNeedsAFreshIdleStatusWithoutBlockReason() throws {
        let idle = try decode(payload(state: "idle"))
        let blocked = try decode(payload(state: "idle", blockReason: "not_localized"))
        let running = try decode(payload())
        func can(_ status: MissionStatus?, fresh: Bool = true, goal: Bool = true, pending: Bool = false,
                 connected: Bool = true) -> Bool {
            MissionPolicy.canGoToRoom(connected: connected, statusIsFresh: fresh, status: status,
                                      roomHasGoal: goal, commandPending: pending)
        }
        #expect(can(idle))
        #expect(!can(idle, fresh: false))
        #expect(!can(idle, goal: false))
        #expect(!can(idle, pending: true))
        #expect(!can(idle, connected: false))
        #expect(!can(nil))
        #expect(!can(blocked))
        #expect(!can(running))
    }

    @Test
    func cancelIsOfferedWhileRunningOrUnknown() throws {
        let running = try decode(payload()).mission
        let idle = try decode(payload(state: "idle")).mission
        #expect(MissionPolicy.cancelIsOffered(connected: true, statusIsFresh: true, everReceived: true, snapshot: running))
        #expect(!MissionPolicy.cancelIsOffered(connected: true, statusIsFresh: true, everReceived: true, snapshot: idle))
        #expect(MissionPolicy.cancelIsOffered(connected: true, statusIsFresh: false, everReceived: true, snapshot: idle))
        // A robot without missions never reported one: no cancel button.
        #expect(!MissionPolicy.cancelIsOffered(connected: true, statusIsFresh: false, everReceived: false, snapshot: nil))
        #expect(!MissionPolicy.cancelIsOffered(connected: false, statusIsFresh: true, everReceived: true, snapshot: running))
    }

    @Test
    func pendingCommandsResolve() throws {
        let go = PendingMissionCommand(kind: .goToRoom(roomID: "kueche"), requestID: "ios-go-1", sentAt: Date())
        let accepted = try decode(payload(event: "go_to_room_result", requestID: "ios-go-1"))
        let refused = try decode(payload(state: "idle", event: "go_to_room_result", ok: false,
                                         requestID: "ios-go-1", blockReason: "not_localized"))
        #expect(MissionPolicy.resolution(of: go, with: accepted) == .confirmed)
        #expect(MissionPolicy.resolution(of: go, with: refused) == .refused("Auftrag läuft."))
        #expect(MissionPolicy.resolution(of: go, with: try decode(payload())) == .stillPending)

        let cancel = PendingMissionCommand(kind: .cancel, requestID: "ios-cancel-1", sentAt: Date())
        #expect(MissionPolicy.resolution(of: cancel, with: try decode(payload(state: "idle"))) == .confirmed)
        #expect(MissionPolicy.resolution(of: cancel, with: try decode(payload())) == .stillPending)
    }

    @Test
    func textsExplainEveryBlockReason() {
        for reason in ["busy", "mapping_active", "not_ready", "no_map", "rooms_not_bound",
                       "not_localized", "navigation_unavailable", "room_invalid"] {
            let text = MissionText.blockReason(reason)
            #expect(text != nil)
            #expect(!(text ?? "").contains(reason))
        }
        #expect(MissionText.blockReason(nil) == nil)
    }
}
