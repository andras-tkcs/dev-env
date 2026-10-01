import AppCore
import SwiftUI

/// The app's entry point: one window showing `ContentView`.
@main
struct __MODULE__App: App {
    private let appInfo = AppInfo(infoDictionary: Bundle.main.infoDictionary)

    var body: some Scene {
        WindowGroup {
            ContentView(appInfo: appInfo)
        }
    }
}
