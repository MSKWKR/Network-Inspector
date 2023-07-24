import * as express from 'express';
import * as path from 'path';
import { ChildProcess, spawn } from 'child_process';
import * as fs from 'fs';
import * as cors from 'cors';

const app: express.Application = express();
const port: number = 5000;
const hostnames: string[] = ["127.0.0.1", "172.16.7.121"];

app.use(cors());

app.get('/trigger', (_, res) => {
    const scriptPath: string = path.resolve(__dirname, '../../utils/scanner.sh');
    const scriptProcess: ChildProcess = spawn('sudo', ['bash', scriptPath]);
    console.log('Status: Script started');

    scriptProcess.on('error', (error: string) => {
        console.error(`Error executing script: ${error}`);
    });

    scriptProcess.stdout?.on('data', (data: string) => {
        const outputLines = data.toString().split('\n');
        for(const line of outputLines) {
            console.log(`${line}\n`);
        }
    });

    scriptProcess.stderr?.on('data', (data: string) => {
        console.error(`${data}`);
    });

    scriptProcess.on('close', () => {
        console.log("Scanner script has finished");
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

hostnames.forEach((hostname) => {
    app.listen(port, hostname, () => {
    console.log(`Server status: up, listening on http://${hostname}:${port}`);
});
});
