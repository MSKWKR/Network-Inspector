import express from 'express';
import * as path from 'path';
import { ChildProcess, spawn } from 'child_process';

const app: express.Application = express();

const port: number = 80;
const hostname: string = "172.16.7.121";


app.get('/trigger', (_, res) => {
    const scriptPath: string = path.resolve(__dirname, 'scanner.sh');
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

app.listen(port, hostname, () => {
    console.log("server status: up");
});