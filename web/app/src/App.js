import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link, useParams } from 'react-router-dom';

const Trigger = () => {
  useEffect(() => {
    // Establish the SSE connection
    const eventSource = new EventSource('/api/trigger');

    eventSource.onmessage = () => {
      console.log('Trigger called');
    };

    eventSource.onerror = (event) => {
      console.error('Trigger error:', event);
    };

    // Clean up the SSE connection when the component unmounts
    return () => {
      eventSource.close();
    };
  }, []);

  // The Trigger component doesn't need to return anything specific
  return (
    <div>
      <h1>Scanning network</h1>
    </div>
  );
};

const FileDisplay = () => {
  const [files, setFiles] = useState([]);

  useEffect(() => {
    // Make an API call to fetch the list of files from Node.js server
    fetch('/api/files')
      .then((response) => response.json())
      .then((data) => {
        setFiles(data);
      })
      .catch((error) => {
        console.error('Error fetching files:', error);
      });
  }, []);

  return (
    <div>
      <h1>JSON List</h1>
      <ul>
        {files.map((file, index) => (
          <li key={index}>
            {/* Use React Router Link to navigate to FileDetails component */}
            <Link to={`/files/${file.name}`}>{file.name}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
};

const FileDetails = () => {
  const { filename } = useParams();
  const [fileContent, setFileContent] = useState('');

  useEffect(() => {
    // Make an API call to fetch the file content
    fetch(`/api/files/${filename}`)
      .then((response) => response.json())
      .then((data) => {
        // Pretty print the JSON content with indentation of 2 spaces
        const prettyJSON = JSON.stringify(data, null, 2);
        setFileContent(prettyJSON);
      })
      .catch((error) => {
        console.error('Error fetching file content:', error);
      });
  }, [filename]);

  return (
    <div>
      <h1>{filename}</h1>
      <pre>{fileContent}</pre>
    </div>
  );
};

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<FileDisplay />} />
        <Route path="/files/:filename" element={<FileDetails />} />
        <Route path="/trigger" element={<Trigger />} />
      </Routes>
    </Router>
  );
};

export default App;
