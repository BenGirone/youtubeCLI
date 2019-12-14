const {app, BrowserWindow} = require('electron');
const express = require('express');
const http = require( "http" );

app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');

const server = express();
const http_server = http.createServer( server ).listen( 8081 );
const http_io = require( "socket.io" )( http_server );

let youtube;

function log(message) {
    youtube.webContents.send('log', '<<server>> ' + message);
}

function createYoutube() {
    // Create the browser window.
    youtube = new BrowserWindow({
        width: 400,
        height: 400,
        frame: false,
        show: false,
        webPreferences: {
            nodeIntegration: true,
            webSecurity: false
        },
    });

    youtube.loadFile('index.html');

    // Open the DevTools.
    // youtube.webContents.openDevTools();

    // Emitted when the window is closed.
    youtube.on('closed', function () {
        youtube = null;
    });

    log('Linked to server');
}

app.on('ready', ()=> {
    createYoutube();
});

http_io.on( "connection", (httpsocket) => {
    httpsocket.on('video', (id) => {
        log('got video ' + id);
        
        youtube.webContents.send('video', id);
    });
    
    httpsocket.on('playlist', (id) => {
        log('got playlist ' + id);
    
        youtube.webContents.send('playlist', id);
    });
    
    httpsocket.on('control', (data) => {
        const dataParsed = JSON.parse(data);
        const command = dataParsed.command;
        const param = dataParsed.param;
    
        if (param) {
            youtube.webContents.send(command, param);
        } else {
            youtube.webContents.send(command);
        }
    });

    httpsocket.once('disconnect', () => {
        youtube.close();
        http_io.close();
        http_server.close();
        app.quit();
    });
});