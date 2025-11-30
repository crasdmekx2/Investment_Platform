import { http, HttpResponse } from 'msw';
import { mockApiResponses, mockApiErrors } from './api';

// MSW request handlers for API mocking
// Use path-based matching to work with API client's baseURL
export const handlers = [
  // Market data endpoints
  http.get('*/api/market-data', () => {
    return HttpResponse.json(mockApiResponses.listAssets().data);
  }),

  http.get('*/api/market-data/:symbol', ({ params }) => {
    const { symbol } = params;
    if (symbol === 'INVALID') {
      return HttpResponse.json(mockApiErrors.notFound, { status: 404 });
    }
    return HttpResponse.json(mockApiResponses.getMarketData(symbol as string).data);
  }),

  http.get('*/api/market-data/:symbol/history', ({ params }) => {
    const { symbol } = params;
    return HttpResponse.json(mockApiResponses.getPriceHistory(symbol as string).data);
  }),

  // Portfolio endpoints
  http.get('*/api/portfolios', () => {
    return HttpResponse.json(mockApiResponses.listPortfolios().data);
  }),

  http.get('*/api/portfolios/:id', ({ params }) => {
    const { id } = params;
    return HttpResponse.json(mockApiResponses.getPortfolio(id as string).data);
  }),

  http.post('*/api/portfolios', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json(mockApiResponses.createPortfolio(body as Partial<any>).data, {
      status: 201,
    });
  }),

  http.put('*/api/portfolios/:id', async ({ params, request }) => {
    const { id } = params;
    const body = await request.json();
    return HttpResponse.json(mockApiResponses.updatePortfolio(id as string, body as Partial<any>).data);
  }),

  http.delete('*/api/portfolios/:id', () => {
    return new HttpResponse(null, { status: 204 });
  }),

  // Transaction endpoints
  http.get('*/api/portfolios/:portfolioId/transactions', ({ params }) => {
    const { portfolioId } = params;
    return HttpResponse.json(mockApiResponses.listTransactions(portfolioId as string).data);
  }),

  http.post('*/api/portfolios/:portfolioId/transactions', async ({ params, request }) => {
    const { portfolioId } = params;
    const body = await request.json();
    return HttpResponse.json(
      mockApiResponses.createTransaction(portfolioId as string, body as Partial<any>).data,
      { status: 201 }
    );
  }),
];

