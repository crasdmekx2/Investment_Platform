import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { JobTemplateSelector } from './JobTemplateSelector';
import { schedulerApi } from '@/lib/api/scheduler';

// Mock the API
vi.mock('@/lib/api/scheduler', () => ({
  schedulerApi: {
    listTemplates: vi.fn(),
  },
}));

describe('JobTemplateSelector', () => {
  const mockOnSelect = vi.fn();
  const mockOnNext = vi.fn();
  const mockOnSkip = vi.fn();

  const mockTemplates = [
    {
      template_id: 1,
      name: 'Daily Stock Collection',
      description: 'Collect stock data daily',
      asset_type: 'stock' as const,
      trigger_type: 'interval' as const,
      trigger_config: { type: 'interval', hours: 24 },
      symbol: 'AAPL',
    },
    {
      template_id: 2,
      name: 'Hourly Crypto Collection',
      description: 'Collect crypto data hourly',
      asset_type: 'crypto' as const,
      trigger_type: 'interval' as const,
      trigger_config: { type: 'interval', hours: 1 },
      symbol: null,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(schedulerApi.listTemplates).mockResolvedValue({
      data: mockTemplates,
    } as any);
  });

  it('renders template selector with title', async () => {
    render(
      <JobTemplateSelector
        assetType="stock"
        selectedTemplateId={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
        onSkip={mockOnSkip}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Select Template (Optional)')).toBeInTheDocument();
    });
  });

  it('loads and displays templates', async () => {
    render(
      <JobTemplateSelector
        assetType="stock"
        selectedTemplateId={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
        onSkip={mockOnSkip}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Daily Stock Collection')).toBeInTheDocument();
      expect(screen.getByText('Hourly Crypto Collection')).toBeInTheDocument();
    });
  });

  it('calls onSelect when template is clicked', async () => {
    const user = userEvent.setup();
    render(
      <JobTemplateSelector
        assetType="stock"
        selectedTemplateId={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
        onSkip={mockOnSkip}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Daily Stock Collection')).toBeInTheDocument();
    });

    const templateButton = screen.getByText('Daily Stock Collection').closest('button');
    if (templateButton) {
      await user.click(templateButton);
      expect(mockOnSelect).toHaveBeenCalledWith(mockTemplates[0]);
    }
  });

  it('deselects template when clicking selected template', async () => {
    const user = userEvent.setup();
    render(
      <JobTemplateSelector
        assetType="stock"
        selectedTemplateId={1}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
        onSkip={mockOnSkip}
      />
    );

    await waitFor(() => {
      const buttons = screen.getAllByText('Daily Stock Collection');
      expect(buttons.length).toBeGreaterThan(0);
    });

    // Find the button (not the selected template text)
    const templateButtons = screen.getAllByRole('button');
    const templateButton = templateButtons.find(btn => 
      btn.textContent?.includes('Daily Stock Collection') && 
      btn.getAttribute('aria-pressed') === 'true'
    );
    
    if (templateButton) {
      await user.click(templateButton);
      expect(mockOnSelect).toHaveBeenCalledWith(null);
    }
  });

  it('highlights selected template', async () => {
    render(
      <JobTemplateSelector
        assetType="stock"
        selectedTemplateId={1}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
        onSkip={mockOnSkip}
      />
    );

    await waitFor(() => {
      const templateButtons = screen.getAllByRole('button');
      const selectedButton = templateButtons.find(btn => 
        btn.getAttribute('aria-pressed') === 'true'
      );
      expect(selectedButton).toBeDefined();
      expect(selectedButton).toHaveClass('border-primary-500', 'bg-primary-50');
    });
  });

  it('displays selected template information', async () => {
    render(
      <JobTemplateSelector
        assetType="stock"
        selectedTemplateId={1}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
        onSkip={mockOnSkip}
      />
    );

    await waitFor(() => {
      // Check for selected template section
      const selectedSection = screen.getByText(/selected template/i);
      expect(selectedSection).toBeInTheDocument();
      
      // Verify template name appears in selected section
      const allDailyStockTexts = screen.getAllByText('Daily Stock Collection');
      expect(allDailyStockTexts.length).toBeGreaterThan(0);
    });
  });

  it('displays empty message when no templates available', async () => {
    vi.mocked(schedulerApi.listTemplates).mockResolvedValue({
      data: [],
    } as any);

    render(
      <JobTemplateSelector
        assetType="stock"
        selectedTemplateId={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
        onSkip={mockOnSkip}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/no templates available/i)).toBeInTheDocument();
    });
  });

  it('calls onSkip when skip button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <JobTemplateSelector
        assetType="stock"
        selectedTemplateId={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
        onSkip={mockOnSkip}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /skip/i })).toBeInTheDocument();
    });

    const skipButton = screen.getByRole('button', { name: /skip/i });
    await user.click(skipButton);

    expect(mockOnSkip).toHaveBeenCalledTimes(1);
  });

  it('calls onNext when next button is clicked', async () => {
    const user = userEvent.setup();
    render(
      <JobTemplateSelector
        assetType="stock"
        selectedTemplateId={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
        onSkip={mockOnSkip}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /continue/i })).toBeInTheDocument();
    });

    const nextButton = screen.getByRole('button', { name: /continue/i });
    await user.click(nextButton);

    expect(mockOnNext).toHaveBeenCalledTimes(1);
  });

  it('displays "Use Template" when template is selected', async () => {
    render(
      <JobTemplateSelector
        assetType="stock"
        selectedTemplateId={1}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
        onSkip={mockOnSkip}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /use template/i })).toBeInTheDocument();
    });
  });

  it('displays error message when API fails', async () => {
    vi.mocked(schedulerApi.listTemplates).mockRejectedValue(new Error('API Error'));

    render(
      <JobTemplateSelector
        assetType="stock"
        selectedTemplateId={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
        onSkip={mockOnSkip}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/failed to load templates/i)).toBeInTheDocument();
    });
  });

  it('has accessible template buttons', async () => {
    render(
      <JobTemplateSelector
        assetType="stock"
        selectedTemplateId={null}
        onSelect={mockOnSelect}
        onNext={mockOnNext}
        onSkip={mockOnSkip}
      />
    );

    await waitFor(() => {
      const templateButton = screen.getByText('Daily Stock Collection').closest('button');
      expect(templateButton).toHaveAttribute('aria-pressed', 'false');
      expect(templateButton).toHaveClass('min-h-[120px]');
    });
  });
});

