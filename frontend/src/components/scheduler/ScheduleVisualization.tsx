import { useState, useMemo } from 'react';
import { Card } from '@/components/common/Card';
import type { ScheduledJob } from '@/types/scheduler';
import { calculateNextRuns, getFrequencyDescription, groupJobsByDate } from '@/lib/utils/scheduleUtils';

interface ScheduleVisualizationProps {
  jobs: ScheduledJob[];
  viewMode?: 'calendar' | 'timeline';
  daysAhead?: number;
}

export function ScheduleVisualization({
  jobs,
  viewMode = 'timeline',
  daysAhead = 7,
}: ScheduleVisualizationProps) {
  const [selectedView, setSelectedView] = useState<'calendar' | 'timeline'>(viewMode);

  // Filter active jobs
  const activeJobs = useMemo(
    () => jobs.filter(job => job.status === 'active' && job.next_run_at),
    [jobs]
  );

  // Group jobs by date for calendar view
  const jobsByDate = useMemo(() => groupJobsByDate(activeJobs), [activeJobs]);

  // Get timeline events (next N runs for each job)
  const timelineEvents = useMemo(() => {
    const events: Array<{
      jobId: string;
      symbol: string;
      assetType: string;
      date: Date;
      frequency: string;
    }> = [];

    activeJobs.forEach(job => {
      const nextRuns = calculateNextRuns(job, 5);
      const frequency = getFrequencyDescription(job.trigger_config);
      
      nextRuns.forEach(date => {
        if (date <= new Date(Date.now() + daysAhead * 24 * 60 * 60 * 1000)) {
          events.push({
            jobId: job.job_id,
            symbol: job.symbol,
            assetType: job.asset_type,
            date,
            frequency,
          });
        }
      });
    });

    return events.sort((a, b) => a.date.getTime() - b.date.getTime());
  }, [activeJobs, daysAhead]);

  // Get dates for calendar view
  const calendarDates = useMemo(() => {
    const dates: string[] = [];
    const today = new Date();
    
    for (let i = 0; i < daysAhead; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      dates.push(date.toISOString().split('T')[0]);
    }
    
    return dates;
  }, [daysAhead]);

  return (
    <Card title="Schedule Visualization">
      <div className="space-y-4">
        {/* View Mode Toggle */}
        <div className="flex gap-4 border-b pb-4">
          <button
            onClick={() => setSelectedView('timeline')}
            className={`
              px-4 py-2 rounded-md font-medium transition-colors min-h-[44px]
              ${selectedView === 'timeline'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
            aria-pressed={selectedView === 'timeline'}
          >
            Timeline
          </button>
          <button
            onClick={() => setSelectedView('calendar')}
            className={`
              px-4 py-2 rounded-md font-medium transition-colors min-h-[44px]
              ${selectedView === 'calendar'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }
            `}
            aria-pressed={selectedView === 'calendar'}
          >
            Calendar
          </button>
        </div>

        {/* Timeline View */}
        {selectedView === 'timeline' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Next {daysAhead} Days Schedule
            </h3>
            {timelineEvents.length === 0 ? (
              <p className="text-gray-500">No scheduled jobs in the next {daysAhead} days</p>
            ) : (
              <div className="space-y-2">
                {timelineEvents.map((event, idx) => (
                  <div
                    key={`${event.jobId}-${event.date.getTime()}-${idx}`}
                    className="flex items-center p-3 bg-gray-50 rounded-md border border-gray-200"
                  >
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{event.symbol}</div>
                      <div className="text-sm text-gray-600">
                        {event.date.toLocaleString()} • {event.frequency}
                      </div>
                    </div>
                    <div className="text-xs text-gray-500 bg-white px-2 py-1 rounded">
                      {event.assetType}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Calendar View */}
        {selectedView === 'calendar' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Calendar View</h3>
            <div className="grid grid-cols-1 md:grid-cols-7 gap-2">
              {calendarDates.map((dateStr) => {
                const date = new Date(dateStr);
                const dayJobs = jobsByDate.get(dateStr) || [];
                const isToday = dateStr === new Date().toISOString().split('T')[0];
                
                return (
                  <div
                    key={dateStr}
                    className={`
                      border rounded-md p-2 min-h-[100px]
                      ${isToday ? 'border-primary-500 bg-primary-50' : 'border-gray-200'}
                    `}
                  >
                    <div className="text-sm font-medium text-gray-700 mb-2">
                      {date.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric' })}
                    </div>
                    {dayJobs.length > 0 && (
                      <div className="space-y-1">
                        {dayJobs.slice(0, 3).map((job) => (
                          <div
                            key={job.job_id}
                            className="text-xs bg-primary-100 text-primary-800 px-1 py-0.5 rounded truncate"
                            title={`${job.symbol} - ${getFrequencyDescription(job.trigger_config)}`}
                          >
                            {job.symbol}
                          </div>
                        ))}
                        {dayJobs.length > 3 && (
                          <div className="text-xs text-gray-500">
                            +{dayJobs.length - 3} more
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

