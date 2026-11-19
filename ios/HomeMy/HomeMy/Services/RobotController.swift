import Foundation

/// Steuerverbindung der App: Kartiermodus ein/aus und Stopp.
///
/// Die App sendet niemals Fahrbefehle. Gefahren wird ausschließlich mit dem
/// Controller am Roboter; siehe `contracts/api/app-bridge.md`.
@MainActor
final class RobotController: NSObject, ObservableObject {
    static let defaultBridgeURL = "ws://homemy.local:9090/"

    private static let bridgeURLDefaultsKey = "homemy_bridge_url"

    @Published var bridgeURL: String
    @Published private(set) var connectionState: RobotConnectionState = .disconnected
    @Published private(set) var mappingStatus: MappingModeStatus?
    @Published private(set) var mappingStatusIsFresh = false
    @Published private(set) var pendingCommand: PendingMappingCommand?
    @Published private(set) var pendingStop: PendingMappingCommand?
    @Published private(set) var missionStatus: MissionStatus?
    @Published private(set) var missionStatusIsFresh = false
    @Published private(set) var missionStatusEverReceived = false
    @Published private(set) var pendingMissionCommand: PendingMissionCommand?
    @Published private(set) var pendingMissionCancel: PendingMissionCommand?
    @Published private(set) var lastConnectionError: String?
    @Published private(set) var logEntries: [RobotLogEntry] = []

    private var session: URLSession?
    private var socketTask: URLSessionWebSocketTask?
    private var activeBridgeURL: String?
    private var receiveLoopTask: Task<Void, Never>?
    private var pingLoopTask: Task<Void, Never>?
    private var reconnectTask: Task<Void, Never>?
    private var staleMonitorTask: Task<Void, Never>?
    private var stopLoopTask: Task<Void, Never>?
    private var missionCancelTask: Task<Void, Never>?
    private var lastMissionStatusAt: Date?
    private var lastStatusReceivedAt: Date?
    private var lastProtocolErrorAt: Date?
    private var reconnectAttempt = 0
    private var shouldReconnect = false
    private var hasStarted = false

    override init() {
        bridgeURL = UserDefaults.standard.string(
            forKey: RobotController.bridgeURLDefaultsKey
        ) ?? RobotController.defaultBridgeURL
        super.init()
    }

    // MARK: - Abgeleiteter Zustand für die Oberfläche

    var mappingSnapshot: MappingModeSnapshot? {
        mappingStatus?.mappingMode
    }

    var commandIsPending: Bool {
        pendingCommand != nil
    }

    var stopIsPending: Bool {
        pendingStop != nil
    }

    var mappingModeConfirmedOff: Bool {
        MappingModePolicy.isConfirmedOff(
            statusIsFresh: mappingStatusIsFresh,
            snapshot: mappingSnapshot
        )
    }

    var mappingModeConfirmedActive: Bool {
        MappingModePolicy.isConfirmedActive(
            statusIsFresh: mappingStatusIsFresh,
            snapshot: mappingSnapshot
        )
    }

    var canEnableMappingMode: Bool {
        MappingModePolicy.canEnable(
            connected: connectionState.isConnected,
            statusIsFresh: mappingStatusIsFresh,
            snapshot: mappingSnapshot,
            commandPending: commandIsPending,
            stopPending: stopIsPending
        )
    }

    var canDisableMappingMode: Bool {
        MappingModePolicy.canDisable(
            connected: connectionState.isConnected,
            statusIsFresh: mappingStatusIsFresh,
            snapshot: mappingSnapshot,
            commandPending: commandIsPending,
            stopPending: stopIsPending
        )
    }

    var stopIsOffered: Bool {
        MappingModePolicy.stopIsOffered(
            connected: connectionState.isConnected,
            statusIsFresh: mappingStatusIsFresh,
            snapshot: mappingSnapshot
        )
    }

    var mapSaveIsAllowed: Bool {
        MappingModePolicy.mapSaveIsAllowed(
            connected: connectionState.isConnected,
            statusIsFresh: mappingStatusIsFresh,
            snapshot: mappingSnapshot
        )
    }

    // MARK: Aufträge

    var missionSnapshot: MissionSnapshot? {
        missionStatus?.mission
    }

    func canGoToRoom(hasNavigationGoal: Bool) -> Bool {
        MissionPolicy.canGoToRoom(
            connected: connectionState.isConnected,
            statusIsFresh: missionStatusIsFresh,
            status: missionStatus,
            roomHasGoal: hasNavigationGoal,
            commandPending: pendingMissionCommand != nil || pendingMissionCancel != nil
        )
    }

    var missionCancelIsOffered: Bool {
        MissionPolicy.cancelIsOffered(
            connected: connectionState.isConnected,
            statusIsFresh: missionStatusIsFresh,
            everReceived: missionStatusEverReceived,
            snapshot: missionSnapshot
        )
    }

    var headline: String {
        guard connectionState.isConnected else {
            return "Nicht mit dem Roboter verbunden"
        }
        guard mappingStatusIsFresh, let snapshot = mappingSnapshot else {
            return "Warte auf den Status des Roboters"
        }
        switch snapshot.state {
        case .active:
            return snapshot.controllerConnected
                ? "Kartiermodus aktiv – mit dem Controller fahren"
                : "Kartiermodus aktiv – Controller nicht verbunden"
        case .off:
            return "Bereit"
        }
    }

    // MARK: - Verbindung

    func start() {
        guard !hasStarted else { return }
        hasStarted = true
        shouldReconnect = true
        startStaleMonitor()
        openConnection(resetBackoff: true)
    }

    func connectNow() {
        shouldReconnect = true
        cancelReconnect()
        openConnection(resetBackoff: true)
    }

    func disconnect() {
        shouldReconnect = false
        cancelReconnect()
        closeCurrentSocket(closeCode: .normalClosure)
        connectionState = .disconnected
        lastConnectionError = nil
        markTelemetryUnknown()
        addLog("Verbindung manuell getrennt", kind: .info)
    }

    func appDidEnterBackground() {
        guard shouldReconnect else { return }
        cancelReconnect()
        closeCurrentSocket(closeCode: .goingAway)
        connectionState = .disconnected
        markTelemetryUnknown()
    }

    func appDidBecomeActive() {
        guard hasStarted, shouldReconnect, socketTask == nil, reconnectTask == nil else {
            return
        }
        openConnection(resetBackoff: false)
    }

    // MARK: - Kartiermodus

    func enableMappingMode() {
        guard canEnableMappingMode else {
            addLog("Kartiermodus kann gerade nicht eingeschaltet werden", kind: .warning)
            return
        }
        sendModeCommand(.enable, logMessage: "Kartiermodus einschalten – warte auf Bestätigung")
    }

    func disableMappingMode() {
        guard canDisableMappingMode else {
            addLog("Kartiermodus kann gerade nicht beendet werden", kind: .warning)
            return
        }
        sendModeCommand(.disable, logMessage: "Kartiermodus beenden – warte auf Bestätigung")
    }

    // MARK: - Aufträge

    func goToRoom(roomID: String, roomName: String, hasNavigationGoal: Bool) {
        guard canGoToRoom(hasNavigationGoal: hasNavigationGoal) else {
            addLog("Fahrt zu \(roomName) ist gerade nicht möglich", kind: .warning)
            return
        }
        guard let task = readySocket() else { return }
        let command = PendingMissionCommand(
            kind: .goToRoom(roomID: roomID),
            requestID: RobotController.makeRequestID(prefix: "ios-go"),
            sentAt: Date()
        )
        do {
            let frame = try RosbridgeProtocol.missionCommandFrame(command.kind, requestID: command.requestID)
            pendingMissionCommand = command
            Task { [weak self, task, command] in
                do {
                    try await task.send(.string(frame))
                    guard let self, self.socketTask === task else { return }
                    self.addLog("Fahrt zu \(roomName) angefordert", kind: .info)
                } catch {
                    guard let self else { return }
                    if self.pendingMissionCommand == command {
                        self.pendingMissionCommand = nil
                    }
                    self.handleSocketFailure(task, error: error)
                }
            }
        } catch {
            addLog(error.localizedDescription, kind: .error)
        }
    }

