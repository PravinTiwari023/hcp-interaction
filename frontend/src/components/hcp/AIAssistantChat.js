import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { chatWithAgentAsync } from '../../features/interactions/interactionsSlice';
import './AIAssistantChat.css';

function AIAssistantChat({ onFormUpdate, formData }) {
  const dispatch = useDispatch();
  const chatResponse = useSelector((state) => state.interactions.chatResponse);
  const chatStatus = useSelector((state) => state.interactions.status);
  
  const [messages, setMessages] = useState([
    {
      type: 'assistant',
      content: 'Hi! I\'m your intelligent AI assistant with LLM-based decision making. I understand your queries, think about what you want to do, and choose the right tool automatically. Just describe what you want naturally - no special commands needed!\n\nExamples:\n• "I met with Dr. Smith today about cardiology" (I\'ll populate the form)\n• "Update Dr. Johnson\'s meeting to positive sentiment" (I\'ll edit the interaction)\n• "Show me all interactions with Dr. Brown" (I\'ll get the history)\n• "Analyze my performance this month" (I\'ll generate insights)',
      timestamp: new Date(),
      isInitial: true
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const lastProcessedResponse = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      const container = messagesEndRef.current.parentElement;
      if (container) {
        // Force scroll to bottom immediately
        container.scrollTop = container.scrollHeight;
        // Then smooth scroll to ensure it's visible
        setTimeout(() => {
          messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }, 50);
      }
    }
  };

  useEffect(() => {
    // Use a slight delay to ensure DOM is updated
    const timer = setTimeout(() => {
      scrollToBottom();
    }, 100);
    return () => clearTimeout(timer);
  }, [messages]);

  useEffect(() => {
    // Also scroll when loading state changes
    if (isLoading) {
      const timer = setTimeout(() => {
        scrollToBottom();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isLoading]);

  useEffect(() => {
    if (chatResponse && chatResponse !== lastProcessedResponse.current) {
      // Handle different response formats from the route_query tool
      let parsedResponse = chatResponse;
      
      // If the response is a string, try to parse it as JSON (for PUT commands)
      if (typeof chatResponse === 'string') {
        try {
          parsedResponse = JSON.parse(chatResponse);
        } catch (e) {
          // If not JSON, treat as regular text response
          parsedResponse = { message: chatResponse };
        }
      }

      // Handle FORM_POPULATE responses (from log interaction)
      if (parsedResponse.response_type === 'FORM_POPULATE') {
        console.log('DEBUG - FORM_POPULATE Response:', parsedResponse);
        
        // Field updates are now directly in the response
        if (parsedResponse.field_updates && onFormUpdate) {
          console.log('DEBUG - Field Updates:', parsedResponse.field_updates);
          console.log('DEBUG - onFormUpdate function:', onFormUpdate);
          
          parsedResponse.field_updates.forEach(update => {
            console.log('DEBUG - Updating field:', update.field, 'with value:', update.value);
            try {
              onFormUpdate(update.field, update.value);
              console.log('DEBUG - Form update successful for:', update.field);
            } catch (error) {
              console.error('DEBUG - Form update failed for:', update.field, error);
            }
          });
        } else if (parsedResponse.message) {
          // Fallback: try to parse the message as JSON
          try {
            const actualResponse = JSON.parse(parsedResponse.message || '{}');
            console.log('DEBUG - Parsed Form Data from message:', actualResponse);
            
            if (actualResponse.field_updates && onFormUpdate) {
              console.log('DEBUG - Field Updates from message:', actualResponse.field_updates);
              actualResponse.field_updates.forEach(update => {
                console.log('DEBUG - Updating field:', update.field, 'with value:', update.value);
                onFormUpdate(update.field, update.value);
              });
            }
          } catch (e) {
            console.log('Could not parse form populate response:', e);
            console.log('Raw message:', parsedResponse.message);
          }
        }
        
        setMessages(prev => [...prev, {
          type: 'assistant',
          content: parsedResponse.message || "I've populated the form with your interaction information.",
          timestamp: new Date(),
          isFormUpdate: true,
          responseType: 'FORM_POPULATE'
        }]);
        
        // Ensure scroll after form populate
        setTimeout(() => scrollToBottom(), 200);
      }
      // Handle FORM_UPDATE responses (from PUT commands)
      else if (parsedResponse.response_type === 'FORM_UPDATE') {
        if (onFormUpdate && parsedResponse.field && parsedResponse.value !== undefined) {
          onFormUpdate(parsedResponse.field, parsedResponse.value);
        }
        
        setMessages(prev => [...prev, {
          type: 'assistant',
          content: parsedResponse.message || `Updated ${parsedResponse.field} to "${parsedResponse.value}"`,
          timestamp: new Date(),
          isFormUpdate: true,
          responseType: 'FORM_UPDATE'
        }]);
        
        // Ensure scroll after form update
        setTimeout(() => scrollToBottom(), 200);
      } 
      // Handle ERROR responses
      else if (parsedResponse.response_type === 'ERROR') {
        setMessages(prev => [...prev, {
          type: 'assistant',
          content: parsedResponse.message || 'An error occurred',
          timestamp: new Date(),
          isError: true,
          responseType: 'ERROR'
        }]);
        
        // Ensure scroll after error message
        setTimeout(() => scrollToBottom(), 200);
      }
      // Handle regular text responses (add commands, get commands, etc.)
      else {
        const content = parsedResponse.message || 
                       (typeof parsedResponse === 'string' ? parsedResponse : 'Response received');
        
        setMessages(prev => [...prev, {
          type: 'assistant',
          content: content,
          timestamp: new Date()
        }]);
        
        // Ensure scroll after regular response
        setTimeout(() => scrollToBottom(), 200);
      }
      
      setIsLoading(false);
      lastProcessedResponse.current = chatResponse;
    }
  }, [chatResponse, onFormUpdate]);

  const handleSendMessage = useCallback(async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    
    // Scroll after user message
    setTimeout(() => scrollToBottom(), 100);

    try {
      await dispatch(chatWithAgentAsync({ 
        message: inputMessage, 
        formData: formData || {} 
      }));
      setInputMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        isError: true
      }]);
      setIsLoading(false);
      
      // Scroll after error message
      setTimeout(() => scrollToBottom(), 200);
    }
  }, [inputMessage, isLoading, dispatch]);

  const formatMessage = (content) => {
    return content.split('\n').map((line, index) => (
      <div key={index}>
        {line}
        {index < content.split('\n').length - 1 && <br />}
      </div>
    ));
  };

  return (
    <div className="ai-assistant-chat">
      {/* Header - exactly as in image.png */}
      <div className="ai-header">
        <div className="ai-icon">🧠</div>
        <div className="ai-title">
          <div className="ai-title-text">Intelligent AI Assistant</div>
          <div className="ai-subtitle">LLM-based decision making</div>
        </div>
      </div>

      {/* Chat Messages Area - exactly as in image.png */}
      <div className="ai-chat-area">
        <div className="ai-messages">
          {messages.map((message, index) => (
            <div key={index} className={`ai-message ${message.type}`}>
              {message.isFormUpdate && (
                <div className="form-update-indicator">
                  {message.responseType === 'FORM_POPULATE' ? 'Form Populated' : 'Form Updated'}
                </div>
              )}
              <div className={`ai-message-content ${message.isFormUpdate ? 'form-update' : ''} ${message.isError ? 'error' : ''}`}>
                {formatMessage(message.content)}
                {message.responseType === 'FORM_UPDATE' && (
                  <div className="put-command-feedback">
                    Field updated successfully
                  </div>
                )}
                {message.responseType === 'FORM_POPULATE' && (
                  <div className="put-command-feedback">
                    Form populated with interaction details
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="ai-message assistant">
              <div className="ai-message-content">
                <div className="ai-typing">
                  <span></span><span></span><span></span>
                  <span style={{ marginLeft: '8px' }}>Processing...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} style={{ height: '1px' }} />
        </div>
      </div>

      {/* Input Area - exactly as in image.png */}
      <div className="ai-input-section">
        <form onSubmit={handleSendMessage}>
          <div className="ai-input-container">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Describe your interaction or ask a question..."
              disabled={isLoading}
              className="ai-textarea"
              rows="3"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(e);
                }
              }}
            />
            <button 
              type="submit"
              disabled={isLoading || !inputMessage.trim()}
              className="ai-log-button"
            >
              ▲ Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AIAssistantChat;