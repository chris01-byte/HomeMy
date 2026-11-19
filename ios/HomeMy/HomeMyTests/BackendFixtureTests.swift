import Foundation
import Testing
@testable import HomeMy

/// Frames recorded from the real ROS 2 backend (`homemy_bringup`, simulation
/// profiles) by `src/homemy_bringup/test/test_app_bridge_e2e.py` and, for
/// missions, `test_drive_sim_e2e.py`, with `HOMEMY_RECORD_FIXTURES`. They
/// prove that the app decodes and accepts what the robot side actually sends.
/// All data is synthetic.
struct BackendFixtureTests {
    private static let directory = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent()
        .appendingPathComponent("Fixtures/backend", isDirectory: true)

    private func frame(_ name: String) throws -> String {
        let url = Self.directory.appendingPathComponent("\(name).json")
        return try String(contentsOf: url, encoding: .utf8)
    }

    private func modeStatus(_ name: String) throws -> MappingModeStatus {
        let event = try RosbridgeProtocol.decodeEvent(from: try frame(name))
        guard case let .mappingModeStatus(status) = event else {
            Issue.record("\(name) is not a mapping-mode status")
            throw RosbridgeProtocolError.invalidMappingModeStatus
        }
        return status
    }

    // MARK: - Mapping mode

