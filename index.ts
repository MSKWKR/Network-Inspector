import * as http from 'http';
import * as path from 'path';
import { spawn } from 'child_process';

const server = http.createServer((req, res) => {
  if (req.url === '/trigger' && req.method === 'GET') {
    const scriptPath = path.resolve(__dirname, 'scanner.sh');
    const scriptProcess = spawn('sudo', ['bash', scriptPath]);

    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
      });
  
    // Send initial SSE message to notify the client that the process has started
    res.write('Scanner script has started\n\n');

    scriptProcess.on('error', (error) => {
      console.error(`Error executing script: ${error}`);
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('Internal Server Error');
    });

    scriptProcess.stdout.on('data', (data) => {
        const outputLines = data.toString().split('\n');
        for(const line of outputLines) {
            res.write(`${line}\n`)
        }
    });

    scriptProcess.stderr.on('data', (data) => {
      console.error(`${data}`);
    });

    scriptProcess.on('close', (code) => {
      res.write(`Scanner script has finished (Exit code: ${code})`)
    })

  } 
  else {
    res.writeHead(404, { 'Content-Type': 'text/plain' });
    res.end('Not Found');
  }
});

const port = 80;
const hostname = '172.16.7.121'

server.listen(port, hostname, () => {
  console.log(`Server listening on port ${port}`);
});

// Handle termination signals
process.on('SIGINT', () => {
  shutdownServer();
});

process.on('SIGTERM', () => {
  shutdownServer();
});

function shutdownServer() {
  server.close(() => {
    console.log('Server closed gracefully');
    process.exit(0);
  });
}
