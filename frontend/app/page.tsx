'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { runExperiment, fetchMarketMetadata, type ExperimentConfig } from '@/lib/api';
import { TrendingUp, Play, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [isFetchingMarket, setIsFetchingMarket] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [marketInfo, setMarketInfo] = useState<{ title: string; description: string } | null>(null);
  
  const [formData, setFormData] = useState<ExperimentConfig>({
    market_slug: 'gemini-3pt0-released-by',
    start_time: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
    end_time: new Date().toISOString().slice(0, 16),
    interval_minutes: 60,
    num_simulations: 1,
    model_provider: 'openai/gpt-4o',
    mode: 'daytona_agent',
  });

  const handleFetchMarket = async () => {
    if (!formData.market_slug.trim()) {
      setError('Please enter a market slug');
      return;
    }

    setIsFetchingMarket(true);
    setError(null);
    try {
      const metadata = await fetchMarketMetadata(formData.market_slug);
      setMarketInfo({
        title: metadata.title,
        description: metadata.description || 'No description available',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch market information');
      setMarketInfo(null);
    } finally {
      setIsFetchingMarket(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      // Convert local datetime to ISO string
      const config: ExperimentConfig = {
        ...formData,
        start_time: new Date(formData.start_time).toISOString(),
        end_time: new Date(formData.end_time).toISOString(),
      };

      const result = await runExperiment(config);
      router.push(`/experiment/${result.experiment_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run experiment');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-12 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 mb-4">
            <TrendingUp className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              LLM Market Timeline
            </h1>
          </div>
          <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
            Backtest AI-driven trading decisions on prediction markets with time-sliced analysis
          </p>
        </div>

        {/* Main Form Card */}
        <Card variant="elevated" className="mb-8">
          <CardHeader>
            <CardTitle>Run New Experiment</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Market Selection */}
              <div className="space-y-4">
                <div className="flex gap-3">
                  <div className="flex-1">
                    <Input
                      label="Market Slug"
                      placeholder="e.g., gemini-3pt0-released-by"
                      value={formData.market_slug}
                      onChange={(e) => setFormData({ ...formData, market_slug: e.target.value })}
                      required
                    />
                  </div>
                  <div className="flex items-end">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleFetchMarket}
                      isLoading={isFetchingMarket}
                    >
                      Fetch Info
                    </Button>
                  </div>
                </div>

                {marketInfo && (
                  <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                    <div className="flex items-start gap-2">
                      <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <h4 className="font-semibold text-green-900 dark:text-green-100 mb-1">
                          {marketInfo.title}
                        </h4>
                        <p className="text-sm text-green-700 dark:text-green-300 line-clamp-2">
                          {marketInfo.description}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Time Configuration */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Input
                  label="Start Time"
                  type="datetime-local"
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  required
                />
                <Input
                  label="End Time"
                  type="datetime-local"
                  value={formData.end_time}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                  required
                />
              </div>

              {/* Simulation Settings */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Input
                  label="Interval (minutes)"
                  type="number"
                  min="1"
                  value={formData.interval_minutes}
                  onChange={(e) =>
                    setFormData({ ...formData, interval_minutes: parseInt(e.target.value) || 60 })
                  }
                  required
                />
                <Input
                  label="Number of Simulations"
                  type="number"
                  min="1"
                  value={formData.num_simulations}
                  onChange={(e) =>
                    setFormData({ ...formData, num_simulations: parseInt(e.target.value) || 1 })
                  }
                  required
                />
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                    Model Provider
                  </label>
                  <select
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.model_provider}
                    onChange={(e) => setFormData({ ...formData, model_provider: e.target.value })}
                    required
                  >
                    <option value="openai/gpt-4o">GPT-4o</option>
                    <option value="openai/gpt-4o-mini">GPT-4o Mini</option>
                    <option value="anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                    <option value="google/gemini-pro-1.5">Gemini Pro 1.5</option>
                  </select>
                </div>
              </div>

              {/* Mode Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  Execution Mode
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="mode"
                      value="daytona_agent"
                      checked={formData.mode === 'daytona_agent'}
                      onChange={(e) =>
                        setFormData({ ...formData, mode: e.target.value as 'daytona_agent' | 'direct_llm' })
                      }
                      className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-gray-700 dark:text-gray-300">Daytona Agent (Code Execution)</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="mode"
                      value="direct_llm"
                      checked={formData.mode === 'direct_llm'}
                      onChange={(e) =>
                        setFormData({ ...formData, mode: e.target.value as 'daytona_agent' | 'direct_llm' })
                      }
                      className="w-4 h-4 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-gray-700 dark:text-gray-300">Direct LLM</span>
                  </label>
                </div>
              </div>

              {/* Error Display */}
              {error && (
                <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
                </div>
              )}

              {/* Submit Button */}
              <div className="flex justify-end pt-4">
                <Button type="submit" variant="primary" size="lg" isLoading={isLoading}>
                  <Play className="w-5 h-5 mr-2" />
                  Run Experiment
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400 mb-1">
                  Time-Sliced
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Analyze decisions at each interval with historical context
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600 dark:text-purple-400 mb-1">
                  AI-Powered
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  LLM agents execute code in secure sandboxes for decisions
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400 mb-1">
                  Backtest
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Compare AI decisions against actual market outcomes
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
