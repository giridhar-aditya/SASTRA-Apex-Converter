const { app, BrowserWindow } = require('electron');
require('@electron/remote/main').initialize();
const path = require('path');
const { spawn } = require('child_process');

const isDev = !app.isPackaged;

function createWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    }
  });

  require('@electron/remote/main').enable(win.webContents);

  const indexPath = path.join(__dirname, 'frontend', 'index.html');
  win.loadFile(indexPath);
}

let backendPath;
let args = [];

if (isDev) {
  backendPath = 'python';
  args = [path.join(__dirname, 'backend', 'app.py')];
} else {
  backendPath = path.join(process.resourcesPath, 'app.exe');
}

let backendProcess = spawn(backendPath, args, { shell: true });

backendProcess.stdout.on('data', data => console.log(`Flask: ${data}`));
backendProcess.stderr.on('data', data => console.error(`Flask Error: ${data}`));

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (backendProcess) backendProcess.kill();
  if (process.platform !== 'darwin') app.quit();
});
