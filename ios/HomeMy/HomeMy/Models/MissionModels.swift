import Foundation

/// Zustand eines Auftrags laut `contracts/api/app-bridge.md`, Abschnitt Missions.
enum MissionState: String, Equatable, Sendable {
    case idle
    case running
    case succeeded
    case failed
    case canceled
}

enum MissionCommandKind: Equatable, Sendable {
    case goToRoom(roomID: String)
    case cancel
}

struct MissionSnapshot: Decodable, Equatable, Sendable {
    let state: MissionState
    let command: String?
    let roomID: String?
    let roomName: String?
    let phase: String?
    let attempt: Int
    let maxAttempts: Int
    let distanceRemainingMeters: Double?
    let result: String?

    enum CodingKeys: String, CodingKey {
        case state
        case command
        case roomID = "room_id"
        case roomName = "room_name"
        case phase
        case attempt
        case maxAttempts = "max_attempts"
        case distanceRemainingMeters = "distance_remaining_m"
        case result
    }

    init(
        state: MissionState,
        command: String?,
        roomID: String?,
        roomName: String?,
        phase: String?,
        attempt: Int,
        maxAttempts: Int,
        distanceRemainingMeters: Double?,
        result: String?
    ) {
        self.state = state
        self.command = command
        self.roomID = roomID
        self.roomName = roomName
        self.phase = phase
        self.attempt = attempt
        self.maxAttempts = maxAttempts
        self.distanceRemainingMeters = distanceRemainingMeters
        self.result = result
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let rawState = try container.decode(String.self, forKey: .state)
        guard let state = MissionState(rawValue: rawState) else {
            throw DecodingError.dataCorruptedError(
                forKey: .state,
                in: container,
                debugDescription: "Unbekannter Auftragszustand."
            )
        }
        self.state = state
        command = try container.decodeIfPresent(String.self, forKey: .command)
        roomID = try container.decodeIfPresent(String.self, forKey: .roomID)
        roomName = try container.decodeIfPresent(String.self, forKey: .roomName)
        phase = try container.decodeIfPresent(String.self, forKey: .phase)
        attempt = try container.decode(Int.self, forKey: .attempt)
        maxAttempts = try container.decode(Int.self, forKey: .maxAttempts)
        distanceRemainingMeters = try container.decodeIfPresent(
            Double.self,
            forKey: .distanceRemainingMeters
        )
        result = try container.decodeIfPresent(String.self, forKey: .result)
    }

    var isValid: Bool {
        guard attempt >= 0, maxAttempts >= 0, attempt <= maxAttempts else {
            return false
        }
        if let distanceRemainingMeters {
            guard distanceRemainingMeters.isFinite, distanceRemainingMeters >= 0 else {
                return false
            }
        }
        if state == .idle {
            return command == nil && roomID == nil
        }
        guard command == "go_to_room", let roomID, !roomID.isEmpty, maxAttempts >= 1 else {
            return false
        }
        return true
    }
}

struct MissionStatus: Decodable, Equatable, Sendable {
    static let knownEvents = Set([
        "status",
        "go_to_room_result",
        "cancel_result",
        "command_result"
    ])

    let schemaVersion: Int
    let event: String
    let ok: Bool
    let requestID: String?
    let message: String
    let mission: MissionSnapshot
    let startBlockReason: String?
    let time: Double

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case event
        case ok
        case requestID = "request_id"
        case message
        case mission
        case startBlockReason = "start_block_reason"
        case time
    }

    var isValid: Bool {
        schemaVersion == 1 &&
            MissionStatus.knownEvents.contains(event) &&
            !message.isEmpty &&
            time.isFinite &&
            (startBlockReason.map { !$0.isEmpty } ?? true) &&
            mission.isValid
    }
}

struct PendingMissionCommand: Equatable, Sendable {
    let kind: MissionCommandKind
    let requestID: String
    let sentAt: Date
}

/// Bedienregeln für Aufträge. Wie beim Kartiermodus schaltet nur ein frischer,
/// eindeutiger Status eine Fahrt frei; im Zweifel bleibt nur das Abbrechen.
enum MissionPolicy {
    static let staleAfter: TimeInterval = 2.5
    static let commandConfirmationTimeout: TimeInterval = 4
    static let cancelResendInterval: TimeInterval = 0.4
    static let cancelConfirmationTimeout: TimeInterval = 4

