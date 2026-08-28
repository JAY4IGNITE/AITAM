import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Play, Settings, Loader2 } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const API_URL = "http://localhost:8000/api";

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
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-white">Configure Evaluation</h1>
        <p className="text-gray-400 mt-2">Run the multi-agent SOC pipeline against the dataset.</p>
      </div>

      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h2 className="text-lg font-medium text-white mb-6 flex items-center gap-2">
          <Settings className="w-5 h-5 text-gray-400" />
          Execution Parameters
        </h2>
        
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Sample Limit</label>
            <input 
              type="number" 
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
              className="w-full bg-gray-900 border border-gray-700 rounded-md px-4 py-2 text-white"
            />
            <p className="text-xs text-gray-500 mt-1">Limit the number of samples to process (useful for testing).</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Parallelism (Concurrency)</label>
            <input 
              type="number" 
              value={parallelism}
              onChange={(e) => setParallelism(parseInt(e.target.value))}
              max={10}
              min={1}
              className="w-full bg-gray-900 border border-gray-700 rounded-md px-4 py-2 text-white"
            />
            <p className="text-xs text-gray-500 mt-1">Number of concurrent sandboxes/agents to run. Max 10.</p>
          </div>

          <button
            onClick={() => runMutation.mutate()}
            disabled={runMutation.isPending || !datasetId}
            className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex justify-center items-center gap-2"
          >
            {runMutation.isPending ? <Loader2 className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5" />}
            {runMutation.isPending ? 'Starting Evaluation...' : 'Run Evaluation'}
          </button>
        </div>
      </div>
    </div>
  );
}
