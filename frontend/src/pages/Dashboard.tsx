import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/common/Card';

export function Dashboard() {
  return (
    <Layout>
      <main id="main-content" className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-gray-600">Overview of your investment portfolio and market data</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" aria-label="Portfolio summary statistics">
          <Card>
            <div className="space-y-2">
              <p className="text-sm text-gray-600">Total Portfolio Value</p>
              <p className="text-2xl font-bold text-gray-900" aria-live="polite" aria-atomic="true">
                $0.00
              </p>
            </div>
          </Card>
          <Card>
            <div className="space-y-2">
              <p className="text-sm text-gray-600">Total Gain/Loss</p>
              <p className="text-2xl font-bold text-gray-900" aria-live="polite" aria-atomic="true">
                $0.00
              </p>
            </div>
          </Card>
          <Card>
            <div className="space-y-2">
              <p className="text-sm text-gray-600">Total Gain/Loss %</p>
              <p className="text-2xl font-bold text-gray-900" aria-live="polite" aria-atomic="true">
                0.00%
              </p>
            </div>
          </Card>
          <Card>
            <div className="space-y-2">
              <p className="text-sm text-gray-600">Number of Holdings</p>
              <p className="text-2xl font-bold text-gray-900" aria-live="polite" aria-atomic="true">
                0
              </p>
            </div>
          </Card>
        </div>

        <Card title="Market Overview">
          <p className="text-gray-600">Market data will be displayed here</p>
        </Card>
      </main>
    </Layout>
  );
}