    @Test
    func readyStatusAllowsEnable() throws {
        let status = try modeStatus("mode_status_ready")
        #expect(status.mappingMode.state == .off)
        #expect(status.mappingMode.controllerConnected)
        #expect(MappingModePolicy.canEnable(
            connected: true,
            statusIsFresh: true,
            snapshot: status.mappingMode,
            commandPending: false,
            stopPending: false
        ))
        #expect(!MappingModePolicy.stopIsOffered(
            connected: true, statusIsFresh: true, snapshot: status.mappingMode
        ))
    }

    @Test
    func enableResultConfirmsThePendingCommand() throws {
        let status = try modeStatus("mode_enable_result")
        #expect(status.event == "enable_result")
        #expect(status.mappingMode.state == .active)
        #expect(status.mappingMode.autoEndRemainingSeconds != nil)
        let pending = PendingMappingCommand(
            kind: .enable, requestID: try #require(status.requestID), sentAt: Date()
        )
        #expect(MappingModePolicy.resolution(of: pending, with: status) == .confirmed)
        #expect(MappingModePolicy.canDisable(
            connected: true,
            statusIsFresh: true,
            snapshot: status.mappingMode,
            commandPending: false,
            stopPending: false
        ))
        #expect(MappingModePolicy.stopIsOffered(
            connected: true, statusIsFresh: true, snapshot: status.mappingMode
        ))
        #expect(!MappingModePolicy.mapSaveIsAllowed(
            connected: true, statusIsFresh: true, snapshot: status.mappingMode
        ))
    }

    @Test
    func stopResultConfirmsTheStopAndAllowsSaving() throws {
        let status = try modeStatus("mode_stop_result")
        #expect(status.event == "stop_result")
        #expect(status.mappingMode.state == .off)
        #expect(status.mappingMode.lastEndReason == "app_stop")
        let stop = PendingMappingCommand(
            kind: .stop, requestID: try #require(status.requestID), sentAt: Date()
        )
        #expect(MappingModePolicy.resolution(of: stop, with: status) == .confirmed)
        #expect(MappingModePolicy.mapSaveIsAllowed(
            connected: true, statusIsFresh: true, snapshot: status.mappingMode
        ))
    }

    @Test
    func automaticEndIsReportedWithAGermanReason() throws {
        let status = try modeStatus("mode_status_inactivity_ended")
        #expect(status.mappingMode.state == .off)
        #expect(status.mappingMode.lastEndReason == "inactivity_timeout")
        let text = try #require(MappingModeText.endReason(status.mappingMode.lastEndReason))
        #expect(!text.contains("inactivity_timeout"))
    }

    @Test
    func refusedEnableShowsTheBlockReason() throws {
        let status = try modeStatus("mode_enable_refused")
        #expect(!status.ok)
        #expect(status.mappingMode.enableBlockReason == "fault")
        let pending = PendingMappingCommand(
            kind: .enable, requestID: try #require(status.requestID), sentAt: Date()
        )
        #expect(MappingModePolicy.resolution(of: pending, with: status) == .refused(status.message))
        #expect(!MappingModePolicy.canEnable(
            connected: true,
            statusIsFresh: true,
            snapshot: status.mappingMode,
            commandPending: false,
            stopPending: false
        ))
    }

    // MARK: - Map, map store, rooms

    @Test
    func savedMapMatchesTheMapStoreAndUnlocksRoomEditing() throws {
        let map = try #require(try MapRosbridgeProtocol.decodeMap(from: try frame("map_saved")))
        let manager = try #require(
            try MapRosbridgeProtocol.decodeMapManagerStatus(
                from: try frame("map_manager_save_result")
            )
        )
        let rooms = try #require(
            try MapRosbridgeProtocol.decodeSemanticMapStatus(from: try frame("room_status_bound"))
        )

        // The app computes the same content fingerprint as the map store.
        #expect(manager.ok)
        #expect(manager.map.summary?.fingerprint == map.contentFingerprint)
        #expect(manager.storage.lastSaved?.matches(map) == true)

        #expect(SemanticMapClientPolicy.canEditRooms(
            mapIsLive: true,
            currentMap: map,
            managerStatus: manager,
            semanticStatus: rooms,
            mutationIsPending: false,
            reloadIsRequired: false
        ))
    }

    @Test
    func createdRoomIsShownOnTheSavedMap() throws {
        let map = try #require(try MapRosbridgeProtocol.decodeMap(from: try frame("map_saved")))
        let manager = try #require(
            try MapRosbridgeProtocol.decodeMapManagerStatus(
                from: try frame("map_manager_save_result")
            )
        )
        let created = try #require(
            try MapRosbridgeProtocol.decodeSemanticMapStatus(from: try frame("room_status_created"))
        )
        let bound = try #require(
            try MapRosbridgeProtocol.decodeSemanticMapStatus(from: try frame("room_status_bound"))
        )

        let snapshot = try #require(SemanticMapClientPolicy.matchedSnapshot(
            mapIsLive: true,
            currentMap: map,
            managerStatus: manager,
            semanticStatus: created
        ))
        #expect(snapshot.rooms.map(\.id) == ["kueche"])
        #expect(snapshot.rooms.first?.navigationGoal != nil)

        let acknowledgement = SemanticMapClientPolicy.validateMutationAcknowledgement(
            created,
            expectedRequestID: try #require(created.requestID),
            mapIsLive: true,
            currentMap: map,
            managerStatus: manager,
            expectedFingerprint: map.contentFingerprint,
            baseRevision: try #require(bound.semanticMap?.revision),
            expectation: .upsert(roomID: "kueche")
        )
        #expect(acknowledgement == .accepted)
    }

    // MARK: - Missions

    private func missionStatus(_ name: String) throws -> MissionStatus {
        let event = try RosbridgeProtocol.decodeEvent(from: try frame(name))
        guard case let .missionStatus(status) = event else {
            Issue.record("\(name) is not a mission status")
            throw RosbridgeProtocolError.invalidMissionStatus
        }
        return status
    }

    @Test
    func acceptedDriveConfirmsThePendingCommand() throws {
        let status = try missionStatus("mission_go_to_room_result")
        #expect(status.event == "go_to_room_result")
        #expect(status.ok)
        let pending = PendingMissionCommand(
            kind: .goToRoom(roomID: "wohnzimmer"),
            requestID: try #require(status.requestID),
            sentAt: Date()
        )
        #expect(MissionPolicy.resolution(of: pending, with: status) == .confirmed)
    }

    @Test
    func runningDriveOffersCancelButNoSecondDrive() throws {
        let status = try missionStatus("mission_running")
        #expect(status.mission.state == .running)
        #expect(status.mission.roomID == "wohnzimmer")
        #expect(status.mission.distanceRemainingMeters != nil)
        #expect(status.startBlockReason == "busy")
        #expect(MissionPolicy.cancelIsOffered(
            connected: true, statusIsFresh: true, everReceived: true, snapshot: status.mission
        ))
        #expect(!MissionPolicy.canGoToRoom(
            connected: true, statusIsFresh: true, status: status, roomHasGoal: true, commandPending: false
        ))
    }

    @Test
    func finishedDriveAllowsTheNextOne() throws {
        let status = try missionStatus("mission_finished")
        #expect(status.mission.state == .succeeded)
        #expect(MissionText.state(status.mission) == "Wohnzimmer erreicht")
        #expect(MissionPolicy.canGoToRoom(
            connected: true, statusIsFresh: true, status: status, roomHasGoal: true, commandPending: false
        ))
    }

    @Test
    func cancelResultEndsTheMission() throws {
        let status = try missionStatus("mission_cancel_result")
        #expect(status.event == "cancel_result")
        #expect(status.mission.state == .canceled)
        let pending = PendingMissionCommand(
            kind: .cancel, requestID: try #require(status.requestID), sentAt: Date()
        )
        #expect(MissionPolicy.resolution(of: pending, with: status) == .confirmed)
    }

    @Test
    func refusalsCarryAReasonTheAppExplains() throws {
        for (name, reason) in [
            ("mission_refused_mapping", "mapping_active"),
            ("mission_refused_not_localized", "not_localized")
        ] {
            let status = try missionStatus(name)
            #expect(!status.ok)
            #expect(status.startBlockReason == reason)
            #expect(MissionText.blockReason(status.startBlockReason) != nil)
        }
    }
}
