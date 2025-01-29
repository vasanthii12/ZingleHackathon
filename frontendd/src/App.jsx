import React, { useState } from 'react';
import { Box, Container, Button, Typography, CircularProgress, Paper, Snackbar, Alert } from '@mui/material';
import ReactFlow, { Controls, Background } from 'reactflow';
import 'reactflow/dist/style.css';
import "./App.css";
import axios from 'axios';

function App() {
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', type: 'info' });
  const [selectedFiles, setSelectedFiles] = useState([]);

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(files);
    
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    setLoading(true);
    try {
      await axios.post('http://localhost:8000/upload-sql/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setNotification({
        open: true,
        message: `Successfully uploaded: ${files.map(f => f.name).join(', ')}`,
        type: 'success'
      });
    } catch (error) {
      setNotification({
        open: true,
        message: `Error uploading files: ${error.message}`,
        type: 'error'
      });
    }
    setLoading(false);
  };

  const createLineage = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/analyze-sql/');
      const descriptions = response.data.results;
      
      // Transform data for graph visualization
      const nodes = [];
      const edges = [];
      const processedTables = new Set();
      const tablePositions = {};
      let xOffset = 100;
      let yOffset = 50;

      // First, create table nodes
      descriptions.forEach((desc) => {
        if (!processedTables.has(desc.table)) {
          const position = { x: xOffset, y: Object.keys(tablePositions).length * 300 };
          tablePositions[desc.table] = position;
          nodes.push({
            id: desc.table,
            data: { label: desc.table },
            position,
            style: {
              background: '#f0f0f0',
              padding: 10,
              borderRadius: 5,
              border: '2px solid #ccc',
              width: 180
            }
          });
          processedTables.add(desc.table);
        }
      });

      // Then add column nodes and edges
      descriptions.forEach((desc, index) => {
        const tablePosition = tablePositions[desc.table];
        nodes.push({
          id: `${desc.table}.${desc.column}`,
          data: { 
            label: desc.column,
            description: desc.description 
          },
          position: {
            x: tablePosition.x + 300,
            y: tablePosition.y + (index % 5) * 60
          },
          style: {
            background: '#e1f5fe',
            padding: 10,
            borderRadius: 5,
            border: '1px solid #81d4fa',
            width: 150
          }
        });

        edges.push({
          id: `${desc.table}-${desc.column}`,
          source: desc.table,
          target: `${desc.table}.${desc.column}`,
          type: 'smoothstep',
          animated: true,
          style: { stroke: '#81d4fa' }
        });
      });

      setGraphData({ nodes, edges });
      setNotification({
        open: true,
        message: 'Lineage graph generated successfully!',
        type: 'success'
      });
    } catch (error) {
      setNotification({
        open: true,
        message: `Error generating lineage: ${error.message}`,
        type: 'error'
      });
    }
    setLoading(false);
  };

  return (
    <Container maxWidth="xl" sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ 
        my: 4, 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center',
        gap: 3
      }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          SQL Lineage Dashboard
        </Typography>

        <Paper elevation={3} sx={{ p: 4, width: '100%', maxWidth: 600, textAlign: 'center' }}>
          <Box sx={{ mb: 3 }}>
            <input
              accept=".sql"
              style={{ display: 'none' }}
              id="sql-file-upload"
              multiple
              type="file"
              onChange={handleFileUpload}
            />
            <label htmlFor="sql-file-upload">
              <Button 
                variant="contained" 
                component="span" 
                sx={{ mr: 2, minWidth: 200 }}
                color="primary"
              >
                Upload SQL Files
              </Button>
            </label>

            <Button 
              variant="contained"
              onClick={createLineage}
              disabled={loading}
              sx={{ minWidth: 200 }}
              color="secondary"
            >
              Create Lineage
            </Button>
          </Box>

          {selectedFiles.length > 0 && (
            <Typography variant="body1" color="textSecondary">
              Selected files: {selectedFiles.map(f => f.name).join(', ')}
            </Typography>
          )}
        </Paper>

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {graphData && (
          <Paper elevation={3} sx={{ width: '100%', height: '70vh', mt: 3 }}>
            <ReactFlow 
              nodes={graphData.nodes}
              edges={graphData.edges}
              fitView
              attributionPosition="bottom-right"
            >
              <Controls />
              <Background />
            </ReactFlow>
          </Paper>
        )}
      </Box>

      <Box sx={{ position: 'relative', width: '100%' }}>
  <Snackbar 
    open={notification.open} 
    autoHideDuration={6000} 
    onClose={() => setNotification({ ...notification, open: false })}
    anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
    sx={{ position: 'absolute', bottom: '-100px' }} 
  >
    <Alert severity={notification.type} sx={{ width: '100%' }}>
      {notification.message}
    </Alert>
  </Snackbar>
</Box>

    </Container>
  );
}

export default App;