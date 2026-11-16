import SwiftUI

struct HomeMyRootView: View {
    var body: some View {
        TabView {
            DashboardView()
                .tabItem {
                    Label("Kartieren", systemImage: "gamecontroller.fill")
                }

            RobotMapView()
                .tabItem {
                    Label("Karte", systemImage: "map.fill")
                }
        }
        .tint(RobotPalette.accent)
        .preferredColorScheme(.dark)
    }
}

#Preview {
    HomeMyRootView()
        .environmentObject(RobotController())
}
