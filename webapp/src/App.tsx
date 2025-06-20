import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import TopBar from './components/TopBar';
import Login from './components/Login';
import QuestionSection from './components/QuestionSection';
import QueryHistory from './components/QueryHistory';
import { getToken, removeToken } from './utils/tokens';
import { getUserInfo } from './utils/api';
import './App.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!getToken());
  const [selectedQueryId, setSelectedQueryId] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  useEffect(() => {
    const verifyUser = async () => {
      if (isLoggedIn) {
        try {
          await getUserInfo();
        } catch (error) {
          console.error('User verification failed:', error);
          removeToken();
          setIsLoggedIn(false);
        }
      }
    };
    verifyUser();
  }, [isLoggedIn]);

  const handleLoginSuccess = () => {
    setIsLoggedIn(true);
    setRefreshTrigger(p => p + 1);
  };

  const handleLogout = () => {
    removeToken();
    setIsLoggedIn(false);
  };

  const handleQuerySelect = (queryId: string) => {
    setSelectedQueryId(queryId);
  };

  const handleNewQuestionSubmitted = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <Router>
      <div className="app">
        <TopBar isLoggedIn={isLoggedIn} onLogout={handleLogout} />
        <div className="app-layout">
          {isLoggedIn && (
            <aside className="sidebar">
              <QueryHistory 
                onQuerySelect={handleQuerySelect} 
                refreshTrigger={refreshTrigger}
              />
            </aside>
          )}
          <main className={`main-content ${!isLoggedIn ? 'full-width' : ''}`}>
            <Routes>
              {!isLoggedIn ? (
                <>
                  <Route path="/login" element={<Login onLoginSuccess={handleLoginSuccess} />} />
                  <Route path="*" element={<Navigate to="/login" replace />} />
                </>
              ) : (
                <>
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
                </>
              )}
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
