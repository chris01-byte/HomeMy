import Foundation
import Testing
@testable import HomeMy

struct RosbridgeProtocolTests {
    // MARK: - Rahmen der Steuerverbindung

    @Test
    func setupFramesAdvertiseCommandAndSubscribeStatus() throws {
        let frames = try RosbridgeProtocol.setupFrames().map(jsonObject)
        #expect(frames.count == 2)

        #expect(frames[0]["op"] as? String == "advertise")
        #expect(frames[0]["topic"] as? String == "/homemy/mapping_mode/command_json")
        #expect(frames[0]["type"] as? String == "std_msgs/String")

        #expect(frames[1]["op"] as? String == "subscribe")
        #expect(frames[1]["topic"] as? String == "/homemy/mapping_mode/status_json")
        #expect(frames[1]["type"] as? String == "std_msgs/String")
    }

    @Test
    func setupFramesNeverTouchAVelocityTopic() throws {
        for frame in try RosbridgeProtocol.setupFrames() {
            #expect(!frame.contains("cmd_vel"))
        }
    }

    @Test(arguments: [
        MappingModeCommandKind.enable,
        MappingModeCommandKind.disable,
        MappingModeCommandKind.stop
    ])
    func commandIsJSONEncodedInsideStdMsgsString(kind: MappingModeCommandKind) throws {
        let frame = try jsonObject(
            RosbridgeProtocol.mappingModeCommandFrame(kind, requestID: "ios-mode-1")
        )
        #expect(frame["op"] as? String == "publish")
        #expect(frame["topic"] as? String == "/homemy/mapping_mode/command_json")

        let message = try #require(frame["msg"] as? [String: Any])
        let inner = try jsonObject(try #require(message["data"] as? String))
        #expect(inner["command"] as? String == kind.rawValue)
        #expect(inner["request_id"] as? String == "ios-mode-1")
        #expect(inner.count == 2)
    }

    @Test(arguments: [
        "",
        "-leading-dash",
        "has space",
        "umlaut-ä",
        "slash/inside",
        String(repeating: "a", count: 65)
    ])
    func rejectsCommandWithInvalidRequestID(requestID: String) {
        #expect(throws: RosbridgeProtocolError.invalidCommand) {
            _ = try RosbridgeProtocol.mappingModeCommandFrame(.stop, requestID: requestID)
        }
    }

    @Test
    func acceptsRequestIDAtLengthLimit() throws {
        let requestID = String(repeating: "a", count: 64)
        _ = try RosbridgeProtocol.mappingModeCommandFrame(.enable, requestID: requestID)
    }

    // MARK: - Status dekodieren

    @Test
    func decodesOffStatus() throws {
        let event = try RosbridgeProtocol.decodeEvent(from: statusFrame())
        guard case let .mappingModeStatus(status) = event else {
            Issue.record("Statusereignis erwartet")
            return
        }
        #expect(status.event == "status")
        #expect(status.ok)
        #expect(status.requestID == nil)
        #expect(status.mappingMode.state == .off)
        #expect(!status.mappingMode.controllerConnected)
        #expect(status.mappingMode.autoEndTimeoutSeconds == 300)
        #expect(status.mappingMode.autoEndRemainingSeconds == nil)
        #expect(status.mappingMode.lastEndReason == nil)
        #expect(status.mappingMode.enableBlockReason == nil)
    }

    @Test
    func decodesActiveResultWithRemainingTime() throws {
        let event = try RosbridgeProtocol.decodeEvent(from: statusFrame(
            event: "enable_result",
            requestID: "ios-mode-7",
            state: "active",
            controllerConnected: true,
            remaining: 212.5
        ))
        guard case let .mappingModeStatus(status) = event else {
            Issue.record("Statusereignis erwartet")
            return
        }
        #expect(status.event == "enable_result")
        #expect(status.requestID == "ios-mode-7")
        #expect(status.mappingMode.state == .active)
        #expect(status.mappingMode.controllerConnected)
        #expect(status.mappingMode.autoEndRemainingSeconds == 212.5)
    }

    @Test
    func decodesRefusalWithBlockReason() throws {
        let event = try RosbridgeProtocol.decodeEvent(from: statusFrame(
            event: "enable_result",
            ok: false,
            requestID: "ios-mode-8",
            blockReason: "not_ready"
        ))
        guard case let .mappingModeStatus(status) = event else {
            Issue.record("Statusereignis erwartet")
            return
        }
        #expect(!status.ok)
        #expect(status.mappingMode.state == .off)
        #expect(status.mappingMode.enableBlockReason == "not_ready")
    }

    @Test
    func rejectsUnknownState() {
        expectInvalidStatus(statusFrame(state: "paused"))
    }

