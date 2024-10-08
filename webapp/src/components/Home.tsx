import React, { useState } from 'react';
import TopBar from './TopBar';
import '../styles/Home.css';
import { askQuestion, submitFeedback } from '../utils/api';

const Home: React.FC = () => {
  const [query, setQuery] = useState('');
  const [queryId, setQueryId] = useState('');
  const [references, setReferences] = useState<{ url: string; title: string; }[]>(
    []
  );
  const [summary, setSummary] = useState<string>('');
  const [referencesFeedback, setReferencesFeedback] = useState<number[]>(
    []
  );
  const [overallFeedback, setOverallFeedback] = useState<string>('');

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await askQuestion(query);

    setReferences(res.references);
    setReferencesFeedback(res.references.map(() => 10));
    setSummary(res.summary);
    setQueryId(res.query_id);
  };

  const handleFeedbackChange = (index: number, useful: boolean) => {
    const updatedReferencesFeedback = [...referencesFeedback];
    updatedReferencesFeedback[index] = useful ? 10 : 0;
    setReferencesFeedback(updatedReferencesFeedback);
  };

  const handleOverallFeedbackChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setOverallFeedback(e.target.value);
  };

  const handleSubmitFeedback = async () => {
    // Handle feedback submission logic here; e.g., send feedback to your API
    await submitFeedback({
      query_id: queryId,
      references_feedback: referencesFeedback,
      feedback: overallFeedback,
    })
  };

  return (
    <div className="home-page">
      <TopBar />
      <div className="home-content">
        <div className="search-container">
          <h2>Ask about Restoration Projects</h2>
          <form className="search-form" onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="Enter your question"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="search-input"
            />
            <button type="submit" className="search-button">
              Search
            </button>
          </form>
        </div>
        {summary && (
          <div className="summary-section">
            <h3>Summary</h3>
            <p>{summary}</p>
          </div>
        )}
        {references.length > 0 && (
          <div className="references-section">
            <h3>References</h3>
            <ul>
              {references.map((ref, index) => (
                <li key={index} className="reference-item">
                  <a href={ref.url} target="_blank" rel="noopener noreferrer">
                    {ref.title}
                  </a>
                  <div className="feedback-options">
                    <label>
                      <input
                        type="radio"
                        name={`feedback-${index}`}
                        value="useful"
                        checked={referencesFeedback[index] === 10}
                        onChange={() => handleFeedbackChange(index, true)}
                      />
                      Useful
                    </label>
                    <label>
                      <input
                        type="radio"
                        name={`feedback-${index}`}
                        value="not-useful"
                        checked={referencesFeedback[index] === 0}
                        onChange={() => handleFeedbackChange(index, false)}
                      />
                      Not Useful
                    </label>
                  </div>
                </li>
              ))}
            </ul>
            <div className="overall-feedback-section">
              <textarea
                placeholder="Overall feedback"
                value={overallFeedback}
                onChange={handleOverallFeedbackChange}
                className="overall-feedback-input"
              ></textarea>
              <button className="submit-feedback-button" onClick={handleSubmitFeedback}>
                Submit Feedback
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;