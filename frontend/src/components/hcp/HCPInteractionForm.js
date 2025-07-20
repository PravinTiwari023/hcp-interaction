import React, { useState, useEffect, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { logInteractionAsync } from '../../features/interactions/interactionsSlice';
import AIAssistantChat from './AIAssistantChat';
import './HCPInteractionForm.css';

function HCPInteractionForm() {
  const dispatch = useDispatch();

  const [formData, setFormData] = useState({
    hcpName: '',
    interactionType: '',
    date: new Date().toISOString().split('T')[0],
    time: new Date().toTimeString().slice(0, 5),
    attendees: '',
    topicsDiscussed: '',
    materialsShared: '',
    samplesDistributed: '',
    hcpSentiment: 'Neutral',
    outcomes: '',
    followUpActions: '',
  });
  const [isRecording, setIsRecording] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [updatedFields, setUpdatedFields] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Handler for form updates from AI assistant
  const handleFormUpdate = useCallback((field, value) => {
    console.log('DEBUG - handleFormUpdate called with:', { field, value });
    
    const fieldMapping = {
      // Primary field mappings
      'sentiment': 'hcpSentiment',
      'interaction_type': 'interactionType',
      'summary': 'outcomes',
      'key_discussion_points': 'topicsDiscussed',
      'materials_shared': 'materialsShared',
      'samples_distributed': 'samplesDistributed',
      'follow_up_actions': 'followUpActions',
      'attendees': 'attendees',
      'date': 'date',
      'time': 'time',
      'hcp_name': 'hcpName',
      
      // Alternative field names (for different PUT command variations)
      'materials': 'materialsShared',
      'samples': 'samplesDistributed',
      'follow_up': 'followUpActions',
      'topics': 'topicsDiscussed',
      'discussion': 'topicsDiscussed',
      'outcomes': 'outcomes',
      'results': 'outcomes',
      'type': 'interactionType',
      'interaction_date': 'date',
      'interaction_time': 'time',
      'name': 'hcpName',
      'doctor': 'hcpName',
      'hcp': 'hcpName',
      
      // Sentiment variations
      'feeling': 'hcpSentiment',
      'mood': 'hcpSentiment',
      'reaction': 'hcpSentiment',
      
      // Date/time variations
      'when': 'date',
      'meeting_date': 'date',
      'meeting_time': 'time'
    };

    const formFieldName = fieldMapping[field.toLowerCase()] || field;
    
    console.log('DEBUG - Field mapping:', { 
      originalField: field, 
      mappedField: formFieldName, 
      value: value 
    });
    
    // Handle special value transformations
    let transformedValue = value;
    
    // Normalize sentiment values
    if (formFieldName === 'hcpSentiment') {
      const sentimentMap = {
        'positive': 'Positive',
        'good': 'Positive',
        'happy': 'Positive',
        'pleased': 'Positive',
        'satisfied': 'Positive',
        'neutral': 'Neutral',
        'okay': 'Neutral',
        'fine': 'Neutral',
        'average': 'Neutral',
        'negative': 'Negative',
        'bad': 'Negative',
        'unhappy': 'Negative',
        'dissatisfied': 'Negative',
        'concerned': 'Negative'
      };
      transformedValue = sentimentMap[value.toLowerCase()] || value;
    }
    
    // Normalize interaction type values
    if (formFieldName === 'interactionType') {
      const typeMap = {
        'meeting': 'Meeting',
        'call': 'Call',
        'phone': 'Call',
        'email': 'Email',
        'visit': 'Visit',
        'conference': 'Conference',
        'other': 'Other'
      };
      transformedValue = typeMap[value.toLowerCase()] || value;
    }
    
    console.log('DEBUG - Updating form data:', {
      formFieldName,
      transformedValue,
      currentFormData: formData
    });
    
    setFormData(prev => ({
      ...prev,
      [formFieldName]: transformedValue
    }));
    
    // Add visual feedback for the updated field
    setUpdatedFields(prev => ({
      ...prev,
      [formFieldName]: true
    }));
    
    // Remove the highlight after 3 seconds
    setTimeout(() => {
      setUpdatedFields(prev => ({
        ...prev,
        [formFieldName]: false
      }));
    }, 3000);
    
    // Show visual feedback for the update
    console.log(`Form updated: ${field} -> ${formFieldName} = ${transformedValue}`);
  }, []);


  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      
      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;
      recognitionInstance.lang = 'en-US';
      
      recognitionInstance.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }
        setFormData(prev => ({ ...prev, topicsDiscussed: transcript }));
      };
      
      recognitionInstance.onend = () => {
        setIsRecording(false);
      };
      
      setRecognition(recognitionInstance);
    }
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSentimentChange = (sentiment) => {
    setFormData(prev => ({ ...prev, hcpSentiment: sentiment }));
  };

  const toggleRecording = () => {
    if (!recognition) return;
    
    if (isRecording) {
      recognition.stop();
      setIsRecording(false);
    } else {
      recognition.start();
      setIsRecording(true);
    }
  };

  // Reset form function
  const resetForm = () => {
    setFormData({
      hcpName: '',
      interactionType: '',
      date: new Date().toISOString().split('T')[0],
      time: '',
      attendees: '',
      topicsDiscussed: '',
      materialsShared: '',
      samplesDistributed: '',
      hcpSentiment: '',
      outcomes: '',
      followUpActions: ''
    });
    setUpdatedFields({});
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Prevent double submission
    if (isSubmitting) return;
    
    // Validation
    if (!formData.hcpName || formData.hcpName.trim() === '') {
      alert("Please enter an HCP name.");
      return;
    }
    
    if (!formData.interactionType) {
      alert("Please select an interaction type.");
      return;
    }

    const interactionData = {
      hcp_name: formData.hcpName.trim(),
      interaction_date: formData.date,
      interaction_time: formData.time,
      interaction_type: formData.interactionType,
      attendees: formData.attendees,
      summary: formData.outcomes,
      key_discussion_points: formData.topicsDiscussed,
      materials_shared: formData.materialsShared,
      samples_distributed: formData.samplesDistributed,
      sentiment: formData.hcpSentiment,
      follow_up_actions: formData.followUpActions,
    };
    
    setIsSubmitting(true);
    
    try {
      console.log('Submitting interaction data:', interactionData);
      
      // Dispatch the async action and wait for it to complete
      const result = await dispatch(logInteractionAsync(interactionData));
      
      if (result.type === 'interactions/logInteraction/fulfilled') {
        const addAnother = window.confirm("✅ Interaction logged successfully!\n\nWould you like to add another interaction?");
        
        if (addAnother) {
          resetForm();
        }
      } else {
        throw new Error(result.payload || 'Failed to log interaction');
      }
    } catch (error) {
      console.error('Error submitting interaction:', error);
      alert("❌ Error logging interaction. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <h1 className="page-title">Log HCP Interaction</h1>
      
      <div className="hcp-interaction-container">
        {/* Left Column - Form */}
        <div className="form-section">
          <form onSubmit={handleSubmit}>
          <div className="form-grid">
            {/* Interaction Details Section */}
            <div>
              <h2 className="section-header">Interaction Details</h2>
              
              <div className="form-row">
                {/* HCP Name */}
                <div className="form-group">
                  <label>HCP Name</label>
                  <input
                    type="text"
                    name="hcpName"
                    value={formData.hcpName}
                    onChange={handleChange}
                    placeholder="Enter HCP name (e.g., Dr. Sarah Johnson)"
                    className={`form-input ${updatedFields.hcpName ? 'updated' : ''}`}
                    required
                  />
                </div>

                {/* Interaction Type */}
                <div className="form-group">
                  <label>Interaction Type</label>
                  <input
                    type="text"
                    name="interactionType"
                    value={formData.interactionType}
                    onChange={handleChange}
                    placeholder="Enter interaction type (e.g., Meeting, Call, Email)"
                    className={`form-input ${updatedFields.interactionType ? 'updated' : ''}`}
                  />
                </div>
              </div>

              <div className="form-row">
                {/* Date */}
                <div className="form-group">
                  <label>Date</label>
                  <input
                    type="date"
                    name="date"
                    value={formData.date}
                    onChange={handleChange}
                    className="form-input"
                  />
                </div>

                {/* Time */}
                <div className="form-group">
                  <label>Time</label>
                  <input
                    type="time"
                    name="time"
                    value={formData.time}
                    onChange={handleChange}
                    className="form-input"
                  />
                </div>
              </div>

              {/* Attendees */}
              <div className="form-row single">
                <div className="form-group">
                  <label>Attendees</label>
                  <input
                    type="text"
                    name="attendees"
                    value={formData.attendees}
                    onChange={handleChange}
                    placeholder="Enter names or search..."
                    className="form-input"
                  />
                </div>
              </div>

              {/* Topics Discussed */}
              <div className="form-row single">
                <div className="form-group">
                  <label>Topics Discussed</label>
                  <div className="textarea-container">
                    <textarea
                      name="topicsDiscussed"
                      value={formData.topicsDiscussed}
                      onChange={handleChange}
                      placeholder="Enter key discussion points..."
                      className={`form-textarea ${updatedFields.topicsDiscussed ? 'updated' : ''}`}
                      rows="5"
                    />
                    <button
                      type="button"
                      onClick={toggleRecording}
                      className={`voice-button ${isRecording ? 'recording' : ''}`}
                      title="Voice recording"
                    >
                      🎤
                    </button>
                  </div>
                  <div className="voice-note-feature">
                    <span className="icon">🎤</span>
                    <span>Summarize from Voice Note (Requires Consent)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Materials Shared / Samples Distributed Section */}
            <div>
              <h2 className="section-header">Materials Shared / Samples Distributed</h2>
              
              <div className="form-row">
                {/* Materials Shared */}
                <div className="form-group">
                  <label>Materials Shared</label>
                  <input
                    type="text"
                    name="materialsShared"
                    value={formData.materialsShared}
                    onChange={handleChange}
                    placeholder="Enter materials shared..."
                    className={`form-input ${updatedFields.materialsShared ? 'updated' : ''}`}
                  />
                </div>

                {/* Samples Distributed */}
                <div className="form-group">
                  <label>Samples Distributed</label>
                  <input
                    type="text"
                    name="samplesDistributed"
                    value={formData.samplesDistributed}
                    onChange={handleChange}
                    placeholder="Enter samples distributed..."
                    className={`form-input ${updatedFields.samplesDistributed ? 'updated' : ''}`}
                  />
                </div>
              </div>
            </div>

            {/* Observed/Inferred HCP Sentiment */}
            <div>
              <h2 className="section-header">Observed/Inferred HCP Sentiment</h2>
              
              <div className="sentiment-group">
                <div 
                  className={`sentiment-option ${updatedFields.hcpSentiment && formData.hcpSentiment === 'Positive' ? 'updated' : ''}`}
                  onClick={() => handleSentimentChange('Positive')}
                >
                  <div className={`sentiment-radio ${formData.hcpSentiment === 'Positive' ? 'checked' : ''}`}></div>
                  <label className="sentiment-label">
                    <span className="sentiment-emoji">😊</span>
                    Positive
                  </label>
                </div>

                <div 
                  className={`sentiment-option ${updatedFields.hcpSentiment && formData.hcpSentiment === 'Neutral' ? 'updated' : ''}`}
                  onClick={() => handleSentimentChange('Neutral')}
                >
                  <div className={`sentiment-radio ${formData.hcpSentiment === 'Neutral' ? 'checked' : ''}`}></div>
                  <label className="sentiment-label">
                    <span className="sentiment-emoji">😐</span>
                    Neutral
                  </label>
                </div>

                <div 
                  className={`sentiment-option ${updatedFields.hcpSentiment && formData.hcpSentiment === 'Negative' ? 'updated' : ''}`}
                  onClick={() => handleSentimentChange('Negative')}
                >
                  <div className={`sentiment-radio ${formData.hcpSentiment === 'Negative' ? 'checked' : ''}`}></div>
                  <label className="sentiment-label">
                    <span className="sentiment-emoji">😞</span>
                    Negative
                  </label>
                </div>
              </div>
            </div>

            {/* Outcomes */}
            <div>
              <h2 className="section-header">Outcomes</h2>
              <div className="form-row single">
                <div className="form-group">
                  <textarea
                    name="outcomes"
                    value={formData.outcomes}
                    onChange={handleChange}
                    placeholder="Key outcomes or agreements..."
                    className="form-textarea"
                    rows="4"
                  />
                </div>
              </div>
            </div>

            {/* Follow-up Actions */}
            <div>
              <h2 className="section-header">Follow-up Actions</h2>
              <div className="form-row single">
                <div className="form-group">
                  <textarea
                    name="followUpActions"
                    value={formData.followUpActions}
                    onChange={handleChange}
                    placeholder="Enter next steps or tasks..."
                    className="form-textarea"
                    rows="3"
                  />
                </div>
              </div>

              {/* AI Suggested Follow-ups */}
              <div className="ai-suggestions">
                <div className="ai-suggestions-title">
                  <span>🧠</span>
                  AI Suggested Follow-ups:
                </div>
                <ul className="ai-suggestions-list">
                  <li>Schedule follow-up meeting in 2 weeks</li>
                  <li>Send OncoBoost Phase III PDF</li>
                  <li>Add Dr. Sharma to advisory board invite list</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="form-section">
            <div className="submit-button-container">
              <button 
                type="submit" 
                className="submit-button"
                disabled={!formData.hcpName || !formData.interactionType || isSubmitting}
              >
                <span className="submit-button-icon">
                  {isSubmitting ? '⏳' : '📝'}
                </span>
                {isSubmitting ? 'Adding Interaction...' : 'Add Interaction Detail'}
              </button>
            </div>
          </div>
        </form>
      </div>

        {/* Right Column - AI Assistant */}
        <div className="ai-assistant-section">
          <AIAssistantChat onFormUpdate={handleFormUpdate} formData={formData} />
        </div>
      </div>
    </div>
  );
}

export default HCPInteractionForm;