import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/common/Card';
import { Button } from '@/components/common/Button';

export function Portfolio() {
  return (
    <Layout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Portfolio</h1>
            <p className="mt-2 text-gray-600">Manage your investment portfolio</p>
          </div>
          <Button>Add Holding</Button>
        </div>

        <Card title="Portfolio Holdings">
          <div className="text-center py-8">
            <p className="text-gray-600">No holdings yet. Add your first holding to get started.</p>
          </div>
        </Card>

        <Card title="Recent Transactions">
          <div className="text-center py-8">
            <p className="text-gray-600">No transactions yet.</p>
          </div>
        </Card>
      </div>
    </Layout>
  );
}

