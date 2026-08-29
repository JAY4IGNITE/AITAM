import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { 
  GraduationCap, BookOpen, CheckCircle, HelpCircle, AlertCircle, 
  ArrowRight, Award, ShieldAlert, Sparkles, Check, X
} from 'lucide-react';

export const Education = () => {
  const [selectedModuleId, setSelectedModuleId] = useState<string>('phishing-fundamentals');
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [quizResult, setQuizResult] = useState<any | null>(null);

  const { data: modules, isLoading } = useQuery({
    queryKey: ['education-modules'],
    queryFn: () => fetch('/api/education/modules').then(res => res.json())
  });

  const submitQuizMutation = useMutation({
    mutationFn: async ({ moduleId, answers }: { moduleId: string; answers: any[] }) => {
      const res = await fetch('/api/education/quizzes/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module_id: moduleId, answers })
      });
      if (!res.ok) throw new Error('Failed to submit quiz');
      return res.json();
    },
    onSuccess: (data) => {
      setQuizResult(data);
    }
  });

  const currentModule = modules?.find((m: any) => m.id === selectedModuleId) || modules?.[0];

  const handleSelectOption = (questionId: string, optionId: string) => {
    setSelectedAnswers(prev => ({ ...prev, [questionId]: optionId }));
  };

  const handleSubmitQuiz = () => {
    if (!currentModule) return;
    const answersPayload = Object.entries(selectedAnswers).map(([qId, optId]) => ({
      question_id: qId,
      selected_option_id: optId
    }));
    submitQuizMutation.mutate({ moduleId: currentModule.id, answers: answersPayload });
  };

  const handleSwitchModule = (id: string) => {
    setSelectedModuleId(id);
    setSelectedAnswers({});
    setQuizResult(null);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <GraduationCap className="w-8 h-8 text-primary" />
            Cybersecurity Awareness & Training
          </h1>
          <p className="text-gray-400 mt-1">Master phishing defenses, QR quishing detection, Punycode identification, and test your skills with interactive SOC quizzes.</p>
        </div>
      </div>

      {/* Module Navigation Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {modules?.map((m: any) => (
          <button
            key={m.id}
            onClick={() => handleSwitchModule(m.id)}
            className={`glass-panel p-5 text-left border transition relative flex flex-col justify-between ${
              selectedModuleId === m.id 
                ? 'border-primary bg-primary/10 shadow-[0_0_15px_rgba(59,130,246,0.2)]' 
                : 'border-white/5 hover:border-white/20'
            }`}
          >
            <div>
              <span className="text-[10px] uppercase font-bold text-primary tracking-wider font-mono">{m.category}</span>
              <h3 className="font-bold text-white text-base mt-1 mb-2">{m.title}</h3>
              <p className="text-xs text-gray-400 line-clamp-2">{m.summary}</p>
            </div>
            <div className="mt-4 flex items-center justify-between text-xs text-gray-500">
              <span>{m.difficulty}</span>
              <span className="text-primary font-semibold flex items-center gap-1">Learn <ArrowRight className="w-3 h-3" /></span>
            </div>
          </button>
        ))}
      </div>

      {/* Main Content Area */}
      {currentModule && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Left: Study Guide */}
          <div className="lg:col-span-7 space-y-6">
            
            <div className="glass-panel p-6 border border-white/10 space-y-6">
              <div>
                <div className="flex items-center gap-2 text-primary font-semibold text-xs uppercase tracking-wider mb-1">
                  <BookOpen className="w-4 h-4" /> Study Guide
                </div>
                <h2 className="text-2xl font-bold text-white">{currentModule.title}</h2>
                <p className="text-sm text-gray-300 mt-2 leading-relaxed">{currentModule.summary}</p>
              </div>

              {/* Key Threat Indicators */}
              <div className="bg-black/40 border border-white/5 p-4 rounded-lg space-y-2">
                <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4" /> Key Threat Indicators
                </h4>
                <ul className="space-y-1.5 text-xs text-gray-300">
                  {currentModule.key_indicators?.map((ind: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-amber-400 font-bold">•</span>
                      <span>{ind}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Prevention Strategies */}
              <div className="bg-black/40 border border-white/5 p-4 rounded-lg space-y-2">
                <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4" /> Recommended Defense Best Practices
                </h4>
                <ul className="space-y-1.5 text-xs text-gray-300">
                  {currentModule.prevention_tips?.map((tip: string, i: number) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-emerald-400 font-bold">•</span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Real World Scenario */}
              <div className="border-l-2 border-primary pl-4 py-1 text-xs text-gray-400 italic">
                <span className="font-bold text-gray-300 not-italic block mb-1">Real-World Case Scenario:</span>
                "{currentModule.real_world_example}"
              </div>
            </div>

          </div>

          {/* Right: Interactive Knowledge Quiz */}
          <div className="lg:col-span-5 space-y-6">
            
            <div className="glass-panel p-6 border border-white/10 space-y-6">
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div className="flex items-center gap-2">
                  <Award className="w-5 h-5 text-primary" />
                  <h3 className="text-lg font-bold text-white">Knowledge Check</h3>
                </div>
                <span className="text-xs font-mono text-gray-400">{currentModule.quizzes?.length} Questions</span>
              </div>

              {quizResult && (
                <div className={`p-4 rounded-lg border text-sm font-semibold flex items-center justify-between ${
                  quizResult.passed ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-red-500/20 text-red-400 border-red-500/30'
                }`}>
                  <div className="flex items-center gap-2">
                    {quizResult.passed ? <CheckCircle className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                    <span>{quizResult.passed ? 'Quiz Passed!' : 'Quiz Needs Review'} ({quizResult.score}/{quizResult.total} Correct - {quizResult.percentage}%)</span>
                  </div>
                  <button 
                    onClick={() => { setQuizResult(null); setSelectedAnswers({}); }}
                    className="text-xs underline hover:opacity-80"
                  >
                    Retake
                  </button>
                </div>
              )}

              <div className="space-y-6">
                {currentModule.quizzes?.map((q: any, qIdx: number) => {
                  const qResult = quizResult?.results?.find((r: any) => r.question_id === q.id);
                  return (
                    <div key={q.id} className="space-y-3">
                      <p className="text-sm font-semibold text-white">
                        <span className="text-primary font-mono mr-1.5">{qIdx + 1}.</span> {q.question}
                      </p>

                      <div className="space-y-2">
                        {q.options?.map((opt: any) => {
                          const isSelected = selectedAnswers[q.id] === opt.id;
                          const isCorrect = qResult && opt.id === qResult.correct_option_id;
                          const isWrongSelection = qResult && isSelected && !qResult.is_correct;

                          return (
                            <button
                              key={opt.id}
                              disabled={!!quizResult}
                              onClick={() => handleSelectOption(q.id, opt.id)}
                              className={`w-full p-3 rounded-lg text-left text-xs font-medium border transition flex items-start justify-between ${
                                isCorrect ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300' :
                                isWrongSelection ? 'bg-red-500/20 border-red-500/40 text-red-300' :
                                isSelected ? 'bg-primary/20 border-primary text-white' :
                                'bg-black/40 border-white/5 text-gray-300 hover:border-white/20'
                              }`}
                            >
                              <span>{opt.text}</span>
                              {isCorrect && <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />}
                              {isWrongSelection && <X className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />}
                            </button>
                          );
                        })}
                      </div>

                      {qResult && (
                        <div className="text-xs bg-white/5 border border-white/10 p-3 rounded text-gray-300 font-mono">
                          <span className="font-bold text-primary block mb-0.5">Explanation:</span>
                          {qResult.explanation}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {!quizResult && (
                <button
                  onClick={handleSubmitQuiz}
                  disabled={Object.keys(selectedAnswers).length < (currentModule.quizzes?.length || 1) || submitQuizMutation.isPending}
                  className="w-full bg-primary text-primary-foreground font-bold py-2.5 rounded-md hover:bg-primary/90 transition shadow-[0_0_20px_rgba(59,130,246,0.3)] disabled:opacity-40 text-xs uppercase tracking-wider"
                >
                  {submitQuizMutation.isPending ? 'Evaluating...' : 'Submit Answers'}
                </button>
              )}
            </div>

          </div>

        </div>
      )}

    </div>
  );
};