    /// Bricht den laufenden Auftrag ab und wiederholt die Anforderung, bis der
    /// Roboter meldet, dass kein Auftrag mehr läuft, höchstens vier Sekunden.
    func cancelMission() {
        guard pendingMissionCancel == nil, missionCancelIsOffered else { return }
        guard let task = readySocket() else { return }
        let cancel = PendingMissionCommand(
            kind: .cancel,
            requestID: RobotController.makeRequestID(prefix: "ios-cancel"),
            sentAt: Date()
        )
        pendingMissionCommand = nil
        pendingMissionCancel = cancel
        addLog("Auftrag abbrechen", kind: .emergency)
        missionCancelTask?.cancel()
        missionCancelTask = Task { [weak self, task, cancel] in
            let interval = UInt64(MissionPolicy.cancelResendInterval * 1_000_000_000)
            while !Task.isCancelled {
                guard let self, self.pendingMissionCancel == cancel, self.socketTask === task else {
                    return
                }
                if Date().timeIntervalSince(cancel.sentAt) > MissionPolicy.cancelConfirmationTimeout {
                    self.pendingMissionCancel = nil
                    self.addLog(
                        "Der Roboter hat den Abbruch nicht bestätigt. Bitte direkt am Roboter prüfen.",
                        kind: .error
                    )
                    return
                }
                do {
                    try await task.send(.string(
                        try RosbridgeProtocol.missionCommandFrame(.cancel, requestID: cancel.requestID)
                    ))
                    try await Task.sleep(nanoseconds: interval)
                } catch is CancellationError {
                    return
                } catch {
                    self.handleSocketFailure(task, error: error)
                    return
                }
            }
        }
    }

    private func apply(_ status: MissionStatus) {
        let previous = missionStatusIsFresh ? missionSnapshot : nil
        missionStatus = status
        lastMissionStatusAt = Date()
        missionStatusIsFresh = true
        missionStatusEverReceived = true

        if let cancel = pendingMissionCancel {
            switch MissionPolicy.resolution(of: cancel, with: status) {
            case .confirmed:
                clearPendingMissionCancel()
                addLog("Abbruch bestätigt – kein Auftrag läuft", kind: .success)
            case let .refused(message):
                clearPendingMissionCancel()
                addLog("Abbruch abgelehnt: \(message)", kind: .error)
            case .stillPending:
                break
            }
        }
        if let command = pendingMissionCommand {
            switch MissionPolicy.resolution(of: command, with: status) {
            case .confirmed:
                pendingMissionCommand = nil
            case let .refused(message):
                pendingMissionCommand = nil
                addLog("Fahrt abgelehnt: \(message)", kind: .warning)
            case .stillPending:
                break
            }
        }

        let current = status.mission
        guard let previous, previous.state != current.state else { return }
        let text = MissionText.state(current)
        switch current.state {
        case .running:
            addLog(text, kind: .info)
        case .succeeded:
            addLog(text, kind: .success)
        case .failed, .canceled:
            let reason = MissionText.result(current.result).map { " – \($0)" } ?? ""
            addLog(text + reason, kind: current.state == .failed ? .warning : .info)
        case .idle:
            break
        }
    }

    private func clearPendingMissionCancel() {
        pendingMissionCancel = nil
        missionCancelTask?.cancel()
        missionCancelTask = nil
    }

    // MARK: - Stopp

