import React, { useState, useEffect } from 'react';
import '../styles/QuestionSection.css';
import {
  askQuestion,
  getQueryWithFeedback,
  submitExperimentFeedback,
  ConfigurationResponse,
  ExperimentFeedbackConfig,
  ExperimentFeedbackEntry,
} from '../utils/api';
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
  const [feedbackConfig, setFeedbackConfig] = useState<ExperimentFeedbackConfig | null>(null);
  const [feedbackValues, setFeedbackValues] = useState<Record<string, number | string>>({});
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

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
      setFeedbackConfig(res.feedback_config || null);
      setFeedbackValues({});
      setFeedbackSubmitted(false);
      onNewQuestionSubmitted();
    } catch (error) {
      console.error('Failed to ask question:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadQueryData = async (loadedQueryId: string) => {
    try {
      setLoading(true);
      const data = await getQueryWithFeedback(loadedQueryId);
      setQuery(data.question);
      setQueryId(data.query_id);

      // Handle both old and new format for responses
      let loadedResponses: ConfigurationResponse[];
      if (data.experiment_responses && data.experiment_responses.length > 0) {
        // New format - use experiment_responses directly
        loadedResponses = data.experiment_responses;
      } else {
        // Old format - convert to single-response array
        loadedResponses = [{
          configuration_id: 'legacy',
          references: data.references || [],
          summary: data.summary || null
        }];
      }
      setResponses(loadedResponses);

      // Load feedback config if available
      if (data.feedback_config) {
        setFeedbackConfig(data.feedback_config as ExperimentFeedbackConfig);
      } else {
        setFeedbackConfig(null);
      }

      // Populate feedback values if feedback exists
      if (data.feedback?.experiment_feedback?.configuration_feedbacks) {
        const loadedValues: Record<string, number | string> = {};
        const configFeedbacks = data.feedback.experiment_feedback.configuration_feedbacks;

        // Map configuration feedbacks back to form values
        loadedResponses.forEach((response, index) => {
          const responseKey = `${index}_${response.configuration_id}`;
          const feedbacksForConfig = configFeedbacks[response.configuration_id];
          if (feedbacksForConfig) {
            feedbacksForConfig.forEach((field: { field_id: string; value: number | string }) => {
              loadedValues[`${responseKey}_${field.field_id}`] = field.value;
            });
          }
        });

        setFeedbackValues(loadedValues);
        setFeedbackSubmitted(true);
      } else {
        setFeedbackValues({});
        setFeedbackSubmitted(false);
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
    setFeedbackConfig(null);
    setFeedbackValues({});
    setFeedbackSubmitted(false);
  };

  const handleFeedbackChange = (configurationId: string, fieldId: string, value: number | string) => {
    setFeedbackValues((prev) => ({
      ...prev,
      [`${configurationId}_${fieldId}`]: value,
    }));
  };

  const handleSubmitFeedback = async () => {
    if (!queryId || !feedbackConfig) return;

    setSubmittingFeedback(true);
    try {
      // Transform feedbackValues into ExperimentFeedbackEntry array
      const feedbacks: ExperimentFeedbackEntry[] = [];
      responses.forEach((response, index) => {
        const responseKey = `${index}_${response.configuration_id}`;
        for (const field of feedbackConfig.fields) {
          const key = `${responseKey}_${field.field_id}`;
          const value = feedbackValues[key];
          if (value !== undefined && value !== '') {
            feedbacks.push({
              configuration_id: response.configuration_id,
              field_id: field.field_id,
              value: value,
            });
          }
        }
      });

      await submitExperimentFeedback({
        query_id: queryId,
        feedbacks: feedbacks,
      });

      setFeedbackSubmitted(true);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSearch(e);
    }
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
        <button type="submit" className="search-button" disabled={loading}>
          {loading ? 'Loading...' : 'Search'}
        </button>
      </form>

      {responses.length > 0 && (
        <div className="responses-section">
          <h3>Answers</h3>
          {responses.map((response, index) => {
            // Use index as part of key to handle duplicate configuration_ids
            const responseKey = `${index}_${response.configuration_id}`;
            return (
              <div key={responseKey} className="response-card">
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

                {/* Feedback form for this response - always show if feedbackConfig exists */}
                {feedbackConfig && (
                  <div className="feedback-section">
                    <h4>Provide Feedback for Answer {index + 1}</h4>
                    {feedbackConfig.fields.map((field) => (
                      <div key={`${responseKey}_${field.field_id}`} className="feedback-field">
                        <label>{field.label}{field.required && ' *'}</label>
                        {field.field_type === 'radio' && field.options && (
                          <div className="feedback-radio-group">
                            {field.options.map((option) => (
                              <label key={`${responseKey}_${field.field_id}_${option.value}`}>
                                <input
                                  type="radio"
                                  name={`${responseKey}_${field.field_id}`}
                                  value={option.value}
                                  checked={feedbackValues[`${responseKey}_${field.field_id}`] === option.value}
                                  onChange={() => handleFeedbackChange(responseKey, field.field_id, option.value)}
                                />
                                {option.label}
                              </label>
                            ))}
                          </div>
                        )}
                        {field.field_type === 'text' && (
                          <textarea
                            className="feedback-reason-input"
                            placeholder="Enter your feedback..."
                            value={feedbackValues[`${responseKey}_${field.field_id}`] as string || ''}
                            onChange={(e) => handleFeedbackChange(responseKey, field.field_id, e.target.value)}
                          />
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {/* Submit button - always show if feedbackConfig exists */}
          {feedbackConfig && (
            <button
              onClick={handleSubmitFeedback}
              className="submit-feedback-button"
              disabled={submittingFeedback}
            >
              {submittingFeedback ? 'Submitting...' : (feedbackSubmitted ? 'Update Feedback' : 'Submit Feedback')}
            </button>
          )}

          {/* Success notification */}
          {feedbackSubmitted && (
            <div className="feedback-notification">
              ✓ Feedback saved
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default QuestionSection;
