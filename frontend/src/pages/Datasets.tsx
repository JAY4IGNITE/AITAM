import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Database, Upload, FileJson, BarChart3, Loader2, Play } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API_URL = "http://localhost:8000/api";

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
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white">Datasets</h1>
          <p className="text-gray-400 mt-2">Manage datasets for evaluation and validation.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 h-fit">
          <h2 className="text-lg font-medium text-white mb-4 flex items-center gap-2">
            <Upload className="w-5 h-5 text-blue-400" />
            Import Dataset
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Dataset Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="e.g. PhishTank 2024"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">File (CSV, JSON, JSONL)</label>
              <input
                type="file"
                accept=".csv,.json,.jsonl"
                onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
                className="w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-gray-700 file:text-white hover:file:bg-gray-600 cursor-pointer"
              />
            </div>
            <button
              onClick={() => uploadMutation.mutate()}
              disabled={!file || !name || uploadMutation.isPending}
              className="w-full bg-blue-600 text-white rounded-md py-2 font-medium hover:bg-blue-700 disabled:opacity-50 flex justify-center items-center gap-2 transition-colors"
            >
              {uploadMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
              {uploadMutation.isPending ? 'Importing...' : 'Upload Dataset'}
            </button>
          </div>
        </div>

        {/* Dataset List */}
        <div className="lg:col-span-2 space-y-4">
          {isLoading ? (
            <div className="flex justify-center p-8">
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
          ) : datasets?.length === 0 ? (
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-12 text-center">
              <Database className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-300">No datasets found</h3>
              <p className="text-gray-500 mt-1">Upload a dataset to start evaluating the platform.</p>
            </div>
          ) : (
            datasets?.map((ds: any) => (
              <div key={ds.id} className="bg-gray-800 border border-gray-700 rounded-lg p-5 flex items-center justify-between hover:border-gray-600 transition-colors">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-gray-900 rounded-lg">
                    <FileJson className="w-6 h-6 text-indigo-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-white">{ds.name}</h3>
                    <div className="flex gap-4 mt-1 text-sm text-gray-400">
                      <span>{ds.sample_count.toLocaleString()} samples</span>
                      <span>Uploaded {new Date(ds.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button 
                    onClick={() => navigate(`/evaluation/run?dataset=${ds.id}`)}
                    className="flex items-center gap-2 px-4 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 transition-colors text-sm font-medium"
                  >
                    <Play className="w-4 h-4" />
                    Evaluate
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
