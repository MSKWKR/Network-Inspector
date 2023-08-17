"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var express = require("express");
var path = require("path");
var child_process_1 = require("child_process");
var fs = require("fs");
var cors = require("cors");
var app = express();
var port = 80;
var hostnames = ["localhost"];
app.use(cors());
app.get('/api/trigger', function (_, res) {
    var _a, _b;
    var scriptPath = path.resolve(__dirname, '../../utils/scanner.sh');
    var scriptProcess = (0, child_process_1.spawn)('bash', [scriptPath]);
    console.log('Script started');
    scriptProcess.on('error', function (error) {
        console.error("Error executing script: ".concat(error));
    });
    (_a = scriptProcess.stdout) === null || _a === void 0 ? void 0 : _a.on('data', function (data) {
        var outputLines = data.toString().split('\n');
        for (var _i = 0, outputLines_1 = outputLines; _i < outputLines_1.length; _i++) {
            var line = outputLines_1[_i];
            console.log("".concat(line));
        }
    });
    (_b = scriptProcess.stderr) === null || _b === void 0 ? void 0 : _b.on('data', function (data) {
        console.error("".concat(data));
    });
    scriptProcess.on('close', function () {
        console.log("Scanner script has finished");
    });
});
app.get('/api/files', function (_, res) {
    var directoryPath = path.resolve(__dirname, '../../json');
    fs.readdir(directoryPath, function (err, files) {
        if (err) {
            console.error('Error reading directory:', err);
            return res.status(500).json({ error: 'Internal Server Error' });
        }
        var fileList = files.map(function (file) {
            return {
                name: file,
                url: "/api/files/".concat(file)
            };
        });
        res.json(fileList);
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