    /// Fordert das Anhalten und Beenden des Kartiermodus an und wiederholt die
    /// Anforderung, bis der Roboter „aus“ bestätigt oder die Frist abläuft.
    /// Läuft ein Auftrag, wird er ebenfalls abgebrochen.
    func requestStop() {
        if missionCancelIsOffered {
            cancelMission()
        }
        guard pendingStop == nil else { return }
        guard let task = readySocket() else { return }

        let stop = PendingMappingCommand(
            kind: .stop,
            requestID: RobotController.makeRequestID(prefix: "ios-stop"),
            sentAt: Date()
        )
        pendingCommand = nil
        pendingStop = stop
        addLog("STOPP gesendet", kind: .emergency)

        stopLoopTask?.cancel()
        stopLoopTask = Task { [weak self, task, stop] in
            let interval = UInt64(MappingModePolicy.stopResendInterval * 1_000_000_000)
            while !Task.isCancelled {
                guard let self, self.pendingStop == stop, self.socketTask === task else {
                    return
                }
                if Date().timeIntervalSince(stop.sentAt) >
                    MappingModePolicy.stopConfirmationTimeout {
                    self.pendingStop = nil
                    self.addLog(
                        "Der Roboter hat den Stopp nicht bestätigt. Bitte direkt am Roboter prüfen.",
                        kind: .error
                    )
                    return
                }
                do {
                    try await task.send(.string(
                        try RosbridgeProtocol.mappingModeCommandFrame(
                            .stop,
                            requestID: stop.requestID
                        )
                    ))
                    try await Task.sleep(nanoseconds: interval)
                } catch is CancellationError {
                    return
                } catch {
                    self.handleSocketFailure(task, error: error)
                    return
                }
            }
        }
    }

    private func sendModeCommand(_ kind: MappingModeCommandKind, logMessage: String) {
        guard let task = readySocket() else { return }
        let command = PendingMappingCommand(
            kind: kind,
            requestID: RobotController.makeRequestID(prefix: "ios-mode"),
            sentAt: Date()
        )
        do {
            let frame = try RosbridgeProtocol.mappingModeCommandFrame(
                kind,
                requestID: command.requestID
            )
            pendingCommand = command
            Task { [weak self, task, command] in
                do {
                    try await task.send(.string(frame))
                    guard let self, self.socketTask === task else { return }
                    self.addLog(logMessage, kind: .info)
                } catch {
                    guard let self else { return }
                    if self.pendingCommand == command {
                        self.pendingCommand = nil
                    }
                    self.handleSocketFailure(task, error: error)
                }
            }
        } catch {
            addLog(error.localizedDescription, kind: .error)
        }
    }

    private static func makeRequestID(prefix: String) -> String {
        "\(prefix)-\(UUID().uuidString.lowercased())"
    }

    private func apply(_ status: MappingModeStatus) {
        let previous = mappingStatusIsFresh ? mappingSnapshot : nil
        mappingStatus = status
        lastStatusReceivedAt = Date()
        mappingStatusIsFresh = true

        if let stop = pendingStop {
            switch MappingModePolicy.resolution(of: stop, with: status) {
            case .confirmed:
                clearPendingStop()
                addLog("Stopp bestätigt – Kartiermodus ist aus", kind: .success)
            case let .refused(message):
                clearPendingStop()
                addLog("Stopp abgelehnt: \(message)", kind: .error)
            case .stillPending:
                break
            }
        }

        if let command = pendingCommand {
            switch MappingModePolicy.resolution(of: command, with: status) {
            case .confirmed:
                pendingCommand = nil
            case let .refused(message):
                pendingCommand = nil
                addLog("Abgelehnt: \(message)", kind: .warning)
            case .stillPending:
                break
            }
        }

        let current = status.mappingMode
        guard let previous, previous.state != current.state else { return }
        switch current.state {
        case .active:
            addLog("Kartiermodus ist aktiv", kind: .success)
        case .off:
            let reason = MappingModeText.endReason(current.lastEndReason) ?? "beendet"
            addLog("Kartiermodus \(reason)", kind: .info)
        }
    }

    private func clearPendingStop() {
        pendingStop = nil
        stopLoopTask?.cancel()
        stopLoopTask = nil
    }

    // MARK: - WebSocket

    private func readySocket() -> URLSessionWebSocketTask? {
        guard connectionState.isConnected, let socketTask else {
            addLog("Keine Verbindung zum Roboter", kind: .error)
            return nil
        }
        return socketTask
    }