    @Test
    func rejectsUnknownEvent() {
        expectInvalidStatus(statusFrame(event: "drive_result"))
    }

    @Test
    func rejectsWrongSchemaVersion() {
        expectInvalidStatus(statusFrame(schemaVersion: 2))
    }

    @Test
    func rejectsEmptyMessage() {
        expectInvalidStatus(statusFrame(message: ""))
    }

    @Test(arguments: [0.0, -5.0])
    func rejectsNonPositiveAutoEndTimeout(timeout: Double) {
        expectInvalidStatus(statusFrame(timeout: timeout))
    }

    @Test
    func rejectsRemainingTimeWhileOff() {
        expectInvalidStatus(statusFrame(state: "off", remaining: 10))
    }

    @Test
    func rejectsRemainingTimeAboveTimeout() {
        expectInvalidStatus(statusFrame(state: "active", timeout: 300, remaining: 301))
    }

    @Test
    func rejectsNegativeRemainingTime() {
        expectInvalidStatus(statusFrame(state: "active", remaining: -1))
    }

    @Test(arguments: [
        "state",
        "controller_connected",
        "auto_end_timeout_s"
    ])
    func rejectsStatusWithoutRequiredModeField(field: String) throws {
        var mode = modePayload()
        mode.removeValue(forKey: field)
        expectInvalidStatus(try publishFrame(inner: statusPayload(mode: mode)))
    }

    @Test(arguments: ["schema_version", "event", "ok", "message", "mapping_mode", "time"])
    func rejectsStatusWithoutRequiredEnvelopeField(field: String) throws {
        var payload = statusPayload(mode: modePayload())
        payload.removeValue(forKey: field)
        expectInvalidStatus(try publishFrame(inner: payload))
    }

    @Test
    func rejectsStatusThatIsNotJSON() throws {
        let frame = try encode([
            "op": "publish",
            "topic": RosbridgeTopics.mappingModeStatus,
            "msg": ["data": "kein json"]
        ])
        expectInvalidStatus(frame)
    }

    @Test
    func rejectsStatusWhoseDataIsNotAString() throws {
        let frame = try encode([
            "op": "publish",
            "topic": RosbridgeTopics.mappingModeStatus,
            "msg": ["data": true]
        ])
        expectInvalidStatus(frame)
    }

