import React, { useState, useEffect } from 'react';
import '../../styles/QuestionSection.css';
import {
  getUserQueryWithFeedback,
  ConfigurationResponse,
  ExperimentFeedbackConfig,
  FeedbackFieldConfig,
} from '../../utils/api';
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

// Old feedback format
interface LegacyFeedback {
  references_feedback?: ReferenceFeedback[];
  summary_feedback?: number;
  feedback?: string;
}

// New experiment feedback format
interface ExperimentFeedback {
  experiment_feedback?: {
    configuration_feedbacks: Record<string, Array<{ field_id: string; value: number | string }>>;
  };
}

type Feedback = LegacyFeedback & ExperimentFeedback;

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
  const [references, setReferences] = useState<Reference[]>([]);
  const [summary, setSummary] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  // New state for experiment responses
  const [responses, setResponses] = useState<ConfigurationResponse[]>([]);
  const [feedbackConfig, setFeedbackConfig] = useState<ExperimentFeedbackConfig | null>(null);
  const [isExperimentQuery, setIsExperimentQuery] = useState(false);
  const [expandedConfigs, setExpandedConfigs] = useState<Set<string>>(new Set());
  const [activeTab, setActiveTab] = useState(0);

  const toggleConfigExpanded = (configId: string) => {
    setExpandedConfigs(prev => {
      const newSet = new Set(prev);
      if (newSet.has(configId)) {
        newSet.delete(configId);
      } else {
        newSet.add(configId);
      }
      return newSet;
    });
  };

  useEffect(() => {
    if (userId && selectedQueryId) {
      loadQueryData(userId, selectedQueryId);
    } else {
      // Clear data when no query is selected
      setQuery('');
      setReferences([]);
      setSummary('');
      setFeedback(null);
      setResponses([]);
      setFeedbackConfig(null);
      setIsExperimentQuery(false);
    }
  }, [userId, selectedQueryId]);

  const loadQueryData = async (userId: string, queryId: string) => {
    try {
      setLoading(true);
      const data = await getUserQueryWithFeedback(userId, queryId);
      setQuery(data.question);
      setFeedback(data.feedback);

      // Check if this is an experiment query (new format)
      if (data.experiment_responses && data.experiment_responses.length > 0) {
        setIsExperimentQuery(true);
        setResponses(data.experiment_responses);
        setFeedbackConfig(data.feedback_config || null);
        setActiveTab(0);
        // Clear legacy fields
        setReferences([]);
        setSummary('');
      } else {
        // Legacy format
        setIsExperimentQuery(false);
        setReferences(data.references || []);
        setSummary(data.summary || '');
        setResponses([]);
        setFeedbackConfig(null);
      }
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

  // Helper to get field label from feedback config
  const getFieldLabel = (fieldId: string): string => {
    if (!feedbackConfig) return fieldId;
    const field = feedbackConfig.fields.find((f: FeedbackFieldConfig) => f.field_id === fieldId);
    return field?.label || fieldId;
  };

  // Helper to get field tooltip from feedback config
  const getFieldTooltip = (fieldId: string): string | undefined => {
    if (!feedbackConfig) return undefined;
    const field = feedbackConfig.fields.find((f: FeedbackFieldConfig) => f.field_id === fieldId);
    return field?.tooltip;
  };

  // Helper to get option label for radio field values
  const getOptionLabel = (fieldId: string, value: number | string): string => {
    if (!feedbackConfig) return String(value);
    const field = feedbackConfig.fields.find((f: FeedbackFieldConfig) => f.field_id === fieldId);
    if (field?.field_type === 'radio' && field.options) {
      const option = field.options.find((o) => o.value === value);
      return option?.label || String(value);
    }
    return String(value);
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

  // Render experiment query (new format)
  if (isExperimentQuery) {
    const configFeedbacks = feedback?.experiment_feedback?.configuration_feedbacks;

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

        <div className="responses-section">
          <h3>Answers</h3>

          {/* Horizontal tabs */}
          {responses.length > 1 && (
            <div className="response-tabs">
              {responses.map((_response, index) => (
                <button
                  key={index}
                  className={`response-tab ${activeTab === index ? 'response-tab--active' : ''}`}
                  onClick={() => setActiveTab(index)}
                >
                  Answer {index + 1}
                </button>
              ))}
            </div>
          )}

          {/* Active tab content */}
          {responses.map((response, index) => {
            if (index !== activeTab) return null;
            const responseFeedback = configFeedbacks?.[response.configuration_id];

            return (
              <div key={`${index}_${response.configuration_id}`} className="response-card" style={{
                marginBottom: '20px',
                padding: '16px',
                border: '1px solid #e9ecef',
                borderRadius: responses.length > 1 ? '0 0 8px 8px' : '8px'
              }}>
                <div className="response-header" style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  {responses.length === 1 && (
                    <span className="response-label" style={{ fontWeight: 'bold', fontSize: '16px' }}>
                      Answer 1
                    </span>
                  )}
                  <button
                    onClick={() => toggleConfigExpanded(response.configuration_id)}
                    style={{
                      fontSize: '12px',
                      padding: '4px 10px',
                      backgroundColor: '#e7f3ff',
                      borderRadius: '4px',
                      color: '#0066cc',
                      border: '1px solid #b3d9ff',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <span>{expandedConfigs.has(response.configuration_id) ? '▼' : '▶'}</span>
                    <strong>{response.configuration?.name || response.configuration_id}</strong>
                  </button>
                </div>

                {/* Collapsible configuration details */}
                {expandedConfigs.has(response.configuration_id) && response.configuration && (
                  <div style={{
                    marginBottom: '12px',
                    padding: '12px',
                    backgroundColor: '#f8f9fa',
                    borderRadius: '6px',
                    border: '1px solid #e9ecef',
                    fontFamily: 'monospace',
                    fontSize: '13px'
                  }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <tbody>
                        <tr>
                          <td style={{ padding: '4px 8px', color: '#666', width: '150px' }}>ID</td>
                          <td style={{ padding: '4px 8px', fontWeight: 'bold' }}>{response.configuration.configuration_id}</td>
                        </tr>
                        <tr>
                          <td style={{ padding: '4px 8px', color: '#666' }}>Name</td>
                          <td style={{ padding: '4px 8px' }}>{response.configuration.name}</td>
                        </tr>
                        <tr>
                          <td style={{ padding: '4px 8px', color: '#666' }}>LLM Model</td>
                          <td style={{ padding: '4px 8px' }}>{response.configuration.llm_model || '(none)'}</td>
                        </tr>
                        <tr>
                          <td style={{ padding: '4px 8px', color: '#666' }}>Embedding Model</td>
                          <td style={{ padding: '4px 8px' }}>{response.configuration.embedding_model}</td>
                        </tr>
                        <tr>
                          <td style={{ padding: '4px 8px', color: '#666' }}>Collection</td>
                          <td style={{ padding: '4px 8px' }}>{response.configuration.collection_name}</td>
                        </tr>
                        <tr>
                          <td style={{ padding: '4px 8px', color: '#666' }}>Temperature</td>
                          <td style={{ padding: '4px 8px' }}>{response.configuration.temperature}</td>
                        </tr>
                        <tr>
                          <td style={{ padding: '4px 8px', color: '#666' }}>Limit</td>
                          <td style={{ padding: '4px 8px' }}>{response.configuration.limit}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                )}
                {response.summary ? (
                  <div className="response-content" style={{ marginTop: '12px' }}>
                    <ReactMarkdown>{response.summary}</ReactMarkdown>
                  </div>
                ) : (
                  <div className="response-content no-summary" style={{ marginTop: '12px', color: '#666' }}>
                    <p>No summary available for this configuration.</p>
                  </div>
                )}

                {/* Display feedback for this response */}
                {responseFeedback && responseFeedback.length > 0 && (
                  <div className="admin-feedback-display" style={{
                    marginTop: '16px',
                    padding: '12px',
                    backgroundColor: '#f8f9fa',
                    borderRadius: '6px',
                    border: '1px solid #e9ecef'
                  }}>
                    <h4 style={{ margin: '0 0 12px 0', color: '#495057' }}>User Feedback</h4>
                    {responseFeedback.map((fieldFeedback: { field_id: string; value: number | string }, idx: number) => {
                      const tooltip = getFieldTooltip(fieldFeedback.field_id);
                      return (
                      <div key={idx} style={{ marginBottom: '8px' }}>
                        <strong>
                          {getFieldLabel(fieldFeedback.field_id)}
                          {tooltip && (
                            <span className="feedback-tooltip-wrapper">
                              <span className="feedback-tooltip-icon">?</span>
                              <span className="feedback-tooltip-text">{tooltip}</span>
                            </span>
                          )}:
                        </strong>{' '}
                        <span style={{ color: '#333' }}>
                          {getOptionLabel(fieldFeedback.field_id, fieldFeedback.value)}
                        </span>
                      </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Render legacy query (old format)
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

            {feedback && feedback.summary_feedback !== undefined && (
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

                {feedback && feedback.references_feedback && feedback.references_feedback[index] && (
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