    private func openConnection(resetBackoff: Bool) {
        guard let url = normalizedBridgeURL(from: bridgeURL) else {
            shouldReconnect = false
            let message = "Bitte eine gültige WebSocket-Adresse eingeben, z. B. ws://192.168.1.50:9090/."
            connectionState = .failed(message)
            lastConnectionError = message
            addLog(message, kind: .error)
            return
        }

        if resetBackoff {
            reconnectAttempt = 0
        }

        closeCurrentSocket(closeCode: .goingAway)
        bridgeURL = url.absoluteString
        activeBridgeURL = url.absoluteString
        connectionState = .connecting
        lastConnectionError = nil
        markTelemetryUnknown()
        addLog("Verbinde \(url.absoluteString)", kind: .info)

        let configuration = URLSessionConfiguration.ephemeral
        configuration.timeoutIntervalForRequest = 12
        configuration.requestCachePolicy = .reloadIgnoringLocalCacheData

        let session = URLSession(
            configuration: configuration,
            delegate: self,
            delegateQueue: nil
        )
        var request = URLRequest(url: url)
        request.timeoutInterval = 12
        let task = session.webSocketTask(with: request)

        self.session = session
        socketTask = task
        task.maximumMessageSize = 1_048_576
        task.resume()
    }

    private func normalizedBridgeURL(from input: String) -> URL? {
        var value = input.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty else { return nil }

        if !value.contains("://") {
            value = "ws://\(value)"
        }

        guard var components = URLComponents(string: value) else { return nil }
        switch components.scheme?.lowercased() {
        case "http":
            components.scheme = "ws"
        case "https":
            components.scheme = "wss"
        case "ws", "wss":
            break
        default:
            return nil
        }

        guard let host = components.host, !host.isEmpty else { return nil }
        if components.port == nil {
            components.port = 9090
        }
        if components.path.isEmpty {
            components.path = "/"
        }
        return components.url
    }

    private func socketDidOpen(_ task: URLSessionWebSocketTask) {
        guard socketTask === task else { return }
        connectionState = .connected
        reconnectAttempt = 0
        lastConnectionError = nil
        UserDefaults.standard.set(
            activeBridgeURL ?? bridgeURL,
            forKey: RobotController.bridgeURLDefaultsKey
        )
        addLog("Mit dem Roboter verbunden", kind: .success)

        startReceiveLoop(for: task)
        startPingLoop(for: task)

        Task { [weak self, task] in
            do {
                for frame in try RosbridgeProtocol.setupFrames() {
                    try await task.send(.string(frame))
                }
            } catch {
                guard let self else { return }
                self.handleSocketFailure(task, error: error)
            }
        }
    }

    private func startReceiveLoop(for task: URLSessionWebSocketTask) {
        receiveLoopTask?.cancel()
        receiveLoopTask = Task { [weak self, task] in
            do {
                while !Task.isCancelled {
                    let message = try await task.receive()
                    guard let self, self.socketTask === task else { return }
                    self.handleIncomingMessage(message)
                }
            } catch is CancellationError {
                return
            } catch {
                guard let self else { return }
                self.handleSocketFailure(task, error: error)
            }
        }
    }

    private func startPingLoop(for task: URLSessionWebSocketTask) {
        pingLoopTask?.cancel()
        pingLoopTask = Task { [weak self, task] in
            while !Task.isCancelled {
                do {
                    try await Task.sleep(nanoseconds: 15_000_000_000)
                    try await self?.sendPing(on: task)
                } catch is CancellationError {
                    return
                } catch {
                    guard let self else { return }
                    self.handleSocketFailure(task, error: error)
                    return
                }
            }
        }
    }

    private func sendPing(on task: URLSessionWebSocketTask) async throws {
        try await withCheckedThrowingContinuation {
            (continuation: CheckedContinuation<Void, Error>) in
            task.sendPing { error in
                if let error {
                    continuation.resume(throwing: error)
                } else {
                    continuation.resume()
                }
            }
        }
    }

    private func handleIncomingMessage(_ message: URLSessionWebSocketTask.Message) {
        let text: String?
        switch message {
        case let .string(value):
            text = value
        case let .data(data):
            text = String(data: data, encoding: .utf8)
        @unknown default:
            text = nil
        }

        guard let text else {
            addProtocolError("Binäre rosbridge-Nachricht ist kein UTF-8.")
            return
        }

        do {
            guard let event = try RosbridgeProtocol.decodeEvent(from: text) else { return }
            switch event {
            case let .mappingModeStatus(status):
                apply(status)
            case let .missionStatus(status):
                apply(status)
            }
        } catch {
            addProtocolError(error.localizedDescription)
        }
    }

    private func startStaleMonitor() {
        staleMonitorTask?.cancel()
        staleMonitorTask = Task { [weak self] in
            while !Task.isCancelled {
                do {
                    try await Task.sleep(nanoseconds: 1_000_000_000)
                } catch {
                    return
                }
                self?.updateFreshness()
            }
        }
    }

    private func updateFreshness(now: Date = Date()) {
        if let command = pendingCommand,
           now.timeIntervalSince(command.sentAt) >
            MappingModePolicy.commandConfirmationTimeout {
            pendingCommand = nil
            addLog("Keine Bestätigung vom Roboter erhalten", kind: .warning)
        }

        if mappingStatusIsFresh,
           now.timeIntervalSince(lastStatusReceivedAt ?? .distantPast) >
            MappingModePolicy.staleAfter {
            mappingStatusIsFresh = false
            addLog("Der Status des Kartiermodus ist veraltet", kind: .warning)
        }

        if let command = pendingMissionCommand,
           now.timeIntervalSince(command.sentAt) > MissionPolicy.commandConfirmationTimeout {
            pendingMissionCommand = nil
            addLog("Keine Bestätigung für die Fahrt erhalten", kind: .warning)
        }

        if missionStatusIsFresh,
           now.timeIntervalSince(lastMissionStatusAt ?? .distantPast) > MissionPolicy.staleAfter {
            missionStatusIsFresh = false
            addLog("Der Auftragsstatus ist veraltet", kind: .warning)
        }
    }

    private func markTelemetryUnknown() {
        mappingStatusIsFresh = false
        lastStatusReceivedAt = nil
        pendingCommand = nil
        missionStatusIsFresh = false
        lastMissionStatusAt = nil
        pendingMissionCommand = nil
        if pendingMissionCancel != nil {
            clearPendingMissionCancel()
            addLog(
                "Verbindung verloren, bevor der Abbruch bestätigt wurde. Bitte direkt am Roboter prüfen.",
                kind: .error
            )
        }
        if pendingStop != nil {
            clearPendingStop()
            addLog(
                "Verbindung verloren, bevor der Stopp bestätigt wurde. Bitte direkt am Roboter prüfen.",
                kind: .error
            )
        }
    }

    private func handleSocketFailure(_ task: URLSessionWebSocketTask, error: Error) {
        guard socketTask === task else { return }
        let message = friendlyNetworkError(error)
        closeCurrentSocket(closeCode: .goingAway)
        markTelemetryUnknown()
        lastConnectionError = message
        connectionState = .failed(message)
        addLog(message, kind: .error)
        scheduleReconnectIfNeeded()
    }

    private func socketDidClose(
        _ task: URLSessionWebSocketTask,
        closeCode: URLSessionWebSocketTask.CloseCode,
        reason: Data?
    ) {
        guard socketTask === task else { return }
        let reasonText = reason.flatMap { String(data: $0, encoding: .utf8) }
        closeCurrentSocket(closeCode: closeCode)
        markTelemetryUnknown()

        if shouldReconnect {
            let suffix = reasonText.map { ": \($0)" } ?? ""
            lastConnectionError = "Der Roboter hat die Verbindung beendet\(suffix)."
            addLog("Verbindung getrennt\(suffix)", kind: .warning)
            scheduleReconnectIfNeeded()
        } else {
            connectionState = .disconnected
        }
    }

