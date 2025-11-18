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
import { getExperiment, type ExperimentResult, type IntervalResult } from '@/lib/api';
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

  useEffect(() => {
    if (experimentId) {
      loadExperiment();
    }
  }, [experimentId]);

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

  if (error || !experiment) {
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

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chart */}
          <div className="lg:col-span-2">
            <Card variant="elevated">
              <CardHeader>
                <CardTitle>Timeline Analysis</CardTitle>
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
                <div className="mt-4 flex flex-wrap gap-4 justify-center text-sm">
                  {chartData.map((point, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        const interval = experiment.timeline.find((i) => i.timestamp === point.timestamp);
                        if (interval) setSelectedInterval(interval);
                      }}
                      className={`px-3 py-1 rounded-full transition-all ${
                        selectedInterval?.timestamp === point.timestamp
                          ? 'ring-2 ring-blue-500 scale-105'
                          : 'hover:scale-105'
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
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {selectedInterval && (
              <>
                {/* Interval Details */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>Interval Details</span>
                      {selectedInterval.aggregated_decision === 'YES' ? (
                        <CheckCircle2 className="w-5 h-5 text-green-500" />
                      ) : (
                        <XCircle className="w-5 h-5 text-red-500" />
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Time</p>
                      <p className="font-semibold">
                        {format(parseISO(selectedInterval.timestamp), 'MMM dd, yyyy HH:mm:ss')}
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Market Odds</p>
                        <p className="text-lg font-semibold text-blue-600 dark:text-blue-400">
                          {(selectedInterval.market_state.price * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Model Confidence</p>
                        <p className="text-lg font-semibold text-purple-600 dark:text-purple-400">
                          {(selectedInterval.aggregated_confidence * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Decision</p>
                      <div
                        className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${
                          selectedInterval.aggregated_decision === 'YES'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                        }`}
                      >
                        {selectedInterval.aggregated_decision === 'YES' ? (
                          <TrendingUp className="w-4 h-4" />
                        ) : (
                          <TrendingDown className="w-4 h-4" />
                        )}
                        <span className="font-semibold">{selectedInterval.aggregated_decision}</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Edge</p>
                      <p
                        className={`text-lg font-semibold ${
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

                {/* Tabs */}
                <Card>
                  <CardHeader>
                    <div className="flex gap-2 border-b border-gray-200 dark:border-gray-800">
                      <button
                        onClick={() => setActiveTab('reasoning')}
                        className={`px-4 py-2 font-medium transition-colors ${
                          activeTab === 'reasoning'
                            ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                        }`}
                      >
                        <FileText className="w-4 h-4 inline mr-2" />
                        Reasoning
                      </button>
                      <button
                        onClick={() => setActiveTab('evidence')}
                        className={`px-4 py-2 font-medium transition-colors ${
                          activeTab === 'evidence'
                            ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                        }`}
                      >
                        <Code className="w-4 h-4 inline mr-2" />
                        Evidence
                      </button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {activeTab === 'reasoning' && (
                      <div className="space-y-4">
                        {selectedInterval.decisions.map((decision, idx) => (
                          <div
                            key={idx}
                            className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                          >
                            <div className="flex items-start justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`px-2 py-1 rounded text-xs font-semibold ${
                                    decision.decision === 'YES'
                                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                                      : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300'
                                  }`}
                                >
                                  {decision.decision}
                                </span>
                                <span className="text-sm text-gray-600 dark:text-gray-400">
                                  {(decision.confidence * 100).toFixed(0)}% confidence
                                </span>
                              </div>
                              {decision.execution_trace && (
                                <span className="text-xs px-2 py-1 bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300 rounded">
                                  Daytona
                                </span>
                              )}
                            </div>
                            <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                              {decision.rationale.length > 300
                                ? `${decision.rationale.substring(0, 300)}...`
                                : decision.rationale}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                    {activeTab === 'evidence' && (
                      <div className="space-y-3">
                        {selectedInterval.decisions[0]?.relevant_evidence_ids.length > 0 ? (
                          selectedInterval.decisions[0].relevant_evidence_ids.map((evidenceId, idx) => (
                            <div
                              key={idx}
                              className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
                            >
                              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">
                                Evidence #{idx + 1}
                              </p>
                              <p className="text-xs text-gray-600 dark:text-gray-400 break-all">{evidenceId}</p>
                            </div>
                          ))
                        ) : (
                          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
                            No evidence cited
                          </p>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

