import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Database, Upload, FileJson, BarChart3, Loader2, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API_URL = "/api";

export function Datasets() {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: async () => {
      const res = await fetch(`${API_URL}/datasets/`);
      if (!res.ok) throw new Error('Failed to fetch datasets');
      return res.json();
    }
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!file || !name) return;
      const formData = new FormData();
      formData.append('file', file);
      formData.append('name', name);
      const res = await fetch(`${API_URL}/datasets/import`, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      setFile(null);
      setName('');
    }
  });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-300">
      <div className="flex justify-between items-center border-b border-zinc-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Benchmark Datasets</h1>
          <p className="text-xs text-zinc-400 mt-1">Manage threat datasets for validation, precision benchmarking, and SOC performance evaluation.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form */}
        <div className="glass-panel p-5 h-fit space-y-4">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Upload className="w-4 h-4 text-zinc-400" />
            <span>Import Dataset</span>
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">Dataset Name</label>
              <input 
                type="text" 
                value={name} 
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. PhishTank 2026 Q1 Corpus"
                className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-zinc-600"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">JSON Dataset File</label>
              <input 
                type="file" 
                accept=".json"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                className="w-full bg-zinc-900 border border-zinc-800 rounded p-2 text-xs text-zinc-400 file:mr-3 file:py-1 file:px-2.5 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-zinc-800 file:text-white hover:file:bg-zinc-700 cursor-pointer"
              />
            </div>
            <button
              onClick={() => uploadMutation.mutate()}
              disabled={!file || !name || uploadMutation.isPending}
              className="w-full bg-white hover:bg-zinc-200 text-zinc-950 font-semibold py-2 px-4 rounded text-xs transition disabled:opacity-40 flex items-center justify-center gap-2"
            >
              {uploadMutation.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>Import Dataset</span>
            </button>
          </div>
        </div>

        {/* Datasets List */}
        <div className="lg:col-span-2 space-y-3">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Database className="w-4 h-4 text-zinc-400" />
            <span>Available Datasets ({datasets?.length || 0})</span>
          </h2>

          {isLoading ? (
            <div className="p-8 text-center text-xs font-mono text-zinc-500">Loading datasets...</div>
          ) : datasets?.length === 0 ? (
            <div className="glass-panel p-8 text-center text-xs text-zinc-400">
              No datasets found. Import a JSON dataset to run evaluations.
            </div>
          ) : (
            <div className="space-y-3">
              {datasets?.map((ds: any) => (
                <div key={ds.id} className="glass-panel p-4 flex justify-between items-center">
                  <div className="space-y-1">
                    <div className="text-xs font-semibold text-white">{ds.name}</div>
                    <div className="text-[11px] text-zinc-400 font-mono">
                      {ds.samples_count ?? 0} samples • Created {new Date(ds.created_at || Date.now()).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => navigate(`/evaluation/run?dataset=${ds.id}`)}
                      className="bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-800 text-xs px-3 py-1.5 rounded transition flex items-center gap-1.5"
                    >
                      <Play className="w-3 h-3 fill-current" />
                      <span>Run Eval</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
