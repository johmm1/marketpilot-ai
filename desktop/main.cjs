const { app, BrowserWindow, shell } = require('electron');
const { URL } = require('node:url');

function getAppUrl() {
  const raw = process.env.MARKETPILOT_WEB_URL || 'http://localhost:3000';
  let parsed;
  try {
    parsed = new URL(raw);
  } catch {
    throw new Error('MARKETPILOT_WEB_URL must be a valid URL.');
  }
  if (parsed.protocol !== 'https:' && parsed.hostname !== 'localhost' && parsed.hostname !== '127.0.0.1') {
    throw new Error('The desktop app requires HTTPS except for local development.');
  }
  return parsed.toString();
}

function createWindow() {
  const target = getAppUrl();
  const mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 900,
    minHeight: 650,
    backgroundColor: '#080d18',
    title: 'MARKETPILOT AI',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true
    }
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const parsed = new URL(url);
      if (parsed.protocol === 'https:') shell.openExternal(url);
    } catch {}
    return { action: 'deny' };
  });

  mainWindow.webContents.on('will-navigate', (event, url) => {
    try {
      const next = new URL(url);
      const base = new URL(target);
      if (next.origin !== base.origin) event.preventDefault();
    } catch {
      event.preventDefault();
    }
  });

  mainWindow.loadURL(target);
}

app.whenReady().then(() => {
  try {
    createWindow();
  } catch (error) {
    console.error(error);
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
