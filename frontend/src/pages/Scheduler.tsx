import { useState } from 'react';
import { Layout } from '@/components/layout/Layout';
import { JobsList } from '@/components/scheduler/JobsList';
import { JobsDashboard } from '@/components/scheduler/JobsDashboard';
import { JobCreator } from '@/components/scheduler/JobCreator';
import { CollectionLogsView } from '@/components/scheduler/CollectionLogsView';

type Tab = 'dashboard' | 'jobs' | 'create' | 'logs';

export function Scheduler() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');

  return (
    <Layout showSidebar={false}>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Data Collection Scheduler</h1>
          <p className="mt-2 text-gray-600">
            Configure and manage automated data collection jobs
          </p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm min-h-[44px] min-w-[44px]
                ${activeTab === 'dashboard'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
              aria-current={activeTab === 'dashboard' ? 'page' : undefined}
            >
              Dashboard
            </button>
            <button
              onClick={() => setActiveTab('jobs')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm min-h-[44px] min-w-[44px]
                ${activeTab === 'jobs'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
              aria-current={activeTab === 'jobs' ? 'page' : undefined}
            >
              Jobs
            </button>
            <button
              onClick={() => setActiveTab('create')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm min-h-[44px] min-w-[44px]
                ${activeTab === 'create'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
              aria-current={activeTab === 'create' ? 'page' : undefined}
            >
              Create Job
            </button>
            <button
              onClick={() => setActiveTab('logs')}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm min-h-[44px] min-w-[44px]
                ${activeTab === 'logs'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
              aria-current={activeTab === 'logs' ? 'page' : undefined}
            >
              Collection Logs
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === 'dashboard' && <JobsDashboard />}
          {activeTab === 'jobs' && <JobsList />}
          {activeTab === 'create' && <JobCreator onSuccess={() => setActiveTab('jobs')} />}
          {activeTab === 'logs' && <CollectionLogsView />}
        </div>
      </div>
    </Layout>
  );
}

