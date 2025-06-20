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
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  const handleQuerySelect = (queryId: string) => {
    setSelectedQueryId(queryId);
  };

  const handleNewQuestionSubmitted = () => {
    // Trigger a refresh of the query history
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <Router>
      <div className="app">
        <TopBar />
        <div className="app-layout">
          <aside className="sidebar">
            <QueryHistory 
              onQuerySelect={handleQuerySelect} 
              refreshTrigger={refreshTrigger}
            />
          </aside>
          <main className="main-content">
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/home" element={<Home />} />
              <Route 
                path="/" 
                element={
                  <QuestionSection 
                    selectedQueryId={selectedQueryId} 
                    onNewQuestionSubmitted={handleNewQuestionSubmitted}
                  />
                } 
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
