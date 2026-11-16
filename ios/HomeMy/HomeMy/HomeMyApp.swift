import SwiftUI

@main
struct HomeMyApp: App {
    @StateObject private var controller = RobotController()

    var body: some Scene {
        WindowGroup {
            HomeMyRootView()
                .environmentObject(controller)
        }
    }
}
