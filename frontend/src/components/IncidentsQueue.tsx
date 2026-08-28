import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

export function IncidentsQueue() {
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState<any[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/incidents')
      .then(res => res.json())
      .then(data => setIncidents(data));
  }, []);

  return (
    <div className="bg-white/5 border border-white/10 rounded-lg p-6 w-full max-w-6xl mx-auto mt-8">
      <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
        <span className="text-red-500">🛡️</span> SOC Incident Queue
      </h2>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-white/10 text-sm text-gray-400">
              <th className="py-3 px-4">ID</th>
              <th className="py-3 px-4">Priority</th>
              <th className="py-3 px-4">Severity</th>
              <th className="py-3 px-4">Title</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Time</th>
            </tr>
          </thead>
          <tbody>
            {incidents.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-gray-500">No active incidents</td>
              </tr>
            ) : incidents.map(inc => (
              <tr 
                key={inc.id} 
                className="border-b border-white/5 hover:bg-white/5 cursor-pointer transition-colors"
                onClick={() => navigate(`/incidents/${inc.id}`)}
              >
                <td className="py-3 px-4 font-mono text-xs">{inc.id.split('-')[0]}</td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${
                    inc.priority === 'P1_CRITICAL' ? 'bg-red-500/20 text-red-400' :
                    inc.priority === 'P2_HIGH' ? 'bg-orange-500/20 text-orange-400' :
                    'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {inc.priority.replace('P1_', '').replace('P2_', '')}
                  </span>
                </td>
                <td className="py-3 px-4 text-sm">{inc.severity}</td>
                <td className="py-3 px-4 font-medium text-white">{inc.title}</td>
                <td className="py-3 px-4">
                  <span className="px-2 py-1 bg-white/10 rounded text-xs text-gray-300">
                    {inc.status}
                  </span>
                </td>
                <td className="py-3 px-4 text-xs text-gray-400">
                  {new Date(inc.created_at).toLocaleTimeString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