    @Test
    func rejectsFrameThatIsNotJSON() {
        #expect(throws: RosbridgeProtocolError.invalidTextFrame) {
            _ = try RosbridgeProtocol.decodeEvent(from: "{")
        }
    }

    @Test
    func ignoresUnrelatedPublishAndOtherOperations() throws {
        let mapFrame = try encode([
            "op": "publish",
            "topic": "/map",
            "msg": ["info": ["width": 1], "data": [0]]
        ])
        #expect(try RosbridgeProtocol.decodeEvent(from: mapFrame) == nil)

        let boolFrame = try encode([
            "op": "publish",
            "topic": "/some/other/topic",
            "msg": ["data": true]
        ])
        #expect(try RosbridgeProtocol.decodeEvent(from: boolFrame) == nil)

        let serviceFrame = try encode(["op": "service_response", "result": true])
        #expect(try RosbridgeProtocol.decodeEvent(from: serviceFrame) == nil)
    }

    // MARK: - Bedienregeln

    @Test
    func enableNeedsFreshUnblockedOffState() {
        let off = snapshot(state: .off)
        #expect(canEnable(snapshot: off))
        #expect(!canEnable(connected: false, snapshot: off))
        #expect(!canEnable(fresh: false, snapshot: off))
        #expect(!canEnable(snapshot: nil))
        #expect(!canEnable(snapshot: snapshot(state: .active, remaining: 100)))
        #expect(!canEnable(snapshot: snapshot(state: .off, blockReason: "fault")))
        #expect(!canEnable(snapshot: off, commandPending: true))
        #expect(!canEnable(snapshot: off, stopPending: true))
    }

    @Test
    func disableNeedsFreshActiveState() {
        let active = snapshot(state: .active, remaining: 100)
        #expect(canDisable(snapshot: active))
        #expect(!canDisable(connected: false, snapshot: active))
        #expect(!canDisable(fresh: false, snapshot: active))
        #expect(!canDisable(snapshot: snapshot(state: .off)))
        #expect(!canDisable(snapshot: active, commandPending: true))
        #expect(!canDisable(snapshot: active, stopPending: true))
    }

    @Test
    func stopIsOfferedWheneverModeIsActiveOrUnknown() {
        let active = snapshot(state: .active, remaining: 100)
        let off = snapshot(state: .off)

        #expect(stopOffered(snapshot: active))
        // Unbekannter Zustand: kein Status, veralteter Status, ungültiger Status.
        #expect(stopOffered(snapshot: nil))
        #expect(stopOffered(fresh: false, snapshot: off))
        #expect(stopOffered(fresh: false, snapshot: active))
        #expect(stopOffered(snapshot: snapshot(state: .off, timeout: 0)))

        // Nur ein frisch bestätigtes „aus“ blendet den Stopp aus.
        #expect(!stopOffered(snapshot: off))
        // Ohne Verbindung kann die App nichts senden.
        #expect(!stopOffered(connected: false, snapshot: active))
    }

    @Test
    func mapSaveNeedsFreshConfirmedOff() {
        let off = snapshot(state: .off)
        #expect(MappingModePolicy.mapSaveIsAllowed(
            connected: true, statusIsFresh: true, snapshot: off
        ))
        #expect(!MappingModePolicy.mapSaveIsAllowed(
            connected: false, statusIsFresh: true, snapshot: off
        ))
        #expect(!MappingModePolicy.mapSaveIsAllowed(
            connected: true, statusIsFresh: false, snapshot: off
        ))
        #expect(!MappingModePolicy.mapSaveIsAllowed(
            connected: true, statusIsFresh: true, snapshot: nil
        ))
        #expect(!MappingModePolicy.mapSaveIsAllowed(
            connected: true,
            statusIsFresh: true,
            snapshot: snapshot(state: .active, remaining: 10)
        ))
    }

    @Test
    func pendingCommandIsResolvedByMatchingResult() {
        let pending = PendingMappingCommand(
            kind: .enable, requestID: "ios-mode-1", sentAt: Date()
        )
        #expect(MappingModePolicy.resolution(
            of: pending,
            with: status(requestID: "ios-mode-1", ok: true, state: .active)
        ) == .confirmed)
        #expect(MappingModePolicy.resolution(
            of: pending,
            with: status(requestID: "ios-mode-1", ok: false, state: .off, message: "nicht bereit")
        ) == .refused("nicht bereit"))
    }

    @Test
    func pendingCommandIsResolvedByReachedStateWithoutResult() {
        let enable = PendingMappingCommand(kind: .enable, requestID: "a", sentAt: Date())
        let disable = PendingMappingCommand(kind: .disable, requestID: "b", sentAt: Date())
        let stop = PendingMappingCommand(kind: .stop, requestID: "c", sentAt: Date())

        #expect(MappingModePolicy.resolution(
            of: enable, with: status(state: .active)
        ) == .confirmed)
        #expect(MappingModePolicy.resolution(
            of: enable, with: status(state: .off)
        ) == .stillPending)
        #expect(MappingModePolicy.resolution(
            of: disable, with: status(state: .off)
        ) == .confirmed)
        #expect(MappingModePolicy.resolution(
            of: disable, with: status(state: .active)
        ) == .stillPending)
        #expect(MappingModePolicy.resolution(
            of: stop, with: status(state: .off)
        ) == .confirmed)
        #expect(MappingModePolicy.resolution(
            of: stop, with: status(state: .active)
        ) == .stillPending)
    }

    @Test
    func foreignResultDoesNotResolvePendingCommand() {
        let enable = PendingMappingCommand(kind: .enable, requestID: "mine", sentAt: Date())
        #expect(MappingModePolicy.resolution(
            of: enable,
            with: status(requestID: "other", ok: false, state: .off)
        ) == .stillPending)
    }

    // MARK: - Anzeigetexte

    @Test
    func knownReasonsHaveGermanTexts() {
        for reason in ["app_disable", "app_stop", "inactivity_timeout", "fault", "shutdown"] {
            let text = MappingModeText.endReason(reason)
            #expect(text != nil)
            #expect(text?.contains(reason) == false)
        }
        for reason in ["not_ready", "fault", "shutting_down"] {
            let text = MappingModeText.blockReason(reason)
            #expect(text != nil)
            #expect(text?.contains(reason) == false)
        }
        #expect(MappingModeText.endReason(nil) == nil)
        #expect(MappingModeText.blockReason(nil) == nil)
    }

    @Test
    func unknownReasonsStayVisible() {
        #expect(MappingModeText.endReason("new_reason")?.contains("new_reason") == true)
        #expect(MappingModeText.blockReason("new_block")?.contains("new_block") == true)
    }

    @Test
    func remainingTimeIsShownAsMinutesAndSeconds() {
        #expect(MappingModeText.remaining(272.9) == "4:32 min")
        #expect(MappingModeText.remaining(59) == "0:59 min")
        #expect(MappingModeText.remaining(0) == "0:00 min")
        #expect(MappingModeText.remaining(-3) == "0:00 min")
        #expect(MappingModeText.timeout(300) == "5 min")
        #expect(MappingModeText.timeout(90) == "90 s")
    }

    // MARK: - Hilfen

    private func canEnable(
        connected: Bool = true,
        fresh: Bool = true,
        snapshot: MappingModeSnapshot?,
        commandPending: Bool = false,
        stopPending: Bool = false
    ) -> Bool {
        MappingModePolicy.canEnable(
            connected: connected,
            statusIsFresh: fresh,
            snapshot: snapshot,
            commandPending: commandPending,
            stopPending: stopPending
        )
    }

    private func canDisable(
        connected: Bool = true,
        fresh: Bool = true,
        snapshot: MappingModeSnapshot?,
        commandPending: Bool = false,
        stopPending: Bool = false
    ) -> Bool {
        MappingModePolicy.canDisable(
            connected: connected,
            statusIsFresh: fresh,
            snapshot: snapshot,
            commandPending: commandPending,
            stopPending: stopPending
        )
    }

    private func stopOffered(
        connected: Bool = true,
        fresh: Bool = true,
        snapshot: MappingModeSnapshot?
    ) -> Bool {
        MappingModePolicy.stopIsOffered(
            connected: connected,
            statusIsFresh: fresh,
            snapshot: snapshot
        )
    }

    private func snapshot(
        state: MappingModeState,
        timeout: Double = 300,
        remaining: Double? = nil,
        blockReason: String? = nil
    ) -> MappingModeSnapshot {
        MappingModeSnapshot(
            state: state,
            controllerConnected: true,
            autoEndTimeoutSeconds: timeout,
            autoEndRemainingSeconds: remaining,
            lastEndReason: nil,
            enableBlockReason: blockReason
        )
    }

    private func status(
        requestID: String? = nil,
        ok: Bool = true,
        state: MappingModeState,
        message: String = "ok"
    ) -> MappingModeStatus {
        MappingModeStatus(
            schemaVersion: 1,
            event: "status",
            ok: ok,
            requestID: requestID,
            message: message,
            mappingMode: snapshot(state: state, remaining: state == .active ? 100 : nil),
            time: 1
        )
    }

    private func modePayload(
        state: String = "off",
        controllerConnected: Bool = false,
        timeout: Double = 300,
        remaining: Double? = nil,
        blockReason: String? = nil
    ) -> [String: Any] {
        [
            "state": state,
            "controller_connected": controllerConnected,
            "auto_end_timeout_s": timeout,
            "auto_end_remaining_s": remaining as Any? ?? NSNull(),
            "last_end_reason": NSNull(),
            "enable_block_reason": blockReason as Any? ?? NSNull()
        ]
    }

    private func statusPayload(
        schemaVersion: Int = 1,
        event: String = "status",
        ok: Bool = true,
        requestID: String? = nil,
        message: String = "Mapping mode is off.",
        mode: [String: Any]
    ) -> [String: Any] {
        [
            "schema_version": schemaVersion,
            "event": event,
            "ok": ok,
            "request_id": requestID as Any? ?? NSNull(),
            "message": message,
            "mapping_mode": mode,
            "time": 1_731_790_000.0
        ]
    }

    private func statusFrame(
        schemaVersion: Int = 1,
        event: String = "status",
        ok: Bool = true,
        requestID: String? = nil,
        message: String = "Mapping mode is off.",
        state: String = "off",
        controllerConnected: Bool = false,
        timeout: Double = 300,
        remaining: Double? = nil,
        blockReason: String? = nil
    ) -> String {
        let payload = statusPayload(
            schemaVersion: schemaVersion,
            event: event,
            ok: ok,
            requestID: requestID,
            message: message,
            mode: modePayload(
                state: state,
                controllerConnected: controllerConnected,
                timeout: timeout,
                remaining: remaining,
                blockReason: blockReason
            )
        )
        // Die Testdaten sind statisch gültig; ein Fehler hier wäre ein Testfehler.
        return (try? publishFrame(inner: payload)) ?? ""
    }

    private func publishFrame(inner: [String: Any]) throws -> String {
        try encode([
            "op": "publish",
            "topic": RosbridgeTopics.mappingModeStatus,
            "msg": ["data": try encode(inner)]
        ])
    }

    private func expectInvalidStatus(_ frame: String) {
        #expect(throws: RosbridgeProtocolError.invalidMappingModeStatus) {
            _ = try RosbridgeProtocol.decodeEvent(from: frame)
        }
    }

    private func encode(_ object: [String: Any]) throws -> String {
        let data = try JSONSerialization.data(withJSONObject: object, options: [.sortedKeys])
        return try #require(String(data: data, encoding: .utf8))
    }

    private func jsonObject(_ text: String) throws -> [String: Any] {
        let data = try #require(text.data(using: .utf8))
        return try #require(
            try JSONSerialization.jsonObject(with: data) as? [String: Any]
        )
    }
}