    static func canGoToRoom(
        connected: Bool,
        statusIsFresh: Bool,
        status: MissionStatus?,
        roomHasGoal: Bool,
        commandPending: Bool
    ) -> Bool {
        guard connected, statusIsFresh, !commandPending, roomHasGoal,
              let status, status.isValid else {
            return false
        }
        return status.mission.state != .running && status.startBlockReason == nil
    }

    /// Abbrechen wird angeboten, solange ein Auftrag läuft oder sein Zustand
    /// unbekannt ist, aber nur, wenn der Roboter überhaupt Aufträge kennt.
    static func cancelIsOffered(
        connected: Bool,
        statusIsFresh: Bool,
        everReceived: Bool,
        snapshot: MissionSnapshot?
    ) -> Bool {
        guard connected, everReceived else { return false }
        guard statusIsFresh, let snapshot, snapshot.isValid else { return true }
        return snapshot.state == .running
    }

    static func resolution(
        of pending: PendingMissionCommand,
        with status: MissionStatus
    ) -> PendingMappingCommandResolution {
        if status.requestID == pending.requestID {
            return status.ok ? .confirmed : .refused(status.message)
        }
        if case .cancel = pending.kind, status.mission.state != .running {
            return .confirmed
        }
        return .stillPending
    }
}

/// Deutsche Anzeige der Kennungen aus dem Vertrag.
enum MissionText {
    static func state(_ snapshot: MissionSnapshot) -> String {
        let room = snapshot.roomName ?? snapshot.roomID ?? "Raum"
        switch snapshot.state {
        case .idle:
            return "Kein Auftrag"
        case .running:
            return "Fährt zu \(room)"
        case .succeeded:
            return "\(room) erreicht"
        case .failed:
            return "\(room) nicht erreicht"
        case .canceled:
            return "Fahrt zu \(room) abgebrochen"
        }
    }

    static func phase(_ snapshot: MissionSnapshot) -> String? {
        guard snapshot.state == .running else { return nil }
        switch snapshot.phase {
        case "starting":
            return "Fahrt wird gestartet"
        case "driving":
            if let distance = snapshot.distanceRemainingMeters {
                return String(format: "unterwegs, noch %.1f m", distance)
            }
            return "unterwegs"
        case "waiting_retry":
            return "wartet und versucht es erneut (Versuch \(snapshot.attempt) von \(snapshot.maxAttempts))"
        case let .some(other):
            return other
        case .none:
            return nil
        }
    }

    static func result(_ result: String?) -> String? {
        switch result {
        case .none, "arrived":
            return nil
        case "app_cancel":
            return "in der App abgebrochen"
        case "mapping_started":
            return "abgebrochen, weil der Kartiermodus begann"
        case "localization_lost":
            return "der Roboter wusste nicht mehr sicher, wo er ist"
        case let .some(other) where other.hasPrefix("navigation_failed"):
            return "kein Weg gefunden oder Weg blockiert"
        case let .some(other) where other.hasPrefix("lifecycle_"):
            return "der Roboter meldet einen Fehler oder wird ausgeschaltet"
        case let .some(other):
            return other
        }
    }

    static func blockReason(_ reason: String?) -> String? {
        switch reason {
        case .none:
            return nil
        case "busy":
            return "Es läuft schon ein Auftrag."
        case "mapping_active":
            return "Erst den Kartiermodus beenden."
        case "not_ready":
            return "Der Roboter ist noch nicht bereit."
        case "no_map":
            return "Es gibt noch keine gespeicherte Karte."
        case "rooms_not_bound":
            return "Die Räume gehören nicht zur geladenen Karte."
        case "not_localized":
            return "Der Roboter weiß noch nicht sicher, wo er ist. Er sucht seine Position in der Karte; das dauert einige Sekunden."
        case "navigation_unavailable":
            return "Die Wegplanung ist nicht bereit."
        case "room_invalid":
            return "Der Raum hat kein gültiges Fahrziel."
        case let .some(other):
            return "Fahrt derzeit nicht möglich (\(other))."
        }
    }
}
