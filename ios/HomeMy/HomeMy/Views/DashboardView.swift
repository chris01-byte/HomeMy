import SwiftUI
import UIKit

struct DashboardView: View {
    @EnvironmentObject private var controller: RobotController
    @Environment(\.scenePhase) private var scenePhase

    @FocusState private var bridgeFieldFocused: Bool

    var body: some View {
        ZStack {
            RobotPalette.background
                .ignoresSafeArea()

            ScrollView {
                LazyVStack(spacing: 12) {
                    header
                    connectionCard
                    mappingCard
                    stopSection
                    stepsCard
                    logCard
                    safetyFootnote
                }
                .padding(.horizontal, 14)
                .padding(.top, 12)
                .padding(.bottom, 24)
                .frame(maxWidth: 560)
                .frame(maxWidth: .infinity)
            }
            .scrollDismissesKeyboard(.interactively)
        }
        .preferredColorScheme(.dark)
        .task {
            controller.start()
        }
        .onChange(of: scenePhase) { phase in
            switch phase {
            case .active:
                controller.appDidBecomeActive()
            case .background:
                controller.appDidEnterBackground()
            case .inactive:
                break
            @unknown default:
                break
            }
        }
    }

    // MARK: - Kopf und Verbindung

    private var header: some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                Label {
                    Text("HomeMy")
                } icon: {
                    Image(systemName: "cpu")
                        .foregroundStyle(RobotPalette.accent)
                }
                .font(.title2.weight(.bold))

