// Minimal stand-in for Apple's CryptoKit so that the protocol and map tests
// can run with `swift test` on Linux. It is compiled only on Linux (see
// Package.swift). On Apple platforms the app links the system CryptoKit.
//
// Only the SHA-256 surface used by the app is provided.

import Foundation

public struct SHA256Digest: Sequence, Equatable, Sendable {
    fileprivate let bytes: [UInt8]

    public func makeIterator() -> Array<UInt8>.Iterator {
        bytes.makeIterator()
    }
}

public struct SHA256: Sendable {
    private static let roundConstants: [UInt32] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    ]

    private var state: [UInt32] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    ]
    private var buffer: [UInt8] = []
    private var messageLength: UInt64 = 0

    public init() {
        buffer.reserveCapacity(64)
    }

    public mutating func update(data: Data) {
        messageLength &+= UInt64(data.count)
        for byte in data {
            buffer.append(byte)
            if buffer.count == 64 {
                compress(buffer)
                buffer.removeAll(keepingCapacity: true)
            }
        }
    }

    public func finalize() -> SHA256Digest {
        var copy = self
        let bitLength = copy.messageLength &* 8
        copy.buffer.append(0x80)
        if copy.buffer.count > 56 {
            copy.buffer.append(contentsOf: [UInt8](repeating: 0, count: 64 - copy.buffer.count))
            copy.compress(copy.buffer)
            copy.buffer.removeAll(keepingCapacity: true)
        }
        copy.buffer.append(contentsOf: [UInt8](repeating: 0, count: 56 - copy.buffer.count))
        for shift in stride(from: 56, through: 0, by: -8) {
            copy.buffer.append(UInt8(truncatingIfNeeded: bitLength >> UInt64(shift)))
        }
        copy.compress(copy.buffer)

        var bytes: [UInt8] = []
        bytes.reserveCapacity(32)
        for word in copy.state {
            bytes.append(UInt8(truncatingIfNeeded: word >> 24))
            bytes.append(UInt8(truncatingIfNeeded: word >> 16))
            bytes.append(UInt8(truncatingIfNeeded: word >> 8))
            bytes.append(UInt8(truncatingIfNeeded: word))
        }
        return SHA256Digest(bytes: bytes)
    }

    public static func hash(data: Data) -> SHA256Digest {
        var hasher = SHA256()
        hasher.update(data: data)
        return hasher.finalize()
    }

    private mutating func compress(_ block: [UInt8]) {
        var words = [UInt32](repeating: 0, count: 64)
        for index in 0..<16 {
            let offset = index * 4
            words[index] = UInt32(block[offset]) << 24 |
                UInt32(block[offset + 1]) << 16 |
                UInt32(block[offset + 2]) << 8 |
                UInt32(block[offset + 3])
        }
        for index in 16..<64 {
            let w15 = words[index - 15]
            let w2 = words[index - 2]
            let sigma0 = Self.rotateRight(w15, 7) ^ Self.rotateRight(w15, 18) ^ (w15 >> 3)
            let sigma1 = Self.rotateRight(w2, 17) ^ Self.rotateRight(w2, 19) ^ (w2 >> 10)
            words[index] = words[index - 16] &+ sigma0 &+ words[index - 7] &+ sigma1
        }

        var a = state[0], b = state[1], c = state[2], d = state[3]
        var e = state[4], f = state[5], g = state[6], h = state[7]

        for index in 0..<64 {
            let sum1 = Self.rotateRight(e, 6) ^ Self.rotateRight(e, 11) ^ Self.rotateRight(e, 25)
            let choice = (e & f) ^ (~e & g)
            let temp1 = h &+ sum1 &+ choice &+ Self.roundConstants[index] &+ words[index]
            let sum0 = Self.rotateRight(a, 2) ^ Self.rotateRight(a, 13) ^ Self.rotateRight(a, 22)
            let majority = (a & b) ^ (a & c) ^ (b & c)
            let temp2 = sum0 &+ majority
            h = g
            g = f
            f = e
            e = d &+ temp1
            d = c
            c = b
            b = a
            a = temp1 &+ temp2
        }

        state[0] = state[0] &+ a
        state[1] = state[1] &+ b
        state[2] = state[2] &+ c
        state[3] = state[3] &+ d
        state[4] = state[4] &+ e
        state[5] = state[5] &+ f
        state[6] = state[6] &+ g
        state[7] = state[7] &+ h
    }

    private static func rotateRight(_ value: UInt32, _ amount: UInt32) -> UInt32 {
        (value >> amount) | (value << (32 - amount))
    }
}
