import { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { templateApi, policyApi } from '../services/api';
import type { Template, PolicySearchResult } from '../types';

export function AdminPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<'templates' | 'policies'>('templates');
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [policies, setPolicies] = useState<PolicySearchResult[]>([]);
  const [loadingPolicies, setLoadingPolicies] = useState(false);
  
  const [showTemplateForm, setShowTemplateForm] = useState(false);
  const [templateForm, setTemplateForm] = useState({
    name: '',
    description: '',
    department: '',
    form_type: '',
    file_type: 'docx',
    required_fields: '{}',
    file: null as File | null,
  });
  
  const [policyForm, setPolicyForm] = useState({
    source_doc: '',
    department: '',
    tags: '',
    file: null as File | null,
  });
  
  useEffect(() => {
    if (user?.role === 'dept_admin' || user?.role === 'system_admin') {
      loadTemplates();
    }
  }, [user]);
  
  const loadTemplates = async () => {
    setLoadingTemplates(true);
    try {
      const data = await templateApi.list();
      setTemplates(data);
    } catch (error) {
      console.error('Failed to load templates:', error);
    } finally {
      setLoadingTemplates(false);
    }
  };
  
  const handleTemplateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const formData = new FormData();
      formData.append('name', templateForm.name);
      formData.append('description', templateForm.description);
      formData.append('department', templateForm.department);
      formData.append('form_type', templateForm.form_type);
      formData.append('file_type', templateForm.file_type);
      formData.append('required_fields', templateForm.required_fields);
      if (templateForm.file) {
        formData.append('file', templateForm.file);
      }
      
      await templateApi.create(formData);
      setShowTemplateForm(false);
      setTemplateForm({
        name: '',
        description: '',
        department: '',
        form_type: '',
        file_type: 'docx',
        required_fields: '{}',
        file: null,
      });
      loadTemplates();
    } catch (error) {
      console.error('Failed to create template:', error);
      alert('Failed to create template');
    }
  };
  
  const handlePolicySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!policyForm.file) return;
    
    setLoadingPolicies(true);
    try {
      const tags = policyForm.tags.split(',').map(t => t.trim()).filter(Boolean);
      await policyApi.upload(policyForm.file, policyForm.source_doc, policyForm.department || undefined, tags);
      setPolicyForm({ source_doc: '', department: '', tags: '', file: null });
      alert('Policy document uploaded successfully');
    } catch (error) {
      console.error('Failed to upload policy:', error);
      alert('Failed to upload policy document');
    } finally {
      setLoadingPolicies(false);
    }
  };
  
  const handleDeleteTemplate = async (id: string) => {
    if (!confirm('Are you sure you want to delete this template?')) return;
    try {
      await templateApi.delete(id);
      loadTemplates();
    } catch (error) {
      console.error('Failed to delete template:', error);
      alert('Failed to delete template');
    }
  };
  
  if (authLoading) return <div className="loading">Loading...</div>;
  if (!user || (user.role !== 'dept_admin' && user.role !== 'system_admin')) {
    return <div className="no-access">Admin access required</div>;
  }
  
  return (
    <div className="admin-page">
      <header className="admin-header">
        <h1>Admin Dashboard</h1>
      </header>
      
      <nav className="admin-tabs">
        <button 
          className={activeTab === 'templates' ? 'active' : ''} 
          onClick={() => setActiveTab('templates')}
        >
          Templates
        </button>
        <button 
          className={activeTab === 'policies' ? 'active' : ''} 
          onClick={() => setActiveTab('policies')}
        >
          Policy Documents
        </button>
      </nav>
      
      {activeTab === 'templates' && (
        <div className="admin-content">
          <div className="admin-toolbar">
            <button onClick={() => setShowTemplateForm(true)} className="btn-primary">
              + Add Template
            </button>
          </div>
          
          {showTemplateForm && (
            <div className="modal-overlay" onClick={() => setShowTemplateForm(false)}>
              <div className="modal" onClick={e => e.stopPropagation()}>
                <h2>Add Template</h2>
                <form onSubmit={handleTemplateSubmit}>
                  <div className="form-group">
                    <label>Name *</label>
                    <input
                      type="text"
                      value={templateForm.name}
                      onChange={e => setTemplateForm({...templateForm, name: e.target.value})}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Description</label>
                    <textarea
                      value={templateForm.description}
                      onChange={e => setTemplateForm({...templateForm, description: e.target.value})}
                    />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Department</label>
                      <input
                        type="text"
                        value={templateForm.department}
                        onChange={e => setTemplateForm({...templateForm, department: e.target.value})}
                      />
                    </div>
                    <div className="form-group">
                      <label>Form Type</label>
                      <input
                        type="text"
                        value={templateForm.form_type}
                        onChange={e => setTemplateForm({...templateForm, form_type: e.target.value})}
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>File Type *</label>
                    <select
                      value={templateForm.file_type}
                      onChange={e => setTemplateForm({...templateForm, file_type: e.target.value})}
                    >
                      <option value="docx">DOCX</option>
                      <option value="xlsx">XLSX</option>
                      <option value="pdf">PDF</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Required Fields (JSON)</label>
                    <textarea
                      value={templateForm.required_fields}
                      onChange={e => setTemplateForm({...templateForm, required_fields: e.target.value})}
                      placeholder='{"field_name": {"type": "string", "required": true, "description": "Field description"}}'
                      rows={4}
                    />
                  </div>
                  <div className="form-group">
                    <label>Template File *</label>
                    <input
                      type="file"
                      accept=".docx,.xlsx,.pdf"
                      onChange={e => setTemplateForm({...templateForm, file: e.target.files?.[0] || null})}
                      required
                    />
                  </div>
                  <div className="modal-actions">
                    <button type="button" className="btn-secondary" onClick={() => setShowTemplateForm(false)}>
                      Cancel
                    </button>
                    <button type="submit" className="btn-primary">Create</button>
                  </div>
                </form>
              </div>
            </div>
          )}
          
          <div className="template-list">
            {loadingTemplates ? (
              <div>Loading...</div>
            ) : templates.length === 0 ? (
              <div className="empty-state">No templates yet. Click "Add Template" to create one.</div>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Department</th>
                    <th>Form Type</th>
                    <th>File Type</th>
                    <th>Version</th>
                    <th>Active</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {templates.map(template => (
                    <tr key={template.id}>
                      <td>{template.name}</td>
                      <td>{template.department || '-'}</td>
                      <td>{template.form_type || '-'}</td>
                      <td>{template.file_type}</td>
                      <td>{template.version}</td>
                      <td>{template.active ? 'Yes' : 'No'}</td>
                      <td>
                        <button 
                          className="btn-danger" 
                          onClick={() => handleDeleteTemplate(template.id)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}
      
      {activeTab === 'policies' && (
        <div className="admin-content">
          <div className="admin-toolbar">
            <h2>Upload Policy Document</h2>
          </div>
          
          <form onSubmit={handlePolicySubmit} className="policy-form">
            <div className="form-group">
              <label>Source Document Name *</label>
              <input
                type="text"
                value={policyForm.source_doc}
                onChange={e => setPolicyForm({...policyForm, source_doc: e.target.value})}
                required
              />
            </div>
            <div className="form-group">
              <label>Department (optional)</label>
              <input
                type="text"
                value={policyForm.department}
                onChange={e => setPolicyForm({...policyForm, department: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label>Tags (comma-separated)</label>
              <input
                type="text"
                value={policyForm.tags}
                onChange={e => setPolicyForm({...policyForm, tags: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label>Policy File *</label>
              <input
                type="file"
                accept=".pdf,.docx,.xlsx,.txt"
                onChange={e => setPolicyForm({...policyForm, file: e.target.files?.[0] || null})}
                required
              />
            </div>
            <button type="submit" className="btn-primary" disabled={loadingPolicies}>
              {loadingPolicies ? 'Uploading...' : 'Upload'}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}