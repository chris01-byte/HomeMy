import Foundation

/// Zustand des Kartiermodus laut `contracts/api/app-bridge.md`.
enum MappingModeState: String, Equatable, Sendable {
    case off
    case active
}

enum MappingModeCommandKind: String, Equatable, Sendable {
    case enable
    case disable
    case stop
}

struct MappingModeSnapshot: Decodable, Equatable, Sendable {
    let state: MappingModeState
    let controllerConnected: Bool
    let autoEndTimeoutSeconds: Double
    let autoEndRemainingSeconds: Double?
    let lastEndReason: String?
    let enableBlockReason: String?

    enum CodingKeys: String, CodingKey {
        case state
        case controllerConnected = "controller_connected"
        case autoEndTimeoutSeconds = "auto_end_timeout_s"
        case autoEndRemainingSeconds = "auto_end_remaining_s"
        case lastEndReason = "last_end_reason"
        case enableBlockReason = "enable_block_reason"
    }

    init(
        state: MappingModeState,
        controllerConnected: Bool,
        autoEndTimeoutSeconds: Double,
        autoEndRemainingSeconds: Double?,
        lastEndReason: String?,
        enableBlockReason: String?
    ) {
        self.state = state
        self.controllerConnected = controllerConnected
        self.autoEndTimeoutSeconds = autoEndTimeoutSeconds
        self.autoEndRemainingSeconds = autoEndRemainingSeconds
        self.lastEndReason = lastEndReason
        self.enableBlockReason = enableBlockReason
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let rawState = try container.decode(String.self, forKey: .state)
        guard let state = MappingModeState(rawValue: rawState) else {
            throw DecodingError.dataCorruptedError(
                forKey: .state,
                in: container,
                debugDescription: "Unbekannter Kartiermodus-Zustand."
            )
        }
        self.state = state
        controllerConnected = try container.decode(Bool.self, forKey: .controllerConnected)
        autoEndTimeoutSeconds = try container.decode(Double.self, forKey: .autoEndTimeoutSeconds)
        autoEndRemainingSeconds = try container.decodeIfPresent(
            Double.self,
            forKey: .autoEndRemainingSeconds
        )
        lastEndReason = try container.decodeIfPresent(String.self, forKey: .lastEndReason)
        enableBlockReason = try container.decodeIfPresent(String.self, forKey: .enableBlockReason)
    }

    /// Nur vollständig plausible Zustände dürfen eine Bedienung freischalten.
    var isValid: Bool {
        guard autoEndTimeoutSeconds.isFinite, autoEndTimeoutSeconds > 0 else {
            return false
        }
        if let remaining = autoEndRemainingSeconds {
            guard state == .active, remaining.isFinite, remaining >= 0,
                  remaining <= autoEndTimeoutSeconds else {
                return false
            }
        }
        if let lastEndReason, lastEndReason.isEmpty {
            return false
        }
        if let enableBlockReason, enableBlockReason.isEmpty {
            return false
        }
        return true
    }
}

struct MappingModeStatus: Decodable, Equatable, Sendable {
    static let knownEvents = Set([
        "status",
        "enable_result",
        "disable_result",
        "stop_result"
    ])

    let schemaVersion: Int
    let event: String
    let ok: Bool
    let requestID: String?
    let message: String
    let mappingMode: MappingModeSnapshot
    let time: Double

    enum CodingKeys: String, CodingKey {
        case schemaVersion = "schema_version"
        case event
        case ok
        case requestID = "request_id"
        case message
        case mappingMode = "mapping_mode"
        case time
    }

    var isValid: Bool {
        schemaVersion == 1 &&
            MappingModeStatus.knownEvents.contains(event) &&
            !message.isEmpty &&
            time.isFinite &&
            mappingMode.isValid
    }
}

/// Reine Bedienregeln der App. Sie schalten nur frei, wenn der Roboter den
/// Zustand frisch und eindeutig meldet; im Zweifel bleibt nur der Stopp.
enum MappingModePolicy {
    static let staleAfter: TimeInterval = 2.5
    static let commandConfirmationTimeout: TimeInterval = 4
    static let stopResendInterval: TimeInterval = 0.4
    static let stopConfirmationTimeout: TimeInterval = 4

    static func canEnable(
        connected: Bool,
        statusIsFresh: Bool,
        snapshot: MappingModeSnapshot?,
        commandPending: Bool,
        stopPending: Bool
    ) -> Bool {
        guard connected, statusIsFresh, !commandPending, !stopPending,
              let snapshot, snapshot.isValid else {
            return false
        }
        return snapshot.state == .off && snapshot.enableBlockReason == nil
    }

    static func canDisable(
        connected: Bool,
        statusIsFresh: Bool,
        snapshot: MappingModeSnapshot?,
        commandPending: Bool,
        stopPending: Bool
    ) -> Bool {
        guard connected, statusIsFresh, !commandPending, !stopPending,
              let snapshot, snapshot.isValid else {
            return false
        }
        return snapshot.state == .active
    }

    /// Der Stopp wird angeboten, sobald die Verbindung steht und der Modus
    /// aktiv oder unbekannt ist. Nur ein frisch bestätigtes „aus“ blendet ihn aus.
    static func stopIsOffered(
        connected: Bool,
        statusIsFresh: Bool,
        snapshot: MappingModeSnapshot?
    ) -> Bool {
        guard connected else { return false }
        return !isConfirmedOff(statusIsFresh: statusIsFresh, snapshot: snapshot)
    }

    static func isConfirmedOff(
        statusIsFresh: Bool,
        snapshot: MappingModeSnapshot?
    ) -> Bool {
        guard statusIsFresh, let snapshot, snapshot.isValid else {
            return false
        }
        return snapshot.state == .off
    }

    static func isConfirmedActive(
        statusIsFresh: Bool,
        snapshot: MappingModeSnapshot?
    ) -> Bool {
        guard statusIsFresh, let snapshot, snapshot.isValid else {
            return false
        }
        return snapshot.state == .active
    }

    /// Eine Karte darf nur gespeichert werden, solange der Roboter frisch
    /// bestätigt, dass nicht mehr kartiert wird.
    static func mapSaveIsAllowed(
        connected: Bool,
        statusIsFresh: Bool,
        snapshot: MappingModeSnapshot?
    ) -> Bool {
        connected && isConfirmedOff(statusIsFresh: statusIsFresh, snapshot: snapshot)
    }

    /// Bewertet eine Statusmeldung gegen einen offenen Befehl.
    static func resolution(
        of pending: PendingMappingCommand,
        with status: MappingModeStatus
    ) -> PendingMappingCommandResolution {
        if status.requestID == pending.requestID {
            return status.ok ? .confirmed : .refused(status.message)
        }
        switch (pending.kind, status.mappingMode.state) {
        case (.enable, .active), (.disable, .off), (.stop, .off):
            return .confirmed
        default:
            return .stillPending
        }
    }
}

struct PendingMappingCommand: Equatable, Sendable {
    let kind: MappingModeCommandKind
    let requestID: String
    let sentAt: Date
}

enum PendingMappingCommandResolution: Equatable, Sendable {
    case stillPending
    case confirmed
    case refused(String)
}

/// Deutsche Anzeige für die im Vertrag festgelegten Kennungen.
enum MappingModeText {
    static func endReason(_ reason: String?) -> String? {
        switch reason {
        case .none:
            return nil
        case "app_disable":
            return "in der App beendet"
        case "app_stop":
            return "durch Stopp in der App beendet"
        case "inactivity_timeout":
            return "automatisch beendet, weil der Controller nicht benutzt wurde"
        case "fault":
            return "wegen eines Fehlers am Roboter beendet"
        case "shutdown":
            return "beim Ausschalten des Roboters beendet"
        case let .some(other):
            return "beendet (\(other))"
        }
    }

    static func blockReason(_ reason: String?) -> String? {
        switch reason {
        case .none:
            return nil
        case "not_ready":
            return "Der Roboter ist noch nicht bereit."
        case "fault":
            return "Der Roboter meldet einen Fehler."
        case "shutting_down":
            return "Der Roboter wird gerade ausgeschaltet."
        case let .some(other):
            return "Der Roboter lässt den Kartiermodus derzeit nicht zu (\(other))."
        }
    }

    static func remaining(_ seconds: Double) -> String {
        let total = max(0, Int(seconds.rounded(.down)))
        return String(format: "%d:%02d min", total / 60, total % 60)
    }

    static func timeout(_ seconds: Double) -> String {
        let total = max(0, Int(seconds.rounded()))
        if total % 60 == 0 {
            return "\(total / 60) min"
        }
        return "\(total) s"
    }
}

enum RobotConnectionState: Equatable {
    case disconnected
    case connecting
    case connected
    case failed(String)
    case waitingToReconnect(seconds: Int)

    var isConnected: Bool {
        if case .connected = self {
            return true
        }
        return false
    }

    var label: String {
        switch self {
        case .disconnected:
            return "getrennt"
        case .connecting:
            return "verbinde …"
        case .connected:
            return "verbunden"
        case .failed:
            return "Fehler"
        case let .waitingToReconnect(seconds):
            return "erneut in \(seconds) s"
        }
    }

    var errorMessage: String? {
        if case let .failed(message) = self {
            return message
        }
        return nil
    }
}

enum RobotLogKind {
    case info
    case success
    case warning
    case error
    case emergency
}

struct RobotLogEntry: Identifiable {
    let id = UUID()
    let date: Date
    let message: String
    let kind: RobotLogKind
}
