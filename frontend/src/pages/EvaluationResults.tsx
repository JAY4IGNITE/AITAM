import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { Loader2, CheckCircle2, XCircle, AlertCircle, RefreshCw } from 'lucide-react';

const API_URL = "http://localhost:8000/api";

export function EvaluationResults() {
  const { id } = useParams();

  const { data: run, isLoading, refetch } = useQuery({
    queryKey: ['evaluation', id],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/evaluation/${id}`);
      if (!res.ok) throw new Error('Failed to fetch evaluation');
      return res.json();
    },
    refetchInterval: (query: any) => {
      const data = query?.state?.data;
      return (data?.status === 'COMPLETED' || data?.status === 'FAILED') ? false : 3000;
    }
  });

  if (isLoading) {
    return <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 text-blue-500 animate-spin" /></div>;
  }

  const isRunning = run?.status === 'RUNNING' || run?.status === 'STARTING';

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            Evaluation Results
            {isRunning && <RefreshCw className="w-5 h-5 text-blue-400 animate-spin" />}
          </h1>
          <p className="text-gray-400 mt-2">ID: {run?.id}</p>
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
          run?.status === 'COMPLETED' ? 'bg-green-900/30 text-green-400' :
          run?.status === 'FAILED' ? 'bg-red-900/30 text-red-400' :
          'bg-blue-900/30 text-blue-400'
        }`}>
          {run?.status}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <div className="text-gray-400 text-sm font-medium">Total Samples</div>
          <div className="text-3xl font-bold text-white mt-2">{run?.total_samples || 0}</div>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <div className="text-gray-400 text-sm font-medium">Completed</div>
          <div className="text-3xl font-bold text-green-400 mt-2 flex items-center gap-2">
            <CheckCircle2 className="w-6 h-6" /> {run?.completed_samples || 0}
          </div>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <div className="text-gray-400 text-sm font-medium">Failed</div>
          <div className="text-3xl font-bold text-red-400 mt-2 flex items-center gap-2">
            <XCircle className="w-6 h-6" /> {run?.failed_samples || 0}
          </div>
        </div>
      </div>

      {run?.status === 'COMPLETED' && run.accuracy !== null && (
        <>
          <h2 className="text-xl font-bold text-white mt-8 mb-4">Metrics (Macro Average)</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard title="Accuracy" value={(run.accuracy * 100).toFixed(1) + '%'} />
            <MetricCard title="Precision" value={(run.precision * 100).toFixed(1) + '%'} />
            <MetricCard title="Recall" value={(run.recall * 100).toFixed(1) + '%'} />
            <MetricCard title="F1 Score" value={(run.f1_score * 100).toFixed(1) + '%'} />
          </div>

          <h2 className="text-xl font-bold text-white mt-8 mb-4">Confusion Matrix</h2>
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 overflow-x-auto">
             <table className="w-full text-sm text-left text-gray-400">
                <thead className="text-xs text-gray-300 uppercase bg-gray-900">
                  <tr>
                    <th className="px-6 py-3">Actual \ Predicted</th>
                    {run.confusion_matrix.labels.map((l: string) => <th key={l} className="px-6 py-3">{l}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {run.confusion_matrix.matrix.map((row: number[], i: number) => (
                    <tr key={i} className="border-b border-gray-700">
                      <th className="px-6 py-4 font-medium text-white bg-gray-900 whitespace-nowrap">
                        {run.confusion_matrix.labels[i]}
                      </th>
                      {row.map((val: number, j: number) => (
                        <td key={j} className={`px-6 py-4 text-center ${i === j ? 'bg-green-900/20 text-green-400 font-bold' : val > 0 ? 'bg-red-900/20 text-red-400 font-bold' : ''}`}>
                          {val}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
             </table>
          </div>
        </>
      )}
    </div>
  );
}

function MetricCard({ title, value }: { title: string, value: string | number }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      <div className="text-gray-400 text-xs font-medium uppercase tracking-wider">{title}</div>
      <div className="text-2xl font-bold text-white mt-1">{value}</div>
    </div>
  );
}
