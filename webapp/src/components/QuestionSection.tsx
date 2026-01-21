import React, { useState, useEffect } from 'react';
import '../styles/QuestionSection.css';
import { askQuestion, getQueryWithFeedback, ConfigurationResponse } from '../utils/api';
import ReactMarkdown from 'react-markdown';

interface QuestionSectionProps {
  selectedQueryId: string | null;
  onNewQuestionSubmitted: () => void;
}

const QuestionSection: React.FC<QuestionSectionProps> = ({ selectedQueryId, onNewQuestionSubmitted }) => {
  const [query, setQuery] = useState('');
  const [queryId, setQueryId] = useState('');
  const [responses, setResponses] = useState<ConfigurationResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (selectedQueryId) {
      loadQueryData(selectedQueryId);
    }
  }, [selectedQueryId]);

  const handleSearch = async (e: React.FormEvent) => {
    if (!query) {
      return;
    }

    e.preventDefault();
    setResponses([]);
    setLoading(true);

    try {
      const res = await askQuestion(query);
      setResponses(res.responses);
      setQueryId(res.query_id);
      onNewQuestionSubmitted();
    } catch (error) {
      console.error('Failed to ask question:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadQueryData = async (queryId: string) => {
    try {
      setLoading(true);
      const data = await getQueryWithFeedback(queryId);
      setQuery(data.question);
      setQueryId(data.query_id);

      // Handle both old and new format
      if (data.experiment_responses && data.experiment_responses.length > 0) {
        // New format - use experiment_responses directly
        setResponses(data.experiment_responses);
      } else {
        // Old format - convert to single-response array
        setResponses([{
          configuration_id: 'legacy',
          references: data.references || [],
          summary: data.summary || null
        }]);
      }
    } catch (error) {
      console.error('Failed to load query:', error);
    } finally {
      setLoading(false);
    }
  };

  const askForNewQuestion = () => {
    setQuery('');
    setQueryId('');
    setResponses([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch(e);
    }
  };

  return (
    <div className="question-section">
      <h2>Ask about Restoration Projects</h2>

      <div className="action-buttons">
        <button
          className="new-question-button"
          onClick={askForNewQuestion}
        >
          New Question
        </button>
      </div>

      <form className="search-form" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Enter your question"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className="search-input"
        />
        <button type="submit" className="search-button" disabled={loading}>
          {loading ? 'Loading...' : 'Search'}
        </button>
      </form>

      {responses.length > 0 && (
        <div className="responses-section">
          <h3>Answers</h3>
          {responses.map((response, index) => (
            <div key={response.configuration_id} className="response-card">
              <div className="response-header">
                <span className="response-label">Answer {index + 1}</span>
              </div>
              {response.summary ? (
                <div className="response-content">
                  <ReactMarkdown>{response.summary}</ReactMarkdown>
                </div>
              ) : (
                <div className="response-content no-summary">
                  <p>No summary available for this configuration.</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default QuestionSection;
