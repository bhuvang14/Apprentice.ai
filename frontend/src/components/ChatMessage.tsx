import { Message } from '../types';

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  
  return (
    <div className={`chat-message ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-content">
        <div className="message-text">{message.content}</div>
        {message.generated_file && (
          <div className="generated-file">
            <a 
              href={message.generated_file.download_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="download-link"
            >
              📄 Download {message.generated_file.filename}
            </a>
          </div>
        )}
      </div>
      <div className="message-time">
        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </div>
    </div>
  );
}