import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

export function IncidentDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    fetch(`http://localhost:8000/api/incidents/${id}`)
      .then(res => res.json())
      .then(d => setData(d));
  }, [id]);

  const handleApprove = async (actionId: string) => {
    await fetch(`http://localhost:8000/api/incidents/${id}/approve-action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_id: actionId, analyst_id: "soc-analyst-1" })
    });
    // Refresh
    const res = await fetch(`http://localhost:8000/api/incidents/${id}`);
    setData(await res.json());
  };

  const handleReject = async (actionId: string) => {
    await fetch(`http://localhost:8000/api/incidents/${id}/reject-action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_id: actionId, analyst_id: "soc-analyst-1" })
    });
    // Refresh
    const res = await fetch(`http://localhost:8000/api/incidents/${id}`);
    setData(await res.json());
  };

  if (!data) return <div className="text-center mt-20 text-gray-400 animate-pulse">Loading incident {id}...</div>;

  const { incident, recommended_actions } = data;

  return (
    <div className="w-full max-w-6xl mx-auto mt-8">
      <button onClick={() => navigate('/incidents')} className="text-sm text-gray-400 hover:text-white mb-6 flex items-center gap-1">
        ← Back to Queue
      </button>

      <div className="bg-white/5 border border-white/10 rounded-lg p-6 mb-8 shadow-2xl">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-3xl font-bold mb-2">{incident.title}</h2>
            <p className="text-gray-400">Incident ID: <span className="font-mono text-gray-300">{incident.id}</span></p>
          </div>
          <div className="flex gap-3">
            <span className="px-3 py-1 bg-red-500/20 text-red-400 rounded-full text-sm font-semibold border border-red-500/30">
              {incident.priority}
            </span>
            <span className="px-3 py-1 bg-white/10 text-white rounded-full text-sm font-medium">
              {incident.status}
            </span>
          </div>
        </div>

        <div className="bg-black/30 p-4 rounded-lg mt-6 border border-white/5">
          <h3 className="text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wider">Executive Summary</h3>
          <p className="text-gray-200 leading-relaxed">{incident.summary}</p>
        </div>
      </div>

      <h3 className="text-xl font-semibold mb-4 border-b border-white/10 pb-2">Recommended Actions</h3>
      <div className="grid gap-4 mb-8">
        {recommended_actions.length === 0 ? (
          <p className="text-gray-500">No actions recommended.</p>
        ) : recommended_actions.map((action: any) => (
          <div key={action.id} className="bg-white/5 border border-white/10 p-5 rounded-lg flex justify-between items-center group hover:bg-white/10 transition-colors">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                  action.action_type === 'BLOCK' ? 'bg-red-500 text-white' : 'bg-blue-500 text-white'
                }`}>
                  {action.action_type}
                </span>
                <span className="text-xs text-gray-500">Confidence: {Math.round(action.confidence * 100)}%</span>
              </div>
              <p className="text-white mt-2">{action.description}</p>
            </div>
            
            <div className="flex gap-2">
              {action.status === 'PENDING_APPROVAL' ? (
                <>
                  <button onClick={() => handleApprove(action.id)} className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded font-medium transition-colors">
                    Approve
                  </button>
                  <button onClick={() => handleReject(action.id)} className="px-4 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-400 rounded font-medium transition-colors border border-red-500/30">
                    Reject
                  </button>
                </>
              ) : (
                <span className={`px-4 py-2 rounded font-medium ${
                  action.status === 'APPROVED' || action.status === 'EXECUTED' ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'
                }`}>
                  {action.status}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
