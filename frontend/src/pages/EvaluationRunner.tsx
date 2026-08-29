import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Play, Settings, Loader2, ArrowLeft } from 'lucide-react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';

const API_URL = "/api";

export function EvaluationRunner() {
  const [searchParams] = useSearchParams();
  const datasetId = searchParams.get('dataset');
  const navigate = useNavigate();

  const [parallelism, setParallelism] = useState(2);
  const [limit, setLimit] = useState(100);

  const runMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`${API_URL}/evaluation/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: datasetId,
          sample_limit: limit,
          parallelism: parallelism
        })
      });
      if (!res.ok) throw new Error('Failed to start evaluation');
      return res.json();
    },
    onSuccess: (data) => {
      navigate(`/evaluation/${data.evaluation_id}`);
    }
  });

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div className="flex items-center justify-between border-b border-zinc-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Configure Benchmark Run</h1>
          <p className="text-xs text-zinc-400 mt-1">Execute the multi-agent SOC pipeline against the benchmark dataset.</p>
        </div>
        <Link to="/datasets" className="text-xs text-zinc-400 hover:text-white flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Datasets
        </Link>
      </div>

      <div className="glass-panel p-6 space-y-6">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Settings className="w-4 h-4 text-zinc-400" />
          <span>Execution Parameters</span>
        </h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Sample Limit</label>
            <input 
              type="number" 
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
              className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-zinc-600"
            />
            <p className="text-[11px] text-zinc-500 mt-1">Limit the number of samples to process from the corpus.</p>
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-300 mb-1">Parallel Swarm Workers</label>
            <input 
              type="number" 
              value={parallelism}
              onChange={(e) => setParallelism(parseInt(e.target.value))}
              className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-xs text-white focus:outline-none focus:border-zinc-600"
            />
            <p className="text-[11px] text-zinc-500 mt-1">Number of parallel worker coroutines dispatching multi-agent investigations.</p>
          </div>

          <div className="pt-2">
            <button
              onClick={() => runMutation.mutate()}
              disabled={runMutation.isPending || !datasetId}
              className="w-full bg-white hover:bg-zinc-200 text-zinc-950 font-semibold py-2.5 px-4 rounded text-xs transition disabled:opacity-40 flex items-center justify-center gap-2"
            >
              {runMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4 fill-current" />
              )}
              <span>{runMutation.isPending ? 'Starting Swarm...' : 'Start Evaluation Run'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
