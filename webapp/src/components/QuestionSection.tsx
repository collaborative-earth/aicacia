import React, { useState } from 'react';
import '../styles/QuestionSection.css';
import { askQuestion, submitFeedback } from '../utils/api';
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

const USEFUL_FEEDBACK = 10;
const NOT_USEFUL_FEEDBACK = 0;
const DONT_KNOW_FEEDBACK = -1;

interface QuestionSectionProps {}

const QuestionSection: React.FC<QuestionSectionProps> = () => {
  const [query, setQuery] = useState('');
  const [queryId, setQueryId] = useState('');
  const [references, setReferences] = useState<Reference[]>([]);
  const [summary, setSummary] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [referencesFeedback, setReferencesFeedback] = useState<ReferenceFeedback[]>([]);
  const [overallFeedback, setOverallFeedback] = useState<string>('');
  const [summaryFeedback, setSummaryFeedback] = useState<number>(DONT_KNOW_FEEDBACK);

  const handleSearch = async (e: React.FormEvent) => {
    if (!query) {
      return;
    }

    e.preventDefault();
    setReferences([]);
    setSummary('');
    setLoading(true);

    const res = await askQuestion(query);

    setLoading(false);
    setReferences(res.references);
    setReferencesFeedback(res.references.map(() => ({ feedback: DONT_KNOW_FEEDBACK, feedback_reason: '' })));
    setSummaryFeedback(DONT_KNOW_FEEDBACK);
    setSummary(res.summary);
    setQueryId(res.query_id);
  };

  const askForNewQuestion = () => {
    setQuery('');
    setQueryId('');
    setReferences([]);
    setReferencesFeedback([]);
    setSummary('');
    setOverallFeedback('');
    setSummaryFeedback(DONT_KNOW_FEEDBACK);
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch(e);
    }
  };

  const handleFeedbackChange = (index: number, feedback: number) => {
    const updatedReferencesFeedback = [...referencesFeedback];
    updatedReferencesFeedback[index] = {
      ...updatedReferencesFeedback[index],
      feedback: feedback
    };
    setReferencesFeedback(updatedReferencesFeedback);
  };

  const handleFeedbackReasonChange = (index: number, reason: string) => {
    const updatedReferencesFeedback = [...referencesFeedback];
    updatedReferencesFeedback[index] = {
      ...updatedReferencesFeedback[index],
      feedback_reason: reason
    };
    setReferencesFeedback(updatedReferencesFeedback);
  };

  const handleOverallFeedbackChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setOverallFeedback(e.target.value);
  };

  const handleSubmitFeedback = async () => {
    await submitFeedback({
      query_id: queryId,
      references_feedback: referencesFeedback,
      summary_feedback: summaryFeedback,
      feedback: overallFeedback,
    });
    alert('Feedback submitted successfully');
    askForNewQuestion();
  };

  return (
    <div className="question-section">
      <h2>Ask about Restoration Projects</h2>
      <form className="search-form" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Enter your question"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className="search-input"
        />
        <button type="submit" className="search-button"  disabled={loading}>
          {loading ? 'Loading...' : 'Search'}
        </button>
      </form>

      {summary && (
        <div className="summary-section">
          <h3>Summary</h3>
          <div className="summary-output">
            <ReactMarkdown>{summary}</ReactMarkdown>

            <div className="feedback-divider"></div>
              <div className="feedback-options">
                <label>
                  <input
                    type="radio"
                    name="summary-feedback"
                    value="useful"
                    checked={summaryFeedback === USEFUL_FEEDBACK}
                    onChange={() => setSummaryFeedback(USEFUL_FEEDBACK)}
                  />
                  Useful
                </label>
                <label>
                  <input
                    type="radio"
                    name="summary-feedback"
                    value="not-useful"
                    checked={summaryFeedback === NOT_USEFUL_FEEDBACK}
                    onChange={() => setSummaryFeedback(NOT_USEFUL_FEEDBACK)}
                  />
                  Not Useful
                </label>
                <label>
                  <input
                    type="radio"
                    name="summary-feedback"
                    value="dont-know"
                    checked={summaryFeedback === DONT_KNOW_FEEDBACK}
                    onChange={() => setSummaryFeedback(DONT_KNOW_FEEDBACK)}
                  />
                  Don't Know
                </label>
              </div>
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
                <div className="feedback-options">
                  <div className="feedback-radio-group">
                    <label>
                      <input
                        type="radio"
                        name={`feedback-${index}`}
                        value="useful"
                        checked={referencesFeedback[index]?.feedback === USEFUL_FEEDBACK}
                        onChange={() => handleFeedbackChange(index, USEFUL_FEEDBACK)}
                      />
                      Useful
                    </label>
                    <label>
                      <input
                        type="radio"
                        name={`feedback-${index}`}
                        value="not-useful"
                        checked={referencesFeedback[index]?.feedback === NOT_USEFUL_FEEDBACK}
                        onChange={() => handleFeedbackChange(index, NOT_USEFUL_FEEDBACK)}
                      />
                      Not Useful
                    </label>
                    <label>
                      <input
                        type="radio"
                        name={`feedback-${index}`}
                        value="not-useful"
                        checked={referencesFeedback[index]?.feedback === DONT_KNOW_FEEDBACK}
                        onChange={() => handleFeedbackChange(index, DONT_KNOW_FEEDBACK)}
                      />
                      Don't Know
                    </label>
                  </div>
                  <textarea
                    placeholder="Why did you choose this option?"
                    value={referencesFeedback[index]?.feedback_reason || ''}
                    onChange={(e) => {
                      handleFeedbackReasonChange(index, e.target.value);
                      // Auto-grow functionality
                      e.target.style.height = 'auto';
                      e.target.style.height = e.target.scrollHeight + 'px';
                    }}
                    className="feedback-reason-input"
                    rows={1}
                  />
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
  );
};

export default QuestionSection;
