import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  FileWarning, Plus, Search, Filter, CheckCircle, Clock, 
  AlertCircle, ShieldCheck, MessageSquare, ChevronLeft, ChevronRight, X
} from 'lucide-react';

export const Reports = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State
  const [indicator, setIndicator] = useState('');
  const [reportType, setReportType] = useState('URL');
  const [description, setDescription] = useState('');
  const [reporterEmail, setReporterEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [formMsg, setFormMsg] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['threat-reports', page, statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '10',
        ...(statusFilter ? { status: statusFilter } : {})
      });
      const res = await fetch(`/api/reports?${params.toString()}`);
      if (!res.ok) throw new Error('Failed to load reports');
      return res.json();
    }
  });

  const updateStatusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      const res = await fetch(`/api/reports/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
      });
      if (!res.ok) throw new Error('Failed to update status');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['threat-reports'] });
    }
  });

  const handleCreateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!indicator || !description) return;
    setSubmitting(true);
    setFormMsg('');
    try {
      const res = await fetch('/api/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          indicator,
          report_type: reportType,
          description,
          reporter_email: reporterEmail || undefined
        })
      });
      if (!res.ok) throw new Error('Failed to submit report');
      setFormMsg('Report submitted successfully.');
      queryClient.invalidateQueries({ queryKey: ['threat-reports'] });
      setTimeout(() => {
        setIsModalOpen(false);
        setIndicator('');
        setDescription('');
        setReporterEmail('');
        setFormMsg('');
      }, 1200);
    } catch (err: any) {
      setFormMsg(`Error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <span className="bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2.5 py-0.5 rounded text-xs font-bold flex items-center gap-1"><Clock className="w-3 h-3" /> PENDING</span>;
      case 'REVIEWED':
        return <span className="bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2.5 py-0.5 rounded text-xs font-bold flex items-center gap-1"><ShieldCheck className="w-3 h-3" /> REVIEWED</span>;
      case 'RESOLVED':
        return <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2.5 py-0.5 rounded text-xs font-bold flex items-center gap-1"><CheckCircle className="w-3 h-3" /> RESOLVED</span>;
      default:
        return <span className="bg-gray-500/20 text-gray-400 px-2.5 py-0.5 rounded text-xs">{status}</span>;
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <FileWarning className="w-8 h-8 text-primary" />
            Threat Reports Queue
          </h1>
          <p className="text-gray-400 mt-1">Review user-submitted phishing reports and track mitigation triage.</p>
        </div>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-primary text-primary-foreground font-semibold px-5 py-2.5 rounded-md hover:bg-primary/90 transition shadow-[0_0_20px_rgba(59,130,246,0.3)] flex items-center gap-2 text-sm"
        >
          <Plus className="w-4 h-4" />
          Submit Threat Report
        </button>
      </div>

      {/* Filter Bar */}
      <div className="glass-panel p-4 border border-white/10 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <Filter className="w-4 h-4 text-gray-500" />
          <span>Status Filter:</span>
        </div>
        <div className="flex gap-2">
          {['', 'PENDING', 'REVIEWED', 'RESOLVED'].map((st) => (
            <button
              key={st}
              onClick={() => { setStatusFilter(st); setPage(1); }}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                statusFilter === st ? 'bg-primary text-primary-foreground' : 'bg-white/5 text-gray-400 hover:bg-white/10'
              }`}
            >
              {st || 'All Reports'}
            </button>
          ))}
        </div>
      </div>

      {/* Reports Table */}
      <div className="glass-panel overflow-hidden border border-white/10">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-white/5 text-gray-400 uppercase tracking-wider font-sans text-[11px]">
              <tr>
                <th className="px-6 py-4">Indicator</th>
                <th className="px-6 py-4">Type</th>
                <th className="px-6 py-4">Description</th>
                <th className="px-6 py-4">Reporter</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Submitted</th>
                <th className="px-6 py-4 text-right">Triage Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {isLoading ? (
                <tr><td colSpan={7} className="text-center py-12 text-gray-500 font-sans">Loading reports queue...</td></tr>
              ) : data?.items?.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-12 text-gray-500 font-sans">No threat reports found in queue.</td></tr>
              ) : (
                data?.items?.map((report: any) => (
                  <tr key={report.id} className="hover:bg-white/5 transition">
                    <td className="px-6 py-4 font-bold text-white max-w-xs truncate" title={report.indicator}>
                      {report.indicator}
                    </td>
                    <td className="px-6 py-4 font-sans text-gray-300 font-medium">
                      {report.report_type}
                    </td>
                    <td className="px-6 py-4 font-sans text-gray-400 max-w-sm truncate" title={report.description}>
                      {report.description}
                    </td>
                    <td className="px-6 py-4 text-gray-500 font-sans">
                      {report.reporter_email || 'Anonymous'}
                    </td>
                    <td className="px-6 py-4 font-sans">
                      {getStatusBadge(report.status)}
                    </td>
                    <td className="px-6 py-4 text-gray-500 font-sans">
                      {new Date(report.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right font-sans">
                      <select
                        className="bg-black/50 border border-white/10 rounded px-2 py-1 text-xs text-gray-300 focus:outline-none"
                        value={report.status}
                        onChange={(e) => updateStatusMutation.mutate({ id: report.id, status: e.target.value })}
                      >
                        <option value="PENDING">PENDING</option>
                        <option value="REVIEWED">REVIEWED</option>
                        <option value="RESOLVED">RESOLVED</option>
                      </select>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="p-4 border-t border-white/10 flex items-center justify-between text-xs text-gray-400">
            <div>Showing page {data.page} of {data.pages} ({data.total} total reports)</div>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                className="bg-white/5 px-3 py-1.5 rounded border border-white/10 disabled:opacity-30 flex items-center gap-1"
              >
                <ChevronLeft className="w-3.5 h-3.5" /> Previous
              </button>
              <button
                disabled={page >= data.pages}
                onClick={() => setPage(p => p + 1)}
                className="bg-white/5 px-3 py-1.5 rounded border border-white/10 disabled:opacity-30 flex items-center gap-1"
              >
                Next <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modal Dialog */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="glass-panel w-full max-w-lg p-6 border border-white/20 shadow-2xl relative animate-in fade-in zoom-in-95">
            <button 
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 text-gray-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
              <FileWarning className="w-5 h-5 text-primary" /> Submit Suspicious Threat
            </h2>
            <p className="text-xs text-gray-400 mb-6">Report a phishing link, spoofed email, or malicious artifact for analyst review.</p>

            {formMsg && (
              <div className={`p-3 rounded mb-4 text-xs font-semibold ${
                formMsg.startsWith('Error') ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
              }`}>
                {formMsg}
              </div>
            )}

            <form onSubmit={handleCreateReport} className="space-y-4 text-xs font-sans">
              <div>
                <label className="block text-gray-300 font-semibold mb-1">Target Indicator (URL / Domain / Sender)</label>
                <input 
                  type="text"
                  required
                  placeholder="e.g. http://login-secure-apple.top"
                  className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white font-mono focus:border-primary focus:outline-none"
                  value={indicator}
                  onChange={e => setIndicator(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Report Type</label>
                  <select
                    className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white focus:border-primary focus:outline-none"
                    value={reportType}
                    onChange={e => setReportType(e.target.value)}
                  >
                    <option value="URL">URL / Link</option>
                    <option value="EMAIL">Email Phishing</option>
                    <option value="SMS">SMS Smishing</option>
                    <option value="QR">QR Code</option>
                    <option value="WEBPAGE">Web Page</option>
                    <option value="SOCIAL">Social Media</option>
                  </select>
                </div>
                <div>
                  <label className="block text-gray-300 font-semibold mb-1">Reporter Email (Optional)</label>
                  <input 
                    type="email"
                    placeholder="analyst@company.com"
                    className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white focus:border-primary focus:outline-none"
                    value={reporterEmail}
                    onChange={e => setReporterEmail(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label className="block text-gray-300 font-semibold mb-1">Incident Description / Observations</label>
                <textarea 
                  required
                  rows={4}
                  placeholder="Describe why this content is suspicious (e.g. fake login page asking for 2FA)..."
                  className="w-full bg-black/50 border border-white/10 rounded p-3 text-white focus:border-primary focus:outline-none resize-none"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                />
              </div>

              <div className="flex justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="bg-primary text-primary-foreground font-bold px-6 py-2 rounded hover:bg-primary/90 transition disabled:opacity-50"
                >
                  {submitting ? 'Submitting...' : 'Submit Report'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
