import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import TopBar from './components/TopBar';
import Home from './components/Home';
import Login from './components/Login';
import QuestionSection from './components/QuestionSection';
import QueryHistory from './components/QueryHistory';
import './App.css';

function App() {
  const [selectedQueryId, setSelectedQueryId] = useState<string | null>(null);

  const handleQuerySelect = (queryId: string) => {
    setSelectedQueryId(queryId);
  };

  return (
    <Router>
      <div className="app">
        <TopBar />
        <div className="app-layout">
          <aside className="sidebar">
            <QueryHistory onQuerySelect={handleQuerySelect} />
          </aside>
          <main className="main-content">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/home" element={<Home />} />
              <Route 
                path="/" 
                element={<QuestionSection selectedQueryId={selectedQueryId} />} 
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
