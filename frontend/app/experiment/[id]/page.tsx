'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { format, parseISO } from 'date-fns';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { getExperiment, getExperimentProgress, type ExperimentResult, type IntervalResult, type ExperimentProgress } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Loader2,
  Code,
  FileText,
  ExternalLink,
  Sparkles,
  BookOpen,
} from 'lucide-react';

export default function ExperimentPage() {
  const params = useParams();
  const router = useRouter();
  const experimentId = params.id as string;

  const [experiment, setExperiment] = useState<ExperimentResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedInterval, setSelectedInterval] = useState<IntervalResult | null>(null);
  const [activeTab, setActiveTab] = useState<'reasoning' | 'evidence'>('reasoning');
  const [progress, setProgress] = useState<ExperimentProgress | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    if (experimentId) {
      loadExperiment();
      checkProgress();
    }
  }, [experimentId]);

  const checkProgress = async () => {
    try {
      const progressData = await getExperimentProgress(experimentId);
      setProgress(progressData);
      setIsRunning(progressData.status === 'running');
      
      if (progressData.status === 'running') {
        // Poll for progress updates
        const pollInterval = setInterval(async () => {
          try {
            const updatedProgress = await getExperimentProgress(experimentId);
            setProgress(updatedProgress);
            if (updatedProgress.status !== 'running') {
              setIsRunning(false);
              clearInterval(pollInterval);
              // Reload experiment data
              loadExperiment();
            }
          } catch (err) {
            console.error('Failed to fetch progress:', err);
            clearInterval(pollInterval);
            setIsRunning(false);
          }
        }, 2000);
        
        return () => clearInterval(pollInterval);
      }
    } catch (err) {
      // Experiment might be completed or not found
      setIsRunning(false);
    }
  };

  const loadExperiment = async () => {
    try {
      setLoading(true);
      const data = await getExperiment(experimentId);
      setExperiment(data);
      if (data.timeline.length > 0) {
        setSelectedInterval(data.timeline[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load experiment');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-600 dark:text-blue-400 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading experiment...</p>
        </div>
      </div>
    );
  }

  if (error || (!experiment && !isRunning)) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">Error</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-4">{error || 'Experiment not found'}</p>
              <Button onClick={() => router.push('/')} variant="primary">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Home
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show progress if experiment is running
  if (isRunning && progress) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
        <div className="container mx-auto px-4 py-12 max-w-6xl">
          <div className="mb-6">
            <Button onClick={() => router.push('/')} variant="outline" className="mb-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
          </div>
          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Experiment Running</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Progress
                  </span>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {progress.completed_intervals}/{progress.total_intervals} intervals
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                  <div
                    className="bg-blue-600 dark:bg-blue-400 h-4 rounded-full transition-all duration-300"
                    style={{ width: `${progress.progress_percent}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                  <span>{progress.progress_percent.toFixed(1)}% complete</span>
                  <span>
                    {Math.floor(progress.elapsed_seconds / 60)}m{' '}
                    {Math.floor(progress.elapsed_seconds % 60)}s elapsed
                  </span>
                </div>
                {progress.failed_intervals > 0 && (
                  <div className="text-sm text-orange-600 dark:text-orange-400">
                    ⚠️ {progress.failed_intervals} interval(s) failed
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const chartData = experiment.timeline.map((interval) => ({
    time: format(parseISO(interval.timestamp), 'MMM dd HH:mm'),
    timestamp: interval.timestamp,
    marketOdds: interval.market_state.price,
    modelProbability: interval.aggregated_confidence,
    decision: interval.aggregated_decision,
    edge: interval.aggregated_confidence - interval.market_state.price,
  }));

  // Calculate summary stats
  const totalIntervals = experiment.timeline.length;
  const yesDecisions = experiment.timeline.filter((i) => i.aggregated_decision === 'YES').length;
  const avgConfidence =
    experiment.timeline.reduce((sum, i) => sum + i.aggregated_confidence, 0) / totalIntervals;
  const avgEdge =
    experiment.timeline.reduce((sum, i) => sum + (i.aggregated_confidence - i.market_state.price), 0) /
    totalIntervals;

  // Find breaking points (decision changes)
  const breakingPoints = experiment.timeline
    .map((interval, index) => {
      if (index === 0) return null;
      const prev = experiment.timeline[index - 1];
      if (prev.aggregated_decision !== interval.aggregated_decision) {
        return { index, timestamp: interval.timestamp, decision: interval.aggregated_decision };
      }
      return null;
    })
    .filter(Boolean) as Array<{ index: number; timestamp: string; decision: 'YES' | 'NO' }>;

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-lg">
          <p className="font-semibold mb-2">{data.time}</p>
          <div className="space-y-1 text-sm">
            <p className="text-blue-600 dark:text-blue-400">
              Market Odds: <span className="font-semibold">{(data.marketOdds * 100).toFixed(1)}%</span>
            </p>
            <p className="text-purple-600 dark:text-purple-400">
              Model Probability: <span className="font-semibold">{(data.modelProbability * 100).toFixed(1)}%</span>
            </p>
            <p className="text-gray-600 dark:text-gray-400">
              Decision: <span className="font-semibold">{data.decision}</span>
            </p>
            <p className={data.edge >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>
              Edge: <span className="font-semibold">{(data.edge * 100).toFixed(1)}%</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => router.push('/')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                {experiment.config.market_slug}
              </h1>
              <div className="flex flex-wrap gap-4 text-sm text-gray-600 dark:text-gray-400">
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {format(parseISO(experiment.config.start_time), 'MMM dd, yyyy HH:mm')} -{' '}
                  {format(parseISO(experiment.config.end_time), 'MMM dd, yyyy HH:mm')}
                </span>
                <span className="flex items-center gap-1">
                  <Target className="w-4 h-4" />
                  {experiment.config.interval_minutes} min intervals
                </span>
                <span className="capitalize">{experiment.config.mode.replace('_', ' ')}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-1">
                  {totalIntervals}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Intervals</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400 mb-1">
                  {yesDecisions}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">YES Decisions</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600 dark:text-purple-400 mb-1">
                  {(avgConfidence * 100).toFixed(1)}%
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Avg Confidence</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div
                  className={`text-2xl font-bold mb-1 ${
                    avgEdge >= 0
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {avgEdge >= 0 ? '+' : ''}
                  {(avgEdge * 100).toFixed(1)}%
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Avg Edge</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Chart Section */}
        <Card variant="elevated" className="mb-8">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Timeline Analysis</CardTitle>
              {selectedInterval && (
                <div className="flex items-center gap-3 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600 dark:text-gray-400">Selected:</span>
                    <span className="font-semibold text-gray-900 dark:text-gray-100">
                      {format(parseISO(selectedInterval.timestamp), 'MMM dd, HH:mm')}
                    </span>
                  </div>
                  <div
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      selectedInterval.aggregated_decision === 'YES'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                        : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                    }`}
                  >
                    {selectedInterval.aggregated_decision}
                  </div>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={500}>
              <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="time"
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280' }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis
                  stroke="#6b7280"
                  tick={{ fill: '#6b7280' }}
                  domain={[0, 1]}
                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="marketOdds"
                  name="Market Odds"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="modelProbability"
                  name="Model Probability"
                  stroke="#9333ea"
                  strokeWidth={2}
                  dot={{ r: 4, fill: '#9333ea' }}
                  activeDot={{ r: 6 }}
                />
                {breakingPoints.map((bp, idx) => (
                  <ReferenceLine
                    key={idx}
                    x={format(parseISO(bp.timestamp), 'MMM dd HH:mm')}
                    stroke="#ef4444"
                    strokeDasharray="3 3"
                    label={{ value: 'Break', position: 'top' }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>

            {/* Chart Legend with Decision Colors */}
            <div className="mt-6 flex flex-wrap gap-2 justify-center">
              {chartData.map((point, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    const interval = experiment.timeline.find((i) => i.timestamp === point.timestamp);
                    if (interval) setSelectedInterval(interval);
                  }}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    selectedInterval?.timestamp === point.timestamp
                      ? 'ring-2 ring-blue-500 scale-105 shadow-md'
                      : 'hover:scale-105 hover:shadow-sm'
                  } ${
                    point.decision === 'YES'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                      : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                  }`}
                >
                  {point.time}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Reasoning & Evidence Section - Full Width Below Chart */}
        {selectedInterval && (
          <div className="space-y-8">
            {/* Interval Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Timestamp</p>
                    <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {format(parseISO(selectedInterval.timestamp), 'MMM dd, HH:mm')}
                    </p>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Market Odds</p>
                    <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
                      {(selectedInterval.market_state.price * 100).toFixed(1)}%
                    </p>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Model Confidence</p>
                    <p className="text-lg font-bold text-purple-600 dark:text-purple-400">
                      {(selectedInterval.aggregated_confidence * 100).toFixed(1)}%
                    </p>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Edge</p>
                    <p
                      className={`text-lg font-bold ${
                        selectedInterval.aggregated_confidence - selectedInterval.market_state.price >= 0
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-red-600 dark:text-red-400'
                      }`}
                    >
                      {selectedInterval.aggregated_confidence - selectedInterval.market_state.price >= 0 ? '+' : ''}
                      {((selectedInterval.aggregated_confidence - selectedInterval.market_state.price) * 100).toFixed(1)}%
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Tabs for Reasoning and Evidence */}
            <div className="border-b border-gray-200 dark:border-gray-800">
              <div className="flex gap-1">
                <button
                  onClick={() => setActiveTab('reasoning')}
                  className={`px-6 py-4 font-medium text-base transition-all relative ${
                    activeTab === 'reasoning'
                      ? 'text-gray-900 dark:text-gray-100'
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5" />
                    <span>Reasoning</span>
                  </div>
                  {activeTab === 'reasoning' && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gray-900 dark:bg-gray-100" />
                  )}
                </button>
                <button
                  onClick={() => setActiveTab('evidence')}
                  className={`px-6 py-4 font-medium text-base transition-all relative ${
                    activeTab === 'evidence'
                      ? 'text-gray-900 dark:text-gray-100'
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-5 h-5" />
                    <span>Evidence</span>
                    {selectedInterval.decisions[0]?.relevant_evidence_ids.length > 0 && (
                      <span className="px-2 py-0.5 text-xs bg-gray-200 dark:bg-gray-700 rounded-full">
                        {selectedInterval.decisions[0].relevant_evidence_ids.length}
                      </span>
                    )}
                  </div>
                  {activeTab === 'evidence' && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gray-900 dark:bg-gray-100" />
                  )}
                </button>
              </div>
            </div>

            {/* Reasoning Content */}
            {activeTab === 'reasoning' && (
              <div className="space-y-6">
                {selectedInterval.decisions.map((decision, idx) => (
                  <Card key={idx} variant="elevated" className="overflow-hidden">
                    <div className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div
                            className={`px-4 py-2 rounded-lg font-bold text-sm ${
                              decision.decision === 'YES'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                                : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                            }`}
                          >
                            {decision.decision}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-600 dark:text-gray-400">Confidence:</span>
                            <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
                              {(decision.confidence * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                        {decision.execution_trace && (
                          <div className="flex items-center gap-2 px-3 py-1.5 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                            <Code className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                            <span className="text-sm font-medium text-purple-800 dark:text-purple-300">
                              Daytona Execution
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                    <CardContent className="p-8">
                      <div className="prose prose-lg dark:prose-invert max-w-none">
                        <div className="text-gray-800 dark:text-gray-200 leading-relaxed whitespace-pre-wrap font-light">
                          {decision.rationale}
                        </div>
                      </div>
                      {decision.execution_trace && (
                        <div className="mt-8 pt-8 border-t border-gray-200 dark:border-gray-700">
                          <details className="group">
                            <summary className="cursor-pointer flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100">
                              <Code className="w-4 h-4" />
                              <span>View Execution Trace</span>
                            </summary>
                            <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
                              <div className="space-y-4">
                                <div>
                                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">Code:</p>
                                  <pre className="text-xs bg-gray-900 dark:bg-black text-gray-100 p-4 rounded overflow-x-auto">
                                    <code>{decision.execution_trace.code}</code>
                                  </pre>
                                </div>
                                {decision.execution_trace.raw_output && (
                                  <div>
                                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 mb-2">Output:</p>
                                    <pre className="text-xs bg-gray-900 dark:bg-black text-gray-100 p-4 rounded overflow-x-auto">
                                      <code>{decision.execution_trace.raw_output}</code>
                                    </pre>
                                  </div>
                                )}
                                <div className="flex gap-4 text-xs text-gray-500 dark:text-gray-400">
                                  <span>Exit Code: {decision.execution_trace.exit_code}</span>
                                  {decision.execution_trace.execution_time_ms && (
                                    <span>Execution Time: {decision.execution_trace.execution_time_ms.toFixed(2)}ms</span>
                                  )}
                                  <span>Attempt: {decision.execution_trace.attempt_number}</span>
                                </div>
                              </div>
                            </div>
                          </details>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Evidence Content */}
            {activeTab === 'evidence' && (
              <div className="space-y-4">
                {(() => {
                  // Get all unique evidence IDs from all decisions
                  const allEvidenceIds = new Set<string>();
                  selectedInterval.decisions.forEach(decision => {
                    decision.relevant_evidence_ids.forEach(id => allEvidenceIds.add(id));
                  });

                  // Match evidence IDs to news snippets
                  const evidenceArticles = Array.from(allEvidenceIds)
                    .map(evidenceId => {
                      // Try to find by ID first, then by URL
                      const article = selectedInterval.news?.find(
                        snippet => snippet.id === evidenceId || snippet.url === evidenceId
                      );
                      return article ? { id: evidenceId, article } : null;
                    })
                    .filter(Boolean) as Array<{ id: string; article: any }>;

                  if (evidenceArticles.length > 0) {
                    return evidenceArticles.map(({ id, article }, idx) => (
                      <Card key={id} variant="elevated" className="hover:shadow-lg transition-shadow overflow-hidden">
                        <CardContent className="p-0">
                          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                            <div className="flex items-start justify-between">
                              <div className="flex items-start gap-4 flex-1">
                                <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0">
                                  <span className="text-base font-bold text-blue-600 dark:text-blue-400">{idx + 1}</span>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2 leading-tight">
                                    {article.title}
                                  </h3>
                                  <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                                    {article.published_date && (
                                      <span className="flex items-center gap-1">
                                        <Clock className="w-3 h-3" />
                                        {format(parseISO(article.published_date), 'MMM dd, yyyy')}
                                      </span>
                                    )}
                                    {article.score > 0 && (
                                      <span className="flex items-center gap-1">
                                        <Target className="w-3 h-3" />
                                        Score: {(article.score * 100).toFixed(0)}%
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </div>
                              {article.url && (
                                <a
                                  href={article.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="ml-4 p-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex-shrink-0"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <ExternalLink className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                </a>
                              )}
                            </div>
                          </div>
                          <div className="p-6">
                            {article.text && (
                              <div className="mb-4">
                                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">Article Excerpt:</p>
                                <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                                  {article.text.length > 500 ? `${article.text.substring(0, 500)}...` : article.text}
                                </p>
                              </div>
                            )}
                            {article.url && (
                              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                                <a
                                  href={article.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm flex items-center gap-2 group"
                                >
                                  <span className="truncate">{article.url}</span>
                                  <ExternalLink className="w-4 h-4 flex-shrink-0" />
                                </a>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ));
                  } else if (selectedInterval.news && selectedInterval.news.length > 0) {
                    // Show all available news articles if no specific evidence was cited
                    return (
                      <>
                        <div className="mb-4 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                          <p className="text-sm text-amber-800 dark:text-amber-300">
                            <AlertCircle className="w-4 h-4 inline mr-2" />
                            No specific evidence was cited, but {selectedInterval.news.length} article(s) were available at this interval.
                          </p>
                        </div>
                        {selectedInterval.news.map((article, idx) => (
                          <Card key={article.id || idx} variant="elevated" className="hover:shadow-lg transition-shadow overflow-hidden">
                            <CardContent className="p-0">
                              <div className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                                <div className="flex items-start justify-between">
                                  <div className="flex items-start gap-4 flex-1">
                                    <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center flex-shrink-0">
                                      <span className="text-base font-bold text-gray-600 dark:text-gray-400">{idx + 1}</span>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2 leading-tight">
                                        {article.title}
                                      </h3>
                                      <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                                        {article.published_date && (
                                          <span className="flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            {format(parseISO(article.published_date), 'MMM dd, yyyy')}
                                          </span>
                                        )}
                                        {article.score > 0 && (
                                          <span className="flex items-center gap-1">
                                            <Target className="w-3 h-3" />
                                            Score: {(article.score * 100).toFixed(0)}%
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                  {article.url && (
                                    <a
                                      href={article.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="ml-4 p-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex-shrink-0"
                                    >
                                      <ExternalLink className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                    </a>
                                  )}
                                </div>
                              </div>
                              <div className="p-6">
                                {article.text && (
                                  <div className="mb-4">
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 font-medium">Article Excerpt:</p>
                                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                                      {article.text.length > 500 ? `${article.text.substring(0, 500)}...` : article.text}
                                    </p>
                                  </div>
                                )}
                                {article.url && (
                                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                                    <a
                                      href={article.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm flex items-center gap-2 group"
                                    >
                                      <span className="truncate">{article.url}</span>
                                      <ExternalLink className="w-4 h-4 flex-shrink-0" />
                                    </a>
                                  </div>
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </>
                    );
                  } else {
                    return (
                      <Card>
                        <CardContent className="p-12 text-center">
                          <BookOpen className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                          <p className="text-gray-500 dark:text-gray-400 text-lg">No evidence cited for this interval</p>
                          <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
                            The model made its decision without referencing specific evidence sources
                          </p>
                        </CardContent>
                      </Card>
                    );
                  }
                })()}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

