import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import TopBar from './components/TopBar';
import Login from './components/Login';
import QuestionSection from './components/QuestionSection';
import QueryHistory from './components/QueryHistory';
import AdminFeedbacks from './components/admin/AdminFeedbacks';
import { getToken, removeToken } from './utils/tokens';
import { getUserInfo } from './utils/api';
import './App.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(!!getToken());
  const [selectedQueryId, setSelectedQueryId] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);
  const [userInfo, setUserInfo] = useState<{email: string, user_id: string, is_admin: boolean} | null>(null);

  useEffect(() => {
    const verifyUser = async () => {
      if (isLoggedIn) {
        try {
          const userInfoResponse = await getUserInfo();
          setUserInfo(userInfoResponse);
        } catch (error) {
          console.error('User verification failed:', error);
          removeToken();
          setIsLoggedIn(false);
          setUserInfo(null);
        }
      } else {
        setUserInfo(null);
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
    setUserInfo(null);
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
        <TopBar isLoggedIn={isLoggedIn} userInfo={userInfo} onLogout={handleLogout} />
        <div className="app-layout">
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
                    <>
                      <aside className="sidebar">
                        <QueryHistory 
                          onQuerySelect={handleQuerySelect} 
                          refreshTrigger={refreshTrigger}
                        />
                      </aside>
                      <main className="main-content">
                        <QuestionSection 
                          selectedQueryId={selectedQueryId} 
                          onNewQuestionSubmitted={handleNewQuestionSubmitted}
                        />
                      </main>
                    </>
                  } 
                />
                <Route 
                  path="/admin/feedbacks" 
                  element={
                    userInfo?.is_admin ? (
                      <AdminFeedbacks />
                    ) : (
                      <Navigate to="/" replace />
                    )
                  } 
                />
                <Route path="*" element={<Navigate to="/" replace />} />
              </>
            )}
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
