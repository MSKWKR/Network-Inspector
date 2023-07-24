"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var express = require("express");
var path = require("path");
var child_process_1 = require("child_process");
var fs = require("fs");
var cors = require("cors");
var app = express();
var port = 5000;
var hostnames = ["127.0.0.1", "172.16.7.121"];
app.use(cors());
app.get('/trigger', function (_, res) {
    var _a, _b;
    var scriptPath = path.resolve(__dirname, '../../utils/scanner.sh');
    var scriptProcess = (0, child_process_1.spawn)('sudo', ['bash', scriptPath]);
    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    });
    res.write('Scanner script has started\n\n');
    console.log('Script started');
    scriptProcess.on('error', function (error) {
        console.error("Error executing script: ".concat(error));
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('Internal Server Error');
    });
    (_a = scriptProcess.stdout) === null || _a === void 0 ? void 0 : _a.on('data', function (data) {
        var outputLines = data.toString().split('\n');
        for (var _i = 0, outputLines_1 = outputLines; _i < outputLines_1.length; _i++) {
            var line = outputLines_1[_i];
            res.write("".concat(line, "\n"));
        }
    });
    (_b = scriptProcess.stderr) === null || _b === void 0 ? void 0 : _b.on('data', function (data) {
        console.error("".concat(data));
    });
    scriptProcess.on('close', function () {
        console.log("Scanner script has finished");
        res.end("Scanner script has finished");
    });
});
app.get('/api/files', function (req, res) {
    var directoryPath = path.resolve(__dirname, '../../json');
    fs.readdir(directoryPath, function (err, files) {
        if (err) {
            console.error('Error reading directory:', err);
            return res.status(500).json({ error: 'Internal Server Error' });
        }
        var fileData = files.map(function (file) {
            return {
                name: file,
                url: "/api/files/".concat(file)
            };
        });
        res.json(fileData);
    });
});
app.get('/api/files/:filename', function (req, res) {
    var fileName = req.params.filename;
    var filePath = path.resolve(__dirname, "../../json/".concat(fileName));
    fs.readFile(filePath, 'utf-8', function (err, data) {
        if (err) {
            console.error('Error reading file:', err);
            return res.status(500).json({ error: 'Internal Server Error' });
        }
        res.send(data);
    });
});
hostnames.forEach(function (hostname) {
    app.listen(port, hostname, function () {
        console.log("Server status: up, listening on http://".concat(hostname, ":").concat(port));
    });
});