                Text(controller.headline)
                    .font(.subheadline)
                    .foregroundStyle(RobotPalette.muted)
                    .lineLimit(3)
                    .animation(.default, value: controller.headline)
            }
            .frame(maxWidth: .infinity, alignment: .leading)

            VStack(alignment: .trailing, spacing: 6) {
                StatusPill(
                    text: controller.connectionState.label,
                    tone: controller.connectionState.isConnected ? .success : .error
                )
                StatusPill(text: modeLabel, tone: modeTone)
            }
        }
        .accessibilityElement(children: .contain)
    }

    private var connectionCard: some View {
        RobotCard {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Label("Verbindung zum Roboter", systemImage: "network")
                        .font(.caption)
                        .foregroundStyle(RobotPalette.muted)
                    Spacer()
                    Circle()
                        .fill(controller.connectionState.isConnected
                              ? RobotPalette.success
                              : RobotPalette.danger)
                        .frame(width: 8, height: 8)
                    Text(controller.connectionState.isConnected ? "online" : "offline")
                        .font(.caption2)
                        .foregroundStyle(RobotPalette.muted)
                }

                HStack(spacing: 8) {
                    TextField("ws://ROBOTER-IP:9090/", text: $controller.bridgeURL)
                        .keyboardType(.URL)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .submitLabel(.go)
                        .focused($bridgeFieldFocused)
                        .onSubmit {
                            bridgeFieldFocused = false
                            controller.connectNow()
                        }
                        .padding(.horizontal, 12)
                        .frame(minHeight: 48)
                        .background(RobotPalette.surfaceRaised)
                        .overlay {
                            RoundedRectangle(cornerRadius: 9, style: .continuous)
                                .stroke(RobotPalette.line, lineWidth: 1)
                        }
                        .clipShape(RoundedRectangle(cornerRadius: 9, style: .continuous))

                    Button {
                        bridgeFieldFocused = false
                        controller.connectNow()
                    } label: {
                        Group {
                            if case .connecting = controller.connectionState {
                                ProgressView()
                                    .tint(RobotPalette.text)
                            } else {
                                Image(systemName: "power")
                            }
                        }
                        .font(.title3.weight(.semibold))
                        .frame(width: 48, height: 48)
                        .foregroundStyle(RobotPalette.text)
                        .background(RobotPalette.surfaceRaised)
                        .overlay {
                            RoundedRectangle(cornerRadius: 9, style: .continuous)
                                .stroke(RobotPalette.line, lineWidth: 1)
                        }
                        .clipShape(RoundedRectangle(cornerRadius: 9, style: .continuous))
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("Mit dem Roboter verbinden")
                }

                if let error = controller.lastConnectionError {
                    Label(error, systemImage: "exclamationmark.triangle.fill")
                        .font(.caption)
                        .foregroundStyle(RobotPalette.danger)
                        .fixedSize(horizontal: false, vertical: true)
                }

                if controller.connectionState.isConnected {
                    Button("Verbindung trennen") {
                        controller.disconnect()
                    }
                    .font(.caption)
                    .foregroundStyle(RobotPalette.muted)
                }
            }
        }
    }

    // MARK: - Kartiermodus

    private var mappingCard: some View {
        RobotCard {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Label("Kartiermodus", systemImage: "map")
                        .font(.subheadline.weight(.semibold))
                    Spacer()
                    Label(
                        controller.mappingStatusIsFresh ? "live" : "unbekannt",
                        systemImage: controller.mappingStatusIsFresh
                            ? "checkmark.circle.fill"
                            : "clock.badge.exclamationmark"
                    )
                    .font(.caption)
                    .foregroundStyle(
                        controller.mappingStatusIsFresh
                            ? RobotPalette.success
                            : RobotPalette.muted
                    )
                }

                HStack(alignment: .top, spacing: 12) {
                    statusValue(title: "Controller", value: controllerText)
                    Divider().overlay(RobotPalette.line)
                    statusValue(title: "Automatisches Ende", value: autoEndText)
                }

                if controller.mappingModeConfirmedActive {
                    PrimaryActionButton(
                        title: controller.commandIsPending
                            ? "Wird beendet …"
                            : "Kartiermodus beenden",
                        systemImage: "checkmark.circle.fill",
                        enabled: controller.canDisableMappingMode
                    ) {
                        commandHaptic()
                        controller.disableMappingMode()
                    }
                } else {
                    PrimaryActionButton(
                        title: controller.commandIsPending
                            ? "Wird eingeschaltet …"
                            : "Kartiermodus einschalten",
                        systemImage: "gamecontroller.fill",
                        enabled: controller.canEnableMappingMode
                    ) {
                        commandHaptic()
                        controller.enableMappingMode()
                    }
                }

                if let hint = mappingHint {
                    Label(hint, systemImage: "info.circle")
                        .font(.caption)
                        .foregroundStyle(RobotPalette.highlight)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
        }
    }

    private var stopSection: some View {
        VStack(spacing: 7) {
            StopButton(
                pending: controller.stopIsPending,
                enabled: controller.stopIsOffered
            ) {
                emergencyHaptic()
                controller.requestStop()
            }

            HStack(spacing: 5) {
                Image(systemName: stopStatus.icon)
                Text(stopStatus.text)
            }
            .font(.caption)
            .foregroundStyle(stopStatus.color)
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var stepsCard: some View {
        RobotCard {
            VStack(alignment: .leading, spacing: 9) {
                Label("So wird kartiert", systemImage: "list.number")
                    .font(.subheadline.weight(.semibold))

                step(1, "Kartiermodus einschalten.")
                step(2, "Mit dem Controller langsam durch alle Räume fahren, besonders in Kurven.")
                step(3, "Kartiermodus beenden.")
                step(4, "Im Tab „Karte“ die Karte speichern und die Räume einzeichnen.")
            }
        }
    }

    private func step(_ number: Int, _ text: String) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 8) {
            Text("\(number)")
                .font(.caption.weight(.bold).monospacedDigit())
                .foregroundStyle(RobotPalette.accent)
                .frame(width: 16, alignment: .trailing)
            Text(text)
                .font(.caption)
                .foregroundStyle(RobotPalette.muted)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    // MARK: - Log

    private var logCard: some View {
        RobotCard {
            VStack(alignment: .leading, spacing: 9) {
                Label("Log", systemImage: "list.bullet.rectangle")
                    .font(.subheadline.weight(.semibold))

                if controller.logEntries.isEmpty {
                    Text("Noch keine Ereignisse")
                        .font(.caption)
                        .foregroundStyle(RobotPalette.muted)
                        .frame(maxWidth: .infinity, minHeight: 56)
                } else {
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 8) {
                            ForEach(controller.logEntries) { entry in
                                HStack(alignment: .firstTextBaseline, spacing: 7) {
                                    Circle()
                                        .fill(logColor(entry.kind))
                                        .frame(width: 7, height: 7)
                                    Text(entry.date, style: .time)
                                        .font(.caption2.monospacedDigit())
                                        .foregroundStyle(RobotPalette.muted)
                                    Text(entry.message)
                                        .font(.caption)
                                        .foregroundStyle(RobotPalette.muted)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                }
                            }
                        }
                    }
                    .frame(maxHeight: 220)
                }
            }
        }
    }

    private var safetyFootnote: some View {
        Label(
            "Die App sendet keine Fahrbefehle. Der Stopp in der App ist kein Not-Aus "
                + "und ersetzt keinen Halt direkt am Roboter.",
            systemImage: "exclamationmark.shield.fill"
        )
        .font(.caption2)
        .foregroundStyle(RobotPalette.muted)
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 2)
    }

    private func statusValue(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(title)
                .font(.caption2)
                .foregroundStyle(RobotPalette.muted)
            Text(value)
                .font(.subheadline.weight(.semibold))
                .lineLimit(3)
                .frame(maxWidth: .infinity, minHeight: 22, alignment: .topLeading)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    // MARK: - Texte

    private var modeLabel: String {
        guard controller.connectionState.isConnected, controller.mappingStatusIsFresh,
              let snapshot = controller.mappingSnapshot else {
            return "Modus unbekannt"
        }
        return snapshot.state == .active ? "kartiert" : "Kartiermodus aus"
    }

    private var modeTone: StatusPill.Tone {
        guard controller.connectionState.isConnected, controller.mappingStatusIsFresh,
              let snapshot = controller.mappingSnapshot else {
            return .neutral
        }
        return snapshot.state == .active ? .warning : .success
    }

    private var controllerText: String {
        guard controller.mappingStatusIsFresh, let snapshot = controller.mappingSnapshot else {
            return "-"
        }
        return snapshot.controllerConnected ? "verbunden" : "nicht verbunden"
    }

    private var autoEndText: String {
        guard controller.mappingStatusIsFresh, let snapshot = controller.mappingSnapshot else {
            return "-"
        }
        if snapshot.state == .active, let remaining = snapshot.autoEndRemainingSeconds {
            return "in \(MappingModeText.remaining(remaining))"
        }
        return "nach \(MappingModeText.timeout(snapshot.autoEndTimeoutSeconds)) ohne Eingabe"
    }

    private var mappingHint: String? {
        guard controller.connectionState.isConnected else {
            return "Zuerst mit dem Roboter verbinden."
        }
        guard controller.mappingStatusIsFresh, let snapshot = controller.mappingSnapshot else {
            return "Warte auf den Status des Roboters. Solange bleibt nur der Stopp verfügbar."
        }
        if controller.stopIsPending {
            return "Stopp gesendet – warte auf die Bestätigung des Roboters."
        }
        if controller.commandIsPending {
            return "Befehl gesendet – warte auf die Bestätigung des Roboters."
        }
        switch snapshot.state {
        case .active:
            return snapshot.controllerConnected
                ? nil
                : "Der Controller ist nicht verbunden. Der Roboter bleibt stehen, bis er verbunden ist."
        case .off:
            if let blocked = MappingModeText.blockReason(snapshot.enableBlockReason) {
                return blocked
            }
            if let reason = MappingModeText.endReason(snapshot.lastEndReason) {
                return "Zuletzt \(reason)."
            }
            return nil
        }
    }

    private var stopStatus: (text: String, icon: String, color: Color) {
        guard controller.connectionState.isConnected else {
            return (
                "Keine Verbindung – Stopp in der App nicht möglich",
                "wifi.slash",
                RobotPalette.danger
            )
        }
        if controller.stopIsPending {
            return ("Stopp wird bestätigt …", "hourglass", RobotPalette.highlight)
        }
        if controller.mappingModeConfirmedOff {
            return ("Kartiermodus ist aus", "checkmark.shield.fill", RobotPalette.success)
        }
        if controller.mappingModeConfirmedActive {
            return (
                "Hält den Roboter an und beendet den Kartiermodus",
                "exclamationmark.octagon.fill",
                RobotPalette.highlight
            )
        }
        return (
            "Status unbekannt – Stopp bleibt verfügbar",
            "questionmark.circle",
            RobotPalette.highlight
        )
    }

    private func logColor(_ kind: RobotLogKind) -> Color {
        switch kind {
        case .info: RobotPalette.muted
        case .success: RobotPalette.success
        case .warning: RobotPalette.highlight
        case .error, .emergency: RobotPalette.danger
        }
    }

    private func commandHaptic() {
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
    }

    private func emergencyHaptic() {
        UINotificationFeedbackGenerator().notificationOccurred(.error)
    }
}

#Preview {
    DashboardView()
        .environmentObject(RobotController())
}
