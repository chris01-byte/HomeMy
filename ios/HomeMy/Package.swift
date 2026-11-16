// swift-tools-version: 6.0
import PackageDescription

// Dieses Paket baut nur die plattformunabhängigen Teile der App (Modelle und
// Protokoll), damit ihre Tests ohne Xcode und ohne Simulator laufen:
//
//     swift test --package-path ios/HomeMy
//
// Die App selbst wird mit HomeMy.xcodeproj gebaut.

#if os(Linux)
// Apples CryptoKit gibt es unter Linux nicht. Für die Tests dort ersetzt ein
// kleines Modul gleichen Namens genau die verwendete SHA-256-Schnittstelle.
let linuxShimTargets: [Target] = [
    .target(name: "CryptoKit", path: "Tools/LinuxShims/CryptoKit")
]
let appDependencies: [Target.Dependency] = ["CryptoKit"]
#else
let linuxShimTargets: [Target] = []
let appDependencies: [Target.Dependency] = []
#endif

let package = Package(
    name: "HomeMyProtocolChecks",
    platforms: [
        .macOS(.v13)
    ],
    targets: [
        .target(
            name: "HomeMy",
            dependencies: appDependencies,
            path: "HomeMy",
            exclude: [
                "Assets.xcassets",
                "Info.plist",
                "PrivacyInfo.xcprivacy",
                "HomeMyApp.swift",
                "Services/RobotController.swift",
                "Services/RobotMapController.swift",
                "Views"
            ],
            sources: [
                "Models/RobotModels.swift",
                "Models/RobotMapModels.swift",
                "Services/RosbridgeProtocol.swift",
                "Services/MapRosbridgeProtocol.swift"
            ]
        ),
        .testTarget(
            name: "HomeMyTests",
            dependencies: ["HomeMy"],
            path: "HomeMyTests"
        )
    ] + linuxShimTargets
)
