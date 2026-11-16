import Foundation

/// Topics der Steuerverbindung laut `contracts/api/app-bridge.md`.
enum RosbridgeTopics {
    static let mappingModeCommand = "/homemy/mapping_mode/command_json"
    static let mappingModeStatus = "/homemy/mapping_mode/status_json"
}

enum RosbridgeEvent: Equatable {
    case mappingModeStatus(MappingModeStatus)
}

enum RosbridgeProtocolError: LocalizedError, Equatable {
    case invalidTextFrame
    case invalidMappingModeStatus
    case invalidCommand

    var errorDescription: String? {
        switch self {
        case .invalidTextFrame:
            return "Ungültiger rosbridge-Datenrahmen."
        case .invalidMappingModeStatus:
            return "Der Kartiermodus-Status ist unvollständig oder ungültig."
        case .invalidCommand:
            return "Der Befehl enthält ungültige Werte."
        }
    }
}

enum RosbridgeProtocol {
    private static let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        return encoder
    }()

    private static let decoder = JSONDecoder()

    static func setupFrames() throws -> [String] {
        try [
            encode(AdvertiseFrame(
                op: "advertise",
                topic: RosbridgeTopics.mappingModeCommand,
                type: "std_msgs/String"
            )),
            encode(SubscribeFrame(
                op: "subscribe",
                topic: RosbridgeTopics.mappingModeStatus,
                type: "std_msgs/String"
            ))
        ]
    }

    static func mappingModeCommandFrame(
        _ kind: MappingModeCommandKind,
        requestID: String
    ) throws -> String {
        guard validRequestID(requestID) else {
            throw RosbridgeProtocolError.invalidCommand
        }
        let commandData = try encoder.encode(MappingModeCommand(
            command: kind.rawValue,
            requestID: requestID
        ))
        guard let commandJSON = String(data: commandData, encoding: .utf8) else {
            throw RosbridgeProtocolError.invalidTextFrame
        }
        return try encode(StringPublishFrame(
            op: "publish",
            topic: RosbridgeTopics.mappingModeCommand,
            msg: .init(data: commandJSON)
        ))
    }

    static func decodeEvent(from text: String) throws -> RosbridgeEvent? {
        guard let data = text.data(using: .utf8) else {
            throw RosbridgeProtocolError.invalidTextFrame
        }
        let frame: IncomingFrame
        do {
            frame = try decoder.decode(IncomingFrame.self, from: data)
        } catch {
            throw RosbridgeProtocolError.invalidTextFrame
        }
        guard frame.op == "publish",
              frame.topic == RosbridgeTopics.mappingModeStatus else {
            return nil
        }
        guard let statusJSON = frame.msg?.data,
              let statusData = statusJSON.data(using: .utf8) else {
            throw RosbridgeProtocolError.invalidMappingModeStatus
        }
        do {
            let status = try decoder.decode(MappingModeStatus.self, from: statusData)
            guard status.isValid else {
                throw RosbridgeProtocolError.invalidMappingModeStatus
            }
            return .mappingModeStatus(status)
        } catch {
            throw RosbridgeProtocolError.invalidMappingModeStatus
        }
    }

    /// Gleiche Regel wie im Kartenprotokoll und im Backend: 1 bis 64 Zeichen,
    /// Beginn mit Buchstabe oder Ziffer, danach zusätzlich `_`, `.`, `:`, `-`.
    static func validRequestID(_ value: String) -> Bool {
        guard !value.isEmpty, value.count <= 64,
              let first = value.utf8.first,
              (65...90).contains(first) || (97...122).contains(first) ||
                (48...57).contains(first) else {
            return false
        }
        return value.utf8.count == value.count && value.utf8.allSatisfy { byte in
            (65...90).contains(byte) || (97...122).contains(byte) ||
                (48...57).contains(byte) || byte == 95 || byte == 46 ||
                byte == 58 || byte == 45
        }
    }

    private static func encode<Value: Encodable>(_ value: Value) throws -> String {
        let data = try encoder.encode(value)
        guard let text = String(data: data, encoding: .utf8) else {
            throw RosbridgeProtocolError.invalidTextFrame
        }
        return text
    }
}

private struct AdvertiseFrame: Encodable {
    let op: String
    let topic: String
    let type: String
}

private struct SubscribeFrame: Encodable {
    let op: String
    let topic: String
    let type: String
}

private struct MappingModeCommand: Encodable {
    let command: String
    let requestID: String

    enum CodingKeys: String, CodingKey {
        case command
        case requestID = "request_id"
    }
}

private struct StringPublishFrame: Encodable {
    struct Message: Encodable {
        let data: String
    }

    let op: String
    let topic: String
    let msg: Message
}

private struct IncomingFrame: Decodable {
    struct Message: Decodable {
        let data: String?

        private enum CodingKeys: String, CodingKey {
            case data
        }

        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)
            // Fremde Topics dürfen andere Datentypen tragen; nur ein String
            // ist für den Kartiermodus-Status gültig.
            data = try? container.decode(String.self, forKey: .data)
        }
    }

    let op: String?
    let topic: String?
    let msg: Message?

    private enum CodingKeys: String, CodingKey {
        case op
        case topic
        case msg
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        op = try container.decodeIfPresent(String.self, forKey: .op)
        topic = try container.decodeIfPresent(String.self, forKey: .topic)
        // `/map` und andere Topics tragen Objekte ohne `data`-String.
        msg = try? container.decodeIfPresent(Message.self, forKey: .msg)
    }
}
