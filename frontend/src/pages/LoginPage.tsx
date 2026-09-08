import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function LoginPage() {
  const { login, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await login(email);
      navigate('/');
    } catch (err) {
      setError('Login failed. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  if (authLoading) {
    return <div className="loading-page">Loading...</div>;
  }
  
  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Faculty Template Assistant</h1>
        <p className="subtitle">Sign in to continue</p>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="faculty@university.edu"
              required
              disabled={loading}
            />
          </div>
          
          <button type="submit" className="btn-primary btn-full" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <div className="demo-accounts">
          <p>Demo accounts:</p>
          <button 
            type="button" 
            onClick={() => setEmail('faculty@university.edu')}
            className="demo-btn"
          >
            Dr. Jane Smith (CS Faculty)
          </button>
          <button 
            type="button" 
            onClick={() => setEmail('prof.biology@university.edu')}
            className="demo-btn"
          >
            Dr. Robert Johnson (Biology Faculty)
          </button>
          <button 
            type="button" 
            onClick={() => setEmail('dept.admin@university.edu')}
            className="demo-btn"
          >
            Sarah Williams (Dept Admin)
          </button>
        </div>
      </div>
    </div>
  );
}