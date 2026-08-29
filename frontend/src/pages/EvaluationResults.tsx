import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { Loader2, CheckCircle2, XCircle, AlertCircle, RefreshCw, ArrowLeft } from 'lucide-react';

const API_URL = "/api";

export function EvaluationResults() {
  const { id } = useParams();

  const { data: run, isLoading } = useQuery({
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
    return (
      <div className="flex justify-center p-16">
        <Loader2 className="w-6 h-6 text-zinc-400 animate-spin" />
      </div>
    );
  }

  const isRunning = run?.status === 'RUNNING' || run?.status === 'STARTING';

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div className="flex justify-between items-center border-b border-zinc-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              <span>Benchmark Results</span>
              {isRunning && <RefreshCw className="w-4 h-4 text-zinc-400 animate-spin" />}
            </h1>
            <span className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-medium ${
              run?.status === 'COMPLETED' ? 'bg-zinc-900 border border-zinc-700 text-zinc-200' :
              run?.status === 'FAILED' ? 'bg-zinc-900 border border-zinc-800 text-zinc-400' :
              'bg-zinc-900 border border-zinc-700 text-white'
            }`}>
              {run?.status}
            </span>
          </div>
          <p className="text-xs text-zinc-400 font-mono mt-1">ID: {run?.id}</p>
        </div>

        <Link to="/datasets" className="text-xs text-zinc-400 hover:text-white flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Datasets
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel p-5 space-y-1">
          <div className="text-xs text-zinc-400 uppercase tracking-wider">Total Samples</div>
          <div className="text-2xl font-bold text-white font-mono">{run?.total_samples || 0}</div>
        </div>
        <div className="glass-panel p-5 space-y-1">
          <div className="text-xs text-zinc-400 uppercase tracking-wider">Completed Samples</div>
          <div className="text-2xl font-bold text-white font-mono flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <span>{run?.completed_samples || 0}</span>
          </div>
        </div>
        <div className="glass-panel p-5 space-y-1">
          <div className="text-xs text-zinc-400 uppercase tracking-wider">Benchmark Progress</div>
          <div className="text-2xl font-bold text-white font-mono">
            {run?.total_samples ? Math.round(((run?.completed_samples || 0) / run.total_samples) * 100) : 0}%
          </div>
        </div>
      </div>

      {run?.metrics && (
        <div className="glass-panel p-5 space-y-4">
          <h2 className="text-sm font-semibold text-white">Evaluation Metrics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-zinc-900/60 border border-zinc-800 p-3 rounded">
              <div className="text-[10px] text-zinc-400 uppercase font-mono">Accuracy</div>
              <div className="text-lg font-bold text-white font-mono mt-1">
                {run.metrics.accuracy ? `${(run.metrics.accuracy * 100).toFixed(1)}%` : 'N/A'}
              </div>
            </div>
            <div className="bg-zinc-900/60 border border-zinc-800 p-3 rounded">
              <div className="text-[10px] text-zinc-400 uppercase font-mono">Precision</div>
              <div className="text-lg font-bold text-white font-mono mt-1">
                {run.metrics.precision ? `${(run.metrics.precision * 100).toFixed(1)}%` : 'N/A'}
              </div>
            </div>
            <div className="bg-zinc-900/60 border border-zinc-800 p-3 rounded">
              <div className="text-[10px] text-zinc-400 uppercase font-mono">Recall</div>
              <div className="text-lg font-bold text-white font-mono mt-1">
                {run.metrics.recall ? `${(run.metrics.recall * 100).toFixed(1)}%` : 'N/A'}
              </div>
            </div>
            <div className="bg-zinc-900/60 border border-zinc-800 p-3 rounded">
              <div className="text-[10px] text-zinc-400 uppercase font-mono">F1-Score</div>
              <div className="text-lg font-bold text-white font-mono mt-1">
                {run.metrics.f1_score ? `${(run.metrics.f1_score * 100).toFixed(1)}%` : 'N/A'}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
