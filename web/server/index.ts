import * as express from 'express';
import * as path from 'path';
import { ChildProcess, spawn } from 'child_process';
import * as fs from 'fs';
import * as cors from 'cors';

const app: express.Application = express();
const port: number = 5000;
const hostname: string = "172.16.7.121";

app.use(cors());

app.get('/trigger', (_, res) => {
    const scriptPath: string = path.resolve(__dirname, '../../utils/scanner.sh');
    const scriptProcess: ChildProcess = spawn('sudo', ['bash', scriptPath]);

    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    });
    res.write('Scanner script has started\n\n');
    console.log('Script started');

    scriptProcess.on('error', (error: string) => {
        console.error(`Error executing script: ${error}`);
        res.writeHead(500, { 'Content-Type': 'text/plain' });
        res.end('Internal Server Error');
    });

    scriptProcess.stdout?.on('data', (data: string) => {
        const outputLines = data.toString().split('\n');
        for(const line of outputLines) {
            res.write(`${line}\n`)
        }
    });

    scriptProcess.stderr?.on('data', (data: string) => {
        console.error(`${data}`);
    });

    scriptProcess.on('close', () => {
        console.log("Scanner script has finished");
        res.end("Scanner script has finished");
    });

});

app.get('/api/files', (req, res) => {
    const directoryPath: string = path.resolve(__dirname, '../../json');

    fs.readdir(directoryPath, (err, files) => {
        if (err) {
            console.error('Error reading directory:', err);
            return res.status(500).json({error: 'Internal Server Error'});
        }

        const fileData = files.map((file) => {
            return {
                name: file,
                url: `/api/files/${file}`
            };
        });

        res.json(fileData);
    })

})

app.get('/api/files/:filename', (req, res) => {
    const fileName: string = req.params.filename;
    const filePath: string = path.resolve(__dirname, `../../json/${fileName}`)

    fs.readFile(filePath, 'utf-8', (err, data) => {
        if (err) {
            console.error('Error reading file:', err);
            return res.status(500).json({error: 'Internal Server Error'});
        }

        res.send(data);
    });
});


app.listen(port, hostname, () => {
    console.log("server status: up");
});