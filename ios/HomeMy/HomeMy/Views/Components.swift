import SwiftUI

enum RobotPalette {
    static let background = Color(hex: 0x0F1419)
    static let surface = Color(hex: 0x17202A)
    static let surfaceRaised = Color(hex: 0x1F2A35)
    static let line = Color(hex: 0x334251)
    static let text = Color(hex: 0xF4F7FB)
    static let muted = Color(hex: 0xAAB7C4)
    static let accent = Color(hex: 0x4FB3A5)
    static let highlight = Color(hex: 0xF2B84B)
    static let danger = Color(hex: 0xE05A47)
    static let dangerDark = Color(hex: 0x6E1D13)
    static let success = Color(hex: 0x4EB06A)
}

extension Color {
    init(hex: UInt32) {
        self.init(
            red: Double((hex >> 16) & 0xFF) / 255,
            green: Double((hex >> 8) & 0xFF) / 255,
            blue: Double(hex & 0xFF) / 255
        )
    }
}

struct RobotCard<Content: View>: View {
    @ViewBuilder let content: Content

    var body: some View {
        content
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(RobotPalette.surface)
            .overlay {
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(RobotPalette.line, lineWidth: 1)
            }
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }
}

struct StatusPill: View {
    enum Tone {
        case neutral
        case success
        case warning
        case error

        var color: Color {
            switch self {
            case .neutral: RobotPalette.muted
            case .success: RobotPalette.success
            case .warning: RobotPalette.highlight
            case .error: RobotPalette.danger
            }
        }
    }

    let text: String
    let tone: Tone

    var body: some View {
        Text(text)
            .font(.caption.weight(.medium))
            .lineLimit(1)
            .foregroundStyle(tone.color)
            .padding(.horizontal, 10)
            .frame(minHeight: 27)
            .background(tone.color.opacity(0.08))
            .overlay {
                Capsule().stroke(tone.color.opacity(0.72), lineWidth: 1)
            }
            .clipShape(Capsule())
    }
}

struct PrimaryActionButton: View {
    let title: String
    let systemImage: String
    let enabled: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Label(title, systemImage: systemImage)
                .font(.body.weight(.bold))
                .frame(maxWidth: .infinity, minHeight: 50)
                .foregroundStyle(Color(hex: 0x061412))
                .background(RobotPalette.accent)
                .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
        }
        .buttonStyle(.plain)
        .disabled(!enabled)
        .opacity(enabled ? 1 : 0.42)
    }
}

struct StopButton: View {
    let pending: Bool
    let enabled: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 10) {
                if pending {
                    ProgressView()
                        .tint(.white)
                } else {
                    Image(systemName: "stop.fill")
                }
                Text("STOPP")
                    .lineLimit(1)
            }
            .font(.headline.weight(.heavy))
            .tracking(1.1)
            .frame(maxWidth: .infinity, minHeight: 64)
            .foregroundStyle(.white)
            .background(RobotPalette.danger)
            .overlay {
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .stroke(Color.white.opacity(0.3), lineWidth: 2)
            }
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
        .buttonStyle(.plain)
        .disabled(!enabled || pending)
        .opacity(enabled || pending ? 1 : 0.48)
        .accessibilityLabel("Stopp")
        .accessibilityHint("Hält den Roboter an und beendet den Kartiermodus.")
    }
}
