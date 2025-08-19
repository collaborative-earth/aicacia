import React, { useState, useEffect } from 'react';
import '../../styles/QuestionSection.css';
import { getUserQueryWithFeedback } from '../../utils/api';
import ReactMarkdown from 'react-markdown';

interface Reference {
  url: string;
  title: string;
  score: number;
  chunk: string;
}

interface ReferenceFeedback {
  feedback: number;
  feedback_reason: string;
}

interface Feedback {
  references_feedback: ReferenceFeedback[];
  summary_feedback: number;
  feedback: string;
}

const USEFUL_FEEDBACK = 10;
const NOT_USEFUL_FEEDBACK = 0;
const DONT_KNOW_FEEDBACK = -1;

interface AdminQuestionSectionProps {
  userId: string | null;
  selectedQueryId: string | null;
}

const AdminQuestionSection: React.FC<AdminQuestionSectionProps> = ({ 
  userId, 
  selectedQueryId 
}) => {
  const [query, setQuery] = useState('');
  const [queryId, setQueryId] = useState('');
  const [references, setReferences] = useState<Reference[]>([]);
  const [summary, setSummary] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  useEffect(() => {
    if (userId && selectedQueryId) {
      loadQueryData(userId, selectedQueryId);
    } else {
      // Clear data when no query is selected
      setQuery('');
      setQueryId('');
      setReferences([]);
      setSummary('');
      setFeedback(null);
    }
  }, [userId, selectedQueryId]);

  const loadQueryData = async (userId: string, queryId: string) => {
    try {
      setLoading(true);
      const data = await getUserQueryWithFeedback(userId, queryId);
      setQuery(data.question);
      setReferences(data.references);
      setSummary(data.summary);
      setQueryId(data.query_id);
      setFeedback(data.feedback);
    } catch (error) {
      console.error('Failed to load query:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFeedbackLabel = (feedbackValue: number) => {
    switch (feedbackValue) {
      case USEFUL_FEEDBACK:
        return 'Useful';
      case NOT_USEFUL_FEEDBACK:
        return 'Not Useful';
      case DONT_KNOW_FEEDBACK:
        return "Don't Know";
      default:
        return 'Unknown';
    }
  };

  const getFeedbackColor = (feedbackValue: number) => {
    switch (feedbackValue) {
      case USEFUL_FEEDBACK:
        return '#27ae60';
      case NOT_USEFUL_FEEDBACK:
        return '#e74c3c';
      case DONT_KNOW_FEEDBACK:
        return '#95a5a6';
      default:
        return '#95a5a6';
    }
  };

  if (!userId || !selectedQueryId) {
    return (
      <div className="question-section">
        <h2>Admin Feedback Review</h2>
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          Select a user and a question to view feedback details
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="question-section">
        <h2>Admin Feedback Review</h2>
        <div style={{ textAlign: 'center', padding: '40px' }}>Loading...</div>
      </div>
    );
  }

  return (
    <div className="question-section">
      <h2>Admin Feedback Review</h2>
      
      <div className="admin-query-info" style={{ 
        backgroundColor: '#f8f9fa', 
        padding: '16px', 
        borderRadius: '8px', 
        marginBottom: '20px',
        border: '1px solid #e9ecef'
      }}>
        <h3 style={{ margin: '0 0 8px 0', color: '#495057' }}>Question</h3>
        <p style={{ margin: '0', fontSize: '16px', lineHeight: '1.5' }}>{query}</p>
      </div>

      {summary && (
        <div className="summary-section">
          <h3>Summary</h3>
          <div className="summary-output">
            <ReactMarkdown>{summary}</ReactMarkdown>

            {feedback && (
              <div className="feedback-divider" style={{ marginTop: '16px' }}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  padding: '8px 12px',
                  backgroundColor: '#f8f9fa',
                  borderRadius: '6px',
                  border: '1px solid #e9ecef'
                }}>
                  <strong>Summary Feedback:</strong>
                  <span style={{ 
                    color: getFeedbackColor(feedback.summary_feedback),
                    fontWeight: 'bold'
                  }}>
                    {getFeedbackLabel(feedback.summary_feedback)}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {references.length > 0 && (
        <div className="references-section">
          <h3>References</h3>
          <ul>
            {references.map((ref, index) => (
              <li key={index} className="reference-item">
                <div className="reference-header">
                  <div className="score-badge">
                    <span className="score-label">Score:</span> {ref.score.toFixed(2)}
                  </div>
                  <a href={ref.url} target="_blank" rel="noopener noreferrer" className="reference-title">
                    {ref.title}
                  </a>
                </div>
                <div className="reference-chunk">{ref.chunk}</div>
                
                {feedback && feedback.references_feedback[index] && (
                  <div className="admin-feedback-display" style={{ 
                    marginTop: '12px',
                    padding: '12px',
                    backgroundColor: '#f8f9fa',
                    borderRadius: '6px',
                    border: '1px solid #e9ecef'
                  }}>
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '8px',
                      marginBottom: '8px'
                    }}>
                      <strong>User Feedback:</strong>
                      <span style={{ 
                        color: getFeedbackColor(feedback.references_feedback[index].feedback),
                        fontWeight: 'bold'
                      }}>
                        {getFeedbackLabel(feedback.references_feedback[index].feedback)}
                      </span>
                    </div>
                    {feedback.references_feedback[index].feedback_reason && (
                      <div style={{ 
                        fontStyle: 'italic',
                        color: '#666',
                        lineHeight: '1.4'
                      }}>
                        "{feedback.references_feedback[index].feedback_reason}"
                      </div>
                    )}
                  </div>
                )}
              </li>
            ))}
          </ul>
          
          {feedback && feedback.feedback && (
            <div className="overall-feedback-display" style={{
              marginTop: '20px',
              padding: '16px',
              backgroundColor: '#f8f9fa',
              borderRadius: '8px',
              border: '1px solid #e9ecef'
            }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#495057' }}>Overall Feedback</h4>
              <div style={{ 
                fontStyle: 'italic',
                color: '#666',
                lineHeight: '1.5'
              }}>
                "{feedback.feedback}"
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AdminQuestionSection;
