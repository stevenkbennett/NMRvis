const { app, BrowserWindow } = require('electron')
const path = require('path')

function createWindow() {
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: path.join(__dirname, 'src/preload.js')
        }
    })

    win.loadFile('src/index.html')
}

// Quit app when all windows are closed on Windows and Linux
app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') app.quit()
})

// Open a window if none are open (macOS)
app.whenReady().then(() => {
    createWindow()

    app.on('activate', function () {
        if (BrowserWindow.getAllWindows().length === 0) createWindow()
    })
})
