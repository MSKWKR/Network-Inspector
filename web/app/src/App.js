import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link, useParams } from 'react-router-dom';

const FileDisplay = () => {
  const [files, setFiles] = useState([]);

  useEffect(() => {
    // Make an API call to fetch the list of files from Node.js server
    fetch('http://127.0.0.1:5000/api/files')
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
    fetch(`http://127.0.0.1:5000/api/files/${filename}`)
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
      </Routes>
    </Router>
  );
};

export default App;