    private func closeCurrentSocket(closeCode: URLSessionWebSocketTask.CloseCode) {
        receiveLoopTask?.cancel()
        pingLoopTask?.cancel()
        receiveLoopTask = nil
        pingLoopTask = nil

        let task = socketTask
        socketTask = nil
        activeBridgeURL = nil
        task?.cancel(with: closeCode, reason: nil)

        let currentSession = session
        session = nil
        currentSession?.invalidateAndCancel()
    }

    private func scheduleReconnectIfNeeded() {
        guard shouldReconnect, reconnectTask == nil else {
            if !shouldReconnect {
                connectionState = .disconnected
            }
            return
        }

        reconnectAttempt += 1
        let delay = min(15, 1 << min(reconnectAttempt, 4))
        reconnectTask = Task { [weak self] in
            for remaining in stride(from: delay, through: 1, by: -1) {
                guard let self, self.shouldReconnect else { return }
                self.connectionState = .waitingToReconnect(seconds: remaining)
                do {
                    try await Task.sleep(nanoseconds: 1_000_000_000)
                } catch {
                    return
                }
            }

            guard let self, self.shouldReconnect else { return }
            self.reconnectTask = nil
            self.openConnection(resetBackoff: false)
        }
    }

    private func cancelReconnect() {
        reconnectTask?.cancel()
        reconnectTask = nil
    }

    private func friendlyNetworkError(_ error: Error) -> String {
        guard let urlError = error as? URLError else {
            return "Verbindungsfehler: \(error.localizedDescription)"
        }
        switch urlError.code {
        case .cannotConnectToHost, .cannotFindHost:
            return "Roboter nicht erreichbar. Adresse, WLAN und Port 9090 prüfen."
        case .timedOut:
            return "Der Verbindungsaufbau zum Roboter hat zu lange gedauert."
        case .notConnectedToInternet, .networkConnectionLost:
            return "Keine stabile WLAN-Verbindung zum Roboter."
        case .appTransportSecurityRequiresSecureConnection:
            return "iOS blockiert die Verbindung. Für das lokale WLAN ist die App-Freigabe erforderlich."
        case .cancelled:
            return "Die Verbindung zum Roboter wurde beendet."
        default:
            return "Verbindungsfehler: \(urlError.localizedDescription)"
        }
    }

    private func addProtocolError(_ message: String) {
        let now = Date()
        if let lastProtocolErrorAt, now.timeIntervalSince(lastProtocolErrorAt) < 5 {
            return
        }
        lastProtocolErrorAt = now
        addLog("Protokollfehler: \(message)", kind: .error)
    }

    private func addLog(_ message: String, kind: RobotLogKind) {
        logEntries.insert(
            RobotLogEntry(date: Date(), message: message, kind: kind),
            at: 0
        )
        if logEntries.count > 40 {
            logEntries.removeLast(logEntries.count - 40)
        }
    }
}

extension RobotController: URLSessionWebSocketDelegate {
    nonisolated func urlSession(
        _ session: URLSession,
        webSocketTask: URLSessionWebSocketTask,
        didOpenWithProtocol protocol: String?
    ) {
        Task { @MainActor [weak self] in
            self?.socketDidOpen(webSocketTask)
        }
    }

    nonisolated func urlSession(
        _ session: URLSession,
        webSocketTask: URLSessionWebSocketTask,
        didCloseWith closeCode: URLSessionWebSocketTask.CloseCode,
        reason: Data?
    ) {
        Task { @MainActor [weak self] in
            self?.socketDidClose(webSocketTask, closeCode: closeCode, reason: reason)
        }
    }

    nonisolated func urlSession(
        _ session: URLSession,
        task: URLSessionTask,
        didCompleteWithError error: Error?
    ) {
        guard let error, let webSocketTask = task as? URLSessionWebSocketTask else { return }
        Task { @MainActor [weak self] in
            self?.handleSocketFailure(webSocketTask, error: error)
        }
    }
}
