# User Experience Standards

## Introduction & Purpose

This document establishes the User Experience (UX) standards for the Investment Platform front-end development. All front-end implementations must adhere to these standards to ensure consistent, accessible, and user-centered experiences. These standards are based on WCAG 2.2 AA compliance requirements, evidence-based design principles, and best practices for financial applications.

**Purpose:**
- Ensure consistent user experiences across all features
- Maintain WCAG 2.2 AA accessibility compliance
- Guide front-end developers in implementing user-centered designs
- Establish clear patterns for financial data visualization and interactions
- Provide actionable checklists and implementation guidelines

**Who Should Use This Document:**
- Front-end engineers implementing UI components
- Designers creating mockups and prototypes
- QA engineers testing for accessibility and usability
- Product managers reviewing feature implementations

**Reference Documents:**
- [UX Expert Role Definition](../roles/user-experience-expert.md)
- [Front-End Engineer Role Definition](../roles/front-end-engineer.md)
- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)

---

## 1. Accessibility Standards (WCAG 2.2 AA)

### 1.1 Compliance Requirements

All implementations **MUST** meet WCAG 2.2 Level AA standards. This is non-negotiable for financial applications.

**Key Requirements:**
- **Perceivable**: Information must be presentable to users in ways they can perceive
- **Operable**: Interface components must be operable by all users
- **Understandable**: Information and UI operation must be understandable
- **Robust**: Content must be robust enough for assistive technologies

### 1.2 Keyboard Navigation

**Requirements:**
- All interactive elements must be keyboard accessible
- Logical tab order following visual flow
- Visible focus indicators (minimum 2px outline, 3:1 contrast ratio)
- Skip links for main content areas
- No keyboard traps

**Implementation:**
```tsx
// ✅ Good: Keyboard accessible button
<button
  className="focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
  aria-label="Submit trade order"
>
  Submit Order
</button>

// ❌ Bad: Missing focus styles
<button className="btn-primary">Submit Order</button>
```

**Checklist:**
- [ ] All buttons, links, and form controls are keyboard accessible
- [ ] Tab order follows logical visual flow
- [ ] Focus indicators are visible (2px minimum, 3:1 contrast)
- [ ] Skip links implemented for main content
- [ ] No keyboard traps exist
- [ ] Escape key closes modals/dialogs
- [ ] Enter/Space activate buttons appropriately

### 1.3 Screen Reader Support

**Requirements:**
- Semantic HTML elements (`<button>`, `<nav>`, `<main>`, `<article>`, etc.)
- ARIA labels for icon-only buttons and complex widgets
- ARIA live regions for dynamic content updates
- Proper heading hierarchy (h1 → h2 → h3, no skipping levels)
- Alt text for informative images, empty alt for decorative images

**Implementation:**
```tsx
// ✅ Good: Proper ARIA labels and semantic HTML
<nav aria-label="Main navigation">
  <button aria-label="Close menu" aria-expanded="true">
    <span aria-hidden="true">×</span>
  </button>
</nav>

// ✅ Good: Live region for real-time updates
<div aria-live="polite" aria-atomic="true" className="sr-only">
  Portfolio value updated: $125,430.50
</div>

// ❌ Bad: Missing ARIA labels
<button>
  <svg>...</svg>
</button>
```

**Checklist:**
- [ ] All interactive elements have accessible names
- [ ] Icon-only buttons have `aria-label` or `aria-labelledby`
- [ ] Dynamic content updates use `aria-live` regions
- [ ] Form inputs have associated labels (`<label>` or `aria-labelledby`)
- [ ] Error messages are associated with form fields (`aria-describedby`)
- [ ] Images have appropriate alt text
- [ ] Decorative images have empty alt (`alt=""`)
- [ ] Heading hierarchy is logical (no skipped levels)

### 1.4 Color Contrast

**Requirements:**
- **Normal text** (16px+): Minimum 4.5:1 contrast ratio
- **Large text** (18pt+ or 14pt+ bold): Minimum 3:1 contrast ratio
- **UI components** (buttons, form controls): Minimum 3:1 contrast ratio
- **Non-text content** (icons, charts): Minimum 3:1 contrast ratio
- Never rely solely on color to convey information

**Implementation:**
```tsx
// ✅ Good: Sufficient contrast
<p className="text-gray-900">Portfolio Value: $125,430.50</p>
<button className="bg-primary-600 text-white">Submit</button>

// ❌ Bad: Insufficient contrast
<p className="text-gray-400">Portfolio Value: $125,430.50</p>
<button className="bg-primary-200 text-primary-100">Submit</button>
```

**Testing Tools:**
- Browser DevTools (Chrome Lighthouse)
- WAVE browser extension
- axe DevTools
- Color Contrast Analyzer

**Checklist:**
- [ ] All text meets 4.5:1 contrast ratio (normal) or 3:1 (large)
- [ ] UI components meet 3:1 contrast ratio
- [ ] Color is not the only means of conveying information
- [ ] Status indicators use icons, text, or patterns in addition to color
- [ ] Links are distinguishable from regular text (underline or sufficient contrast)

### 1.5 ARIA Attributes

**Common ARIA Patterns:**

```tsx
// Modal/Dialog
<div role="dialog" aria-modal="true" aria-labelledby="modal-title">
  <h2 id="modal-title">Confirm Trade</h2>
</div>

// Form validation
<input
  aria-invalid={hasError}
  aria-describedby={hasError ? "error-message" : undefined}
/>
{hasError && (
  <div id="error-message" role="alert">
    Invalid amount
  </div>
)}

// Loading states
<button aria-busy="true" aria-label="Processing trade">
  <LoadingSpinner />
</button>

// Collapsible sections
<button aria-expanded={isOpen} aria-controls="portfolio-details">
  Portfolio Details
</button>
<div id="portfolio-details" hidden={!isOpen}>
  ...
</div>
```

**Checklist:**
- [ ] Modals use `role="dialog"` and `aria-modal="true"`
- [ ] Form validation uses `aria-invalid` and `aria-describedby`
- [ ] Loading states use `aria-busy="true"`
- [ ] Collapsible content uses `aria-expanded` and `aria-controls`
- [ ] Landmarks used appropriately (`<nav>`, `<main>`, `<aside>`)
- [ ] Complex widgets have appropriate ARIA roles

---

## 2. Design Principles

### 2.1 User-Centered Design

**Principle:** All design decisions must prioritize user needs, goals, and contexts over technical convenience or personal preferences.

**Implementation:**
- Start with user research and user needs
- Test designs with real users when possible
- Base decisions on evidence, not assumptions
- Consider user context (mobile vs desktop, time constraints, etc.)

### 2.2 Cognitive Load Reduction

**Principle:** Minimize the mental effort required to understand and use the interface.

**Strategies:**
- **Progressive Disclosure**: Show essential information first, reveal details on demand
- **Chunking**: Group related information together
- **Clear Visual Hierarchy**: Use typography, spacing, and color to guide attention
- **Consistent Patterns**: Reuse familiar interaction patterns
- **Clear Labels**: Use plain language, avoid jargon

**Implementation:**
```tsx
// ✅ Good: Progressive disclosure
<Card>
  <CardHeader>
    <h3>Portfolio Summary</h3>
    <button onClick={toggleDetails}>View Details</button>
  </CardHeader>
  <CardContent>
    <p>Total Value: $125,430.50</p>
    {showDetails && (
      <div className="mt-4">
        <p>Breakdown by asset type...</p>
      </div>
    )}
  </CardContent>
</Card>

// ❌ Bad: Information overload
<Card>
  <h3>Portfolio Summary</h3>
  <p>Total Value: $125,430.50</p>
  <p>Stocks: $80,000 (63.7%)</p>
  <p>Bonds: $30,000 (23.9%)</p>
  <p>Cash: $15,430.50 (12.3%)</p>
  <p>Gain/Loss: +$5,430.50 (+4.5%)</p>
  <p>Today's Change: +$230.00 (+0.18%)</p>
  <p>30-Day Change: +$2,100.00 (+1.7%)</p>
  {/* ... 20 more lines ... */}
</Card>
```

### 2.3 Visual Hierarchy

**Principle:** Use visual design to guide users' attention and help them understand information structure.

**Techniques:**
- **Typography Scale**: Clear heading hierarchy (h1 > h2 > h3)
- **Spacing**: Use consistent spacing scale (Tailwind: 4px base)
- **Color**: Use color to indicate importance and relationships
- **Size**: Larger elements draw more attention
- **Contrast**: Higher contrast for more important information

**Implementation:**
```tsx
// ✅ Good: Clear visual hierarchy
<div className="space-y-4">
  <h1 className="text-3xl font-bold text-gray-900">Portfolio</h1>
  <p className="text-lg text-gray-600">Manage your investments</p>
  <div className="grid grid-cols-3 gap-4">
    <Card>
      <p className="text-sm text-gray-600">Total Value</p>
      <p className="text-2xl font-bold text-gray-900">$125,430.50</p>
    </Card>
  </div>
</div>
```

### 2.4 Consistency

**Principle:** Use consistent patterns, components, and interactions throughout the application.

**Areas of Consistency:**
- **Component Patterns**: Use design system components (Button, Card, etc.)
- **Interaction Patterns**: Consistent button placement, modal behavior
- **Terminology**: Use consistent language (e.g., "Portfolio" not "Holdings" in one place and "Portfolio" in another)
- **Visual Style**: Consistent colors, spacing, typography
- **Navigation**: Consistent navigation patterns and placement

**Checklist:**
- [ ] Reuse existing components from design system
- [ ] Follow established interaction patterns
- [ ] Use consistent terminology throughout
- [ ] Maintain consistent spacing scale
- [ ] Use consistent color palette
- [ ] Follow consistent typography scale

---

## 3. Component Standards

### 3.1 Buttons

**Requirements:**
- Minimum touch target: 44x44px
- Clear visual affordance (looks clickable)
- Loading states for async actions
- Disabled states clearly indicated
- Keyboard accessible with focus indicators

**Implementation:**
```tsx
// ✅ Good: Accessible button with loading state
<Button
  variant="primary"
  size="md"
  isLoading={isSubmitting}
  disabled={!isValid}
  aria-label="Submit trade order"
>
  Submit Order
</Button>

// Button component should include:
// - Focus ring: focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
// - Minimum size: 44x44px (or padding to achieve this)
// - Loading spinner with aria-busy
// - Disabled state with reduced opacity
```

**Variants:**
- **Primary**: Main actions (Submit, Confirm, Buy, Sell)
- **Secondary**: Secondary actions (Cancel, Back, View Details)
- **Danger**: Destructive actions (Delete, Cancel Order)

**Checklist:**
- [ ] Minimum 44x44px touch target
- [ ] Clear visual affordance
- [ ] Loading state implemented
- [ ] Disabled state clearly indicated
- [ ] Keyboard accessible with focus indicator
- [ ] ARIA labels for icon-only buttons
- [ ] Appropriate variant for action type

### 3.2 Forms

**Requirements:**
- All inputs have associated labels
- Clear error messages
- Inline validation feedback
- Required fields clearly marked
- Keyboard accessible
- Proper input types (email, number, tel, etc.)

**Implementation:**
```tsx
// ✅ Good: Accessible form with validation
<form onSubmit={handleSubmit}>
  <div className="space-y-4">
    <div>
      <label htmlFor="amount" className="block text-sm font-medium text-gray-700">
        Amount <span className="text-danger-600" aria-label="required">*</span>
      </label>
      <input
        id="amount"
        type="number"
        step="0.01"
        min="0"
        aria-invalid={errors.amount ? "true" : "false"}
        aria-describedby={errors.amount ? "amount-error" : undefined}
        className={cn(
          "mt-1 block w-full rounded-md border-gray-300 shadow-sm",
          errors.amount && "border-danger-600 focus:border-danger-600 focus:ring-danger-600"
        )}
      />
      {errors.amount && (
        <p id="amount-error" role="alert" className="mt-1 text-sm text-danger-600">
          {errors.amount}
        </p>
      )}
    </div>
  </div>
</form>
```

**Checklist:**
- [ ] All inputs have associated `<label>` elements
- [ ] Required fields marked with asterisk and `aria-label="required"`
- [ ] Error messages associated with `aria-describedby`
- [ ] `aria-invalid` set on invalid inputs
- [ ] Error messages use `role="alert"` for screen readers
- [ ] Input types appropriate (number, email, tel, etc.)
- [ ] Placeholder text is supplementary, not replacement for labels
- [ ] Form validation provides clear, actionable error messages

### 3.3 Cards

**Requirements:**
- Clear visual boundaries
- Consistent padding and spacing
- Accessible heading structure
- Optional header actions
- Responsive layout

**Implementation:**
```tsx
// ✅ Good: Accessible card component
<Card title="Portfolio Holdings" headerActions={<Button>Add Holding</Button>}>
  <div className="space-y-4">
    {/* Card content */}
  </div>
</Card>

// Card should include:
// - Semantic structure with proper heading levels
// - Consistent padding (p-6 recommended)
// - Clear visual boundaries (border or shadow)
// - Responsive behavior
```

**Checklist:**
- [ ] Clear visual boundaries (border or shadow)
- [ ] Consistent padding (p-6 standard)
- [ ] Proper heading hierarchy
- [ ] Responsive layout
- [ ] Optional header actions positioned consistently

### 3.4 Navigation

**Requirements:**
- Clear current page indicator
- Keyboard accessible
- Mobile-friendly (hamburger menu or bottom navigation)
- Accessible labels
- Skip links for main content

**Implementation:**
```tsx
// ✅ Good: Accessible navigation
<nav aria-label="Main navigation">
  <ul className="flex space-x-4">
    <li>
      <a
        href="/dashboard"
        aria-current={isActive ? "page" : undefined}
        className={cn(
          "px-4 py-2 rounded-md",
          isActive && "bg-primary-600 text-white"
        )}
      >
        Dashboard
      </a>
    </li>
  </ul>
</nav>

// Mobile navigation
<button
  aria-label="Toggle navigation menu"
  aria-expanded={isOpen}
  aria-controls="mobile-menu"
>
  <MenuIcon />
</button>
<nav id="mobile-menu" hidden={!isOpen} aria-label="Mobile navigation">
  {/* Menu items */}
</nav>
```

**Checklist:**
- [ ] Current page clearly indicated (`aria-current="page"`)
- [ ] Keyboard accessible
- [ ] Mobile-friendly navigation pattern
- [ ] Accessible labels for navigation regions
- [ ] Skip links implemented
- [ ] Focus management for mobile menus

### 3.5 Data Tables

**Requirements:**
- Sortable columns with clear indicators
- Responsive design (horizontal scroll on mobile or card layout)
- Accessible table structure (`<thead>`, `<tbody>`, `<th>` with `scope`)
- Loading and empty states
- Pagination or virtual scrolling for large datasets

**Implementation:**
```tsx
// ✅ Good: Accessible data table
<table className="min-w-full divide-y divide-gray-200">
  <thead>
    <tr>
      <th scope="col" className="px-6 py-3 text-left">
        <button
          onClick={handleSort}
          aria-label={`Sort by Symbol ${sortDirection === 'asc' ? 'ascending' : 'descending'}`}
        >
          Symbol {sortIcon}
        </button>
      </th>
      <th scope="col" className="px-6 py-3 text-left">
        Quantity
      </th>
    </tr>
  </thead>
  <tbody>
    {holdings.map((holding) => (
      <tr key={holding.id}>
        <td className="px-6 py-4">{holding.symbol}</td>
        <td className="px-6 py-4">{holding.quantity}</td>
      </tr>
    ))}
  </tbody>
</table>
```

**Checklist:**
- [ ] Proper table structure (`<thead>`, `<tbody>`, `<th>` with `scope`)
- [ ] Sortable columns have clear indicators and ARIA labels
- [ ] Responsive design (mobile-friendly)
- [ ] Loading state implemented
- [ ] Empty state with helpful message
- [ ] Pagination or virtual scrolling for large datasets

---

## 4. Interaction Patterns

### 4.1 Loading States

**Requirements:**
- Show loading indicators for async operations
- Provide context about what's loading
- Use `aria-busy` and `aria-live` for screen readers
- Skeleton screens for better perceived performance

**Implementation:**
```tsx
// ✅ Good: Loading state with context
{isLoading ? (
  <div aria-busy="true" aria-live="polite">
    <LoadingSpinner />
    <p className="sr-only">Loading portfolio data</p>
  </div>
) : (
  <PortfolioContent data={portfolioData} />
)}

// Skeleton screen for better UX
{isLoading ? (
  <div className="animate-pulse space-y-4">
    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
  </div>
) : (
  <Content />
)}
```

**Checklist:**
- [ ] Loading indicators for all async operations
- [ ] Context provided about what's loading
- [ ] `aria-busy="true"` on loading containers
- [ ] Skeleton screens for better perceived performance
- [ ] Loading states don't block entire UI unnecessarily

### 4.2 Error Handling

**Requirements:**
- Clear, actionable error messages
- Error messages associated with form fields
- Global error handling for API failures
- Recovery paths provided
- Error prevention through validation

**Implementation:**
```tsx
// ✅ Good: Accessible error handling
<ErrorMessage
  title="Unable to submit trade"
  message="The trade could not be submitted. Please check your balance and try again."
  onRetry={handleRetry}
  actions={
    <Button variant="secondary" onClick={handleContactSupport}>
      Contact Support
    </Button>
  }
/>

// Form field errors
<input
  aria-invalid={hasError}
  aria-describedby={hasError ? "error-message" : undefined}
/>
{hasError && (
  <p id="error-message" role="alert" className="text-danger-600">
    {errorMessage}
  </p>
)}
```

**Checklist:**
- [ ] Error messages are clear and actionable
- [ ] Form errors associated with fields (`aria-describedby`)
- [ ] Global errors displayed prominently
- [ ] Recovery paths provided (retry, contact support, etc.)
- [ ] Error prevention through client-side validation
- [ ] Financial transaction errors are especially clear

### 4.3 Feedback & Affordances

**Requirements:**
- Visual feedback for all user actions
- Clear affordances (elements look interactive)
- Status indicators for system state
- Confirmation for destructive actions
- Success messages for completed actions

**Implementation:**
```tsx
// ✅ Good: Clear feedback
<button
  onClick={handleSubmit}
  className="transition-colors hover:bg-primary-700 active:bg-primary-800"
  aria-label="Submit order"
>
  Submit Order
</button>

// Success feedback
{showSuccess && (
  <div role="alert" className="bg-success-50 border border-success-200 text-success-800 p-4 rounded-md">
    <p>Trade submitted successfully</p>
  </div>
)}

// Confirmation for destructive actions
<Dialog
  open={showConfirm}
  title="Cancel Order"
  message="Are you sure you want to cancel this order? This action cannot be undone."
  confirmLabel="Cancel Order"
  cancelLabel="Keep Order"
  onConfirm={handleCancel}
  variant="danger"
/>
```

**Checklist:**
- [ ] Visual feedback for all interactions (hover, active states)
- [ ] Clear affordances (buttons look clickable)
- [ ] Status indicators for system state
- [ ] Confirmation dialogs for destructive actions
- [ ] Success messages for completed actions
- [ ] Feedback is immediate and clear

### 4.4 Micro-Interactions

**Requirements:**
- Subtle animations enhance UX without distracting
- Transitions should be smooth (200-300ms)
- Animations respect `prefers-reduced-motion`
- Loading animations provide feedback
- State changes are visually clear

**Implementation:**
```tsx
// ✅ Good: Respects reduced motion preference
const motionVariants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.2 }
};

// CSS with reduced motion support
.transition-smooth {
  transition: all 0.2s ease-in-out;
}

@media (prefers-reduced-motion: reduce) {
  .transition-smooth {
    transition: none;
  }
}
```

**Checklist:**
- [ ] Animations are subtle and purposeful
- [ ] Transitions are smooth (200-300ms)
- [ ] `prefers-reduced-motion` is respected
- [ ] Loading animations provide feedback
- [ ] State changes are visually clear

---

## 5. Financial Platform-Specific Guidelines

### 5.1 Real-Time Data Display

**Requirements:**
- Real-time updates without page refresh
- Clear indication of data freshness
- Smooth updates without jarring changes
- Loading states during data fetch
- Error handling for connection issues

**Implementation:**
```tsx
// ✅ Good: Real-time data with freshness indicator
<div className="space-y-2">
  <div className="flex items-center justify-between">
    <span className="text-sm font-medium">Current Price</span>
    <span className="text-xs text-gray-500 flex items-center gap-1">
      <span className="w-2 h-2 bg-success-500 rounded-full animate-pulse" aria-hidden="true"></span>
      Live
    </span>
  </div>
  <p className="text-2xl font-bold" aria-live="polite" aria-atomic="true">
    ${price.toFixed(2)}
  </p>
</div>

// WebSocket connection status
{connectionStatus === 'disconnected' && (
  <div role="alert" className="bg-warning-50 border border-warning-200 text-warning-800 p-2 rounded">
    Connection lost. Attempting to reconnect...
  </div>
)}
```

**Checklist:**
- [ ] Real-time updates implemented (WebSocket/SSE)
- [ ] Data freshness indicated
- [ ] Updates are smooth (debounced if necessary)
- [ ] Connection status displayed
- [ ] Graceful degradation if connection lost
- [ ] `aria-live` regions for screen reader updates

### 5.2 Trading Interfaces

**Requirements:**
- Clear buy/sell distinction (color coding + labels)
- Confirmation dialogs for all trades
- Clear display of order details before submission
- Real-time balance updates
- Error prevention (insufficient funds, invalid amounts)
- Transaction history easily accessible

**Implementation:**
```tsx
// ✅ Good: Clear trading interface
<div className="space-y-4">
  <div className="flex gap-2">
    <Button
      variant={orderType === 'buy' ? 'primary' : 'secondary'}
      onClick={() => setOrderType('buy')}
      aria-pressed={orderType === 'buy'}
    >
      Buy
    </Button>
    <Button
      variant={orderType === 'sell' ? 'danger' : 'secondary'}
      onClick={() => setOrderType('sell')}
      aria-pressed={orderType === 'sell'}
    >
      Sell
    </Button>
  </div>
  
  <form onSubmit={handleSubmit}>
    {/* Form fields */}
    <Button
      type="submit"
      disabled={!isValid || insufficientFunds}
      aria-describedby={insufficientFunds ? "funds-error" : undefined}
    >
      {orderType === 'buy' ? 'Buy' : 'Sell'} {symbol}
    </Button>
    {insufficientFunds && (
      <p id="funds-error" role="alert" className="text-danger-600">
        Insufficient funds. Available: ${availableBalance.toFixed(2)}
      </p>
    )}
  </form>
</div>

// Confirmation dialog
<Dialog
  open={showConfirm}
  title={`Confirm ${orderType === 'buy' ? 'Buy' : 'Sell'} Order`}
  message={
    <div className="space-y-2">
      <p>Symbol: {symbol}</p>
      <p>Quantity: {quantity}</p>
      <p>Price: ${price.toFixed(2)}</p>
      <p className="font-bold">Total: ${total.toFixed(2)}</p>
    </div>
  }
  confirmLabel={`Confirm ${orderType === 'buy' ? 'Buy' : 'Sell'}`}
  onConfirm={handleConfirm}
/>
```

**Checklist:**
- [ ] Buy/sell clearly distinguished (color + labels)
- [ ] Confirmation dialogs for all trades
- [ ] Order details displayed before submission
- [ ] Real-time balance updates
- [ ] Error prevention (validation before submission)
- [ ] Transaction history easily accessible
- [ ] Clear error messages for trading errors

### 5.3 Portfolio Visualization

**Requirements:**
- Clear visual hierarchy for portfolio data
- Multiple view options (list, chart, summary)
- Progressive disclosure for detailed information
- Clear gain/loss indicators (color + icons + text)
- Responsive design for mobile viewing

**Implementation:**
```tsx
// ✅ Good: Portfolio visualization with clear indicators
<div className="space-y-4">
  <Card>
    <CardHeader>
      <h2>Portfolio Summary</h2>
    </CardHeader>
    <CardContent>
      <div className="space-y-4">
        <div>
          <p className="text-sm text-gray-600">Total Value</p>
          <p className="text-3xl font-bold text-gray-900">${totalValue.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Total Gain/Loss</p>
          <div className="flex items-center gap-2">
            <span className={cn(
              "text-2xl font-bold",
              totalGainLoss >= 0 ? "text-success-600" : "text-danger-600"
            )}>
              {totalGainLoss >= 0 ? '+' : ''}${totalGainLoss.toFixed(2)}
            </span>
            <span className={cn(
              "text-lg",
              totalGainLossPercent >= 0 ? "text-success-600" : "text-danger-600"
            )}>
              ({totalGainLossPercent >= 0 ? '+' : ''}{totalGainLossPercent.toFixed(2)}%)
            </span>
            {totalGainLoss >= 0 ? (
              <ArrowUpIcon className="w-5 h-5 text-success-600" aria-hidden="true" />
            ) : (
              <ArrowDownIcon className="w-5 h-5 text-danger-600" aria-hidden="true" />
            )}
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
</div>
```

**Checklist:**
- [ ] Clear visual hierarchy for portfolio data
- [ ] Multiple view options available
- [ ] Progressive disclosure for details
- [ ] Gain/loss indicators use color, icons, and text
- [ ] Responsive design for mobile
- [ ] Data is accurate and updates in real-time

### 5.4 Trust & Security Indicators

**Requirements:**
- Security badges and indicators visible
- Regulatory compliance information accessible
- Transparent communication about fees and risks
- Clear authentication status
- Secure connection indicators (HTTPS)

**Implementation:**
```tsx
// ✅ Good: Trust indicators
<footer className="border-t border-gray-200 py-4">
  <div className="flex items-center justify-between text-sm text-gray-600">
    <div className="flex items-center gap-4">
      <span className="flex items-center gap-1">
        <LockIcon className="w-4 h-4" aria-hidden="true" />
        <span>Secure Connection</span>
      </span>
      <span>FDIC Insured</span>
    </div>
    <a href="/security" className="hover:text-gray-900">
      Security & Privacy
    </a>
  </div>
</footer>
```

**Checklist:**
- [ ] Security indicators visible
- [ ] Regulatory compliance information accessible
- [ ] Fees and risks clearly communicated
- [ ] Authentication status clear
- [ ] Secure connection indicators (HTTPS badge)

---

## 6. Responsive Design Standards

### 6.1 Mobile-First Approach

**Principle:** Design for mobile devices first, then progressively enhance for larger screens.

**Breakpoints (Tailwind CSS):**
- `sm`: 640px (small tablets)
- `md`: 768px (tablets)
- `lg`: 1024px (laptops)
- `xl`: 1280px (desktops)
- `2xl`: 1536px (large desktops)

**Implementation:**
```tsx
// ✅ Good: Mobile-first responsive design
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  <Card>Portfolio Value</Card>
  <Card>Gain/Loss</Card>
  <Card>Holdings</Card>
  <Card>Cash Balance</Card>
</div>

// Mobile navigation
<div className="lg:hidden">
  <MobileNavigation />
</div>
<div className="hidden lg:block">
  <DesktopNavigation />
</div>
```

### 6.2 Touch Targets

**Requirements:**
- Minimum touch target size: **44x44px** (Apple HIG) or **48x48px** (Material Design)
- Adequate spacing between touch targets (minimum 8px)
- Touch targets should not overlap
- Larger targets for critical actions

**Implementation:**
```tsx
// ✅ Good: Proper touch target sizing
<button className="min-h-[44px] min-w-[44px] px-4 py-2">
  Submit
</button>

// Icon buttons
<button className="min-h-[44px] min-w-[44px] p-2" aria-label="Close">
  <CloseIcon className="w-6 h-6" />
</button>
```

**Checklist:**
- [ ] All interactive elements are at least 44x44px
- [ ] Adequate spacing between touch targets (8px minimum)
- [ ] Touch targets don't overlap
- [ ] Critical actions have larger touch targets
- [ ] Tested on actual mobile devices

### 6.3 Responsive Typography

**Requirements:**
- Readable font sizes on mobile (minimum 16px for body text)
- Scalable typography that works across screen sizes
- Appropriate line height for readability (1.5-1.6 for body text)

**Implementation:**
```tsx
// ✅ Good: Responsive typography
<h1 className="text-2xl md:text-3xl lg:text-4xl font-bold">
  Portfolio
</h1>
<p className="text-base md:text-lg leading-relaxed">
  Manage your investments
</p>
```

**Checklist:**
- [ ] Body text is at least 16px on mobile
- [ ] Typography scales appropriately
- [ ] Line height is readable (1.5-1.6)
- [ ] Headings are appropriately sized
- [ ] Text is readable without zooming

---

## 7. Performance & Core Web Vitals

### 7.1 Core Web Vitals Targets

**Requirements:**
- **LCP (Largest Contentful Paint)**: < 2.5 seconds
- **FID (First Input Delay)**: < 100 milliseconds
- **CLS (Cumulative Layout Shift)**: < 0.1

**Strategies:**
- Optimize images (WebP, lazy loading, proper sizing)
- Code splitting and lazy loading
- Minimize JavaScript bundle size
- Optimize fonts (subset, preload, display: swap)
- Use CDN for static assets

**Checklist:**
- [ ] LCP < 2.5 seconds
- [ ] FID < 100 milliseconds
- [ ] CLS < 0.1
- [ ] Images optimized and lazy loaded
- [ ] Code splitting implemented
- [ ] Fonts optimized
- [ ] Bundle size minimized

### 7.2 Loading States

**Requirements:**
- Show loading indicators for async operations
- Skeleton screens for better perceived performance
- Progressive loading (show content as it becomes available)
- Optimistic updates where appropriate

**Implementation:**
```tsx
// ✅ Good: Skeleton loading
{isLoading ? (
  <div className="animate-pulse space-y-4">
    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
  </div>
) : (
  <Content data={data} />
)}
```

**Checklist:**
- [ ] Loading indicators for async operations
- [ ] Skeleton screens implemented
- [ ] Progressive loading where possible
- [ ] Optimistic updates for better UX

---

## 8. Color & Typography Guidelines

### 8.1 Color Palette

**Current Palette (from `tailwind.config.js`):**
- Primary: Blue scale (primary-50 to primary-900)
- Success: Green scale (success-50 to success-900)
- Danger: Red scale (danger-50 to danger-900)
- Warning: Yellow/Orange scale (warning-50 to warning-900)

**Usage Guidelines:**
- **Primary**: Main actions, links, primary CTAs
- **Success**: Success messages, positive gains, completed actions
- **Danger**: Errors, losses, destructive actions
- **Warning**: Warnings, caution messages
- **Gray**: Text, borders, backgrounds

**Financial Data Colors:**
- **Gains**: Use success colors (green)
- **Losses**: Use danger colors (red)
- **Neutral**: Use gray colors
- **Never rely solely on color** - use icons, text, or patterns

**Implementation:**
```tsx
// ✅ Good: Color + text + icon for gains/losses
<div className={cn(
  "flex items-center gap-2",
  value >= 0 ? "text-success-600" : "text-danger-600"
)}>
  <span>{value >= 0 ? '+' : ''}${value.toFixed(2)}</span>
  {value >= 0 ? (
    <ArrowUpIcon className="w-4 h-4" aria-hidden="true" />
  ) : (
    <ArrowDownIcon className="w-4 h-4" aria-hidden="true" />
  )}
</div>

// ❌ Bad: Color only
<div className={value >= 0 ? "text-success-600" : "text-danger-600"}>
  ${value.toFixed(2)}
</div>
```

**Checklist:**
- [ ] Color palette used consistently
- [ ] Financial data uses color + text + icons
- [ ] Color contrast meets WCAG standards
- [ ] Color is not the only means of conveying information

### 8.2 Typography

**Font Families:**
- **Sans-serif**: Inter, system-ui, sans-serif (body text)
- **Monospace**: JetBrains Mono, monospace (code, numbers)

**Typography Scale:**
- `text-xs`: 12px (captions, labels)
- `text-sm`: 14px (secondary text)
- `text-base`: 16px (body text)
- `text-lg`: 18px (lead text)
- `text-xl`: 20px (subheadings)
- `text-2xl`: 24px (headings)
- `text-3xl`: 30px (large headings)
- `text-4xl`: 36px (display headings)

**Usage:**
- **Headings**: Use semantic HTML (`<h1>`, `<h2>`, etc.) with appropriate font sizes
- **Body Text**: Use `text-base` (16px minimum) with `leading-relaxed` (1.625)
- **Labels**: Use `text-sm` with `font-medium`
- **Numbers**: Consider monospace font for financial data alignment

**Checklist:**
- [ ] Semantic HTML for headings
- [ ] Body text is at least 16px
- [ ] Appropriate line height (1.5-1.6)
- [ ] Consistent typography scale
- [ ] Monospace font for aligned numbers

---

## 9. Error Handling & Recovery

### 9.1 Error Prevention

**Strategies:**
- Client-side validation before submission
- Confirmation dialogs for destructive actions
- Clear constraints (min/max values, required fields)
- Helpful placeholder text and examples
- Real-time validation feedback

**Implementation:**
```tsx
// ✅ Good: Error prevention
<input
  type="number"
  min="0"
  max={maxQuantity}
  step="0.01"
  placeholder="Enter amount (min: $10)"
  aria-describedby="amount-help"
/>
<p id="amount-help" className="text-sm text-gray-500">
  Minimum trade amount: $10.00
</p>
```

**Checklist:**
- [ ] Client-side validation implemented
- [ ] Confirmation dialogs for destructive actions
- [ ] Clear constraints (min/max, required)
- [ ] Helpful placeholder text
- [ ] Real-time validation feedback

### 9.2 Error Recovery

**Requirements:**
- Clear, actionable error messages
- Recovery paths provided (retry, contact support, etc.)
- Error messages associated with form fields
- Global error handling for API failures
- Graceful degradation

**Implementation:**
```tsx
// ✅ Good: Error recovery
<ErrorMessage
  title="Trade submission failed"
  message="Unable to submit trade. Please check your connection and try again."
  onRetry={handleRetry}
  actions={
    <>
      <Button variant="secondary" onClick={handleContactSupport}>
        Contact Support
      </Button>
      <Button variant="primary" onClick={handleRetry}>
        Try Again
      </Button>
    </>
  }
/>
```

**Checklist:**
- [ ] Error messages are clear and actionable
- [ ] Recovery paths provided
- [ ] Form errors associated with fields
- [ ] Global error handling implemented
- [ ] Graceful degradation for failures

---

## 10. Content & Copy Guidelines

### 10.1 Plain Language

**Principle:** Use clear, concise language that users can understand without financial expertise.

**Guidelines:**
- Avoid jargon and technical terms when possible
- Explain financial terms when first used
- Use active voice
- Keep sentences short and clear
- Use consistent terminology

**Examples:**
- ✅ "Your portfolio gained $1,250.00 today (+2.5%)"
- ❌ "Your portfolio experienced a positive delta of $1,250.00, representing a 2.5% ROI"

**Checklist:**
- [ ] Plain language used throughout
- [ ] Financial terms explained when first used
- [ ] Active voice preferred
- [ ] Sentences are clear and concise
- [ ] Consistent terminology

### 10.2 Information Hierarchy

**Principle:** Present information in order of importance, with most important information first.

**Structure:**
1. Primary information (what user needs to know)
2. Secondary information (supporting details)
3. Tertiary information (additional context)

**Implementation:**
```tsx
// ✅ Good: Clear information hierarchy
<Card>
  <div className="space-y-2">
    <p className="text-sm text-gray-600">Total Portfolio Value</p>
    <p className="text-3xl font-bold text-gray-900">$125,430.50</p>
    <p className="text-sm text-gray-500">As of 3:45 PM EST</p>
  </div>
</Card>
```

**Checklist:**
- [ ] Most important information is most prominent
- [ ] Information hierarchy is clear
- [ ] Progressive disclosure for detailed information
- [ ] Scannable layout with clear sections

---

## 11. Testing & Validation Checklist

### 11.1 Accessibility Testing

**Manual Testing:**
- [ ] Keyboard navigation works throughout
- [ ] Screen reader testing (NVDA/JAWS/VoiceOver)
- [ ] Color contrast verified (4.5:1 for text, 3:1 for UI)
- [ ] Focus indicators visible
- [ ] ARIA attributes tested
- [ ] Form labels and error messages tested

**Automated Testing:**
- [ ] Lighthouse accessibility audit (90+ score)
- [ ] axe DevTools scan (0 violations)
- [ ] WAVE browser extension (0 errors)

### 11.2 Cross-Browser Testing

**Browsers to Test:**
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

**Checklist:**
- [ ] Layout works correctly in all browsers
- [ ] Functionality works in all browsers
- [ ] No browser-specific bugs
- [ ] Performance is acceptable in all browsers

### 11.3 Device Testing

**Devices to Test:**
- [ ] Mobile (iOS Safari, Chrome Android)
- [ ] Tablet (iPad, Android tablet)
- [ ] Desktop (various screen sizes)

**Checklist:**
- [ ] Touch targets are adequate (44x44px minimum)
- [ ] Layout is responsive
- [ ] Text is readable without zooming
- [ ] Interactions work on touch devices
- [ ] Performance is acceptable on mobile

### 11.4 Functional Testing

**Checklist:**
- [ ] All user flows work end-to-end
- [ ] Error states handled gracefully
- [ ] Loading states implemented
- [ ] Real-time updates work correctly
- [ ] Form validation works
- [ ] Confirmation dialogs work
- [ ] Navigation works correctly

---

## 12. Implementation Examples

### 12.1 Accessible Form Component

```tsx
interface TradeFormProps {
  onSubmit: (data: TradeData) => void;
  symbol: string;
  availableBalance: number;
}

export function TradeForm({ onSubmit, symbol, availableBalance }: TradeFormProps) {
  const [orderType, setOrderType] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = () => {
    const newErrors: Record<string, string> = {};
    const qty = parseFloat(quantity);
    
    if (!quantity || isNaN(qty) || qty <= 0) {
      newErrors.quantity = 'Please enter a valid quantity';
    } else if (qty < 0.01) {
      newErrors.quantity = 'Minimum quantity is 0.01';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    
    setIsSubmitting(true);
    try {
      await onSubmit({ orderType, quantity: parseFloat(quantity), symbol });
    } catch (error) {
      // Error handling
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <fieldset>
          <legend className="sr-only">Order Type</legend>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setOrderType('buy')}
              aria-pressed={orderType === 'buy'}
              className={cn(
                "px-4 py-2 rounded-md font-medium",
                orderType === 'buy'
                  ? "bg-primary-600 text-white"
                  : "bg-gray-200 text-gray-900"
              )}
            >
              Buy
            </button>
            <button
              type="button"
              onClick={() => setOrderType('sell')}
              aria-pressed={orderType === 'sell'}
              className={cn(
                "px-4 py-2 rounded-md font-medium",
                orderType === 'sell'
                  ? "bg-danger-600 text-white"
                  : "bg-gray-200 text-gray-900"
              )}
            >
              Sell
            </button>
          </div>
        </fieldset>
      </div>

      <div>
        <label htmlFor="quantity" className="block text-sm font-medium text-gray-700">
          Quantity <span className="text-danger-600" aria-label="required">*</span>
        </label>
        <input
          id="quantity"
          type="number"
          step="0.01"
          min="0.01"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          aria-invalid={errors.quantity ? "true" : "false"}
          aria-describedby={errors.quantity ? "quantity-error quantity-help" : "quantity-help"}
          className={cn(
            "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500",
            errors.quantity && "border-danger-600 focus:border-danger-600 focus:ring-danger-600"
          )}
        />
        <p id="quantity-help" className="mt-1 text-sm text-gray-500">
          Minimum: 0.01
        </p>
        {errors.quantity && (
          <p id="quantity-error" role="alert" className="mt-1 text-sm text-danger-600">
            {errors.quantity}
          </p>
        )}
      </div>

      <Button
        type="submit"
        variant="primary"
        isLoading={isSubmitting}
        disabled={!quantity || isSubmitting}
        className="w-full min-h-[44px]"
      >
        {orderType === 'buy' ? 'Buy' : 'Sell'} {symbol}
      </Button>
    </form>
  );
}
```

### 12.2 Accessible Data Display

```tsx
interface PortfolioValueProps {
  value: number;
  gainLoss: number;
  gainLossPercent: number;
  lastUpdated: Date;
}

export function PortfolioValue({ value, gainLoss, gainLossPercent, lastUpdated }: PortfolioValueProps) {
  const isPositive = gainLoss >= 0;
  
  return (
    <Card>
      <div className="space-y-4">
        <div>
          <p className="text-sm text-gray-600">Total Portfolio Value</p>
          <p className="text-3xl font-bold text-gray-900" aria-live="polite" aria-atomic="true">
            ${value.toFixed(2)}
          </p>
        </div>
        
        <div>
          <p className="text-sm text-gray-600">Total Gain/Loss</p>
          <div className="flex items-center gap-2">
            <span className={cn(
              "text-2xl font-bold",
              isPositive ? "text-success-600" : "text-danger-600"
            )}>
              {isPositive ? '+' : ''}${gainLoss.toFixed(2)}
            </span>
            <span className={cn(
              "text-lg",
              isPositive ? "text-success-600" : "text-danger-600"
            )}>
              ({isPositive ? '+' : ''}{gainLossPercent.toFixed(2)}%)
            </span>
            {isPositive ? (
              <ArrowUpIcon className="w-5 h-5 text-success-600" aria-hidden="true" />
            ) : (
              <ArrowDownIcon className="w-5 h-5 text-danger-600" aria-hidden="true" />
            )}
            <span className="sr-only">
              {isPositive ? 'Gain' : 'Loss'} of ${Math.abs(gainLoss).toFixed(2)} ({Math.abs(gainLossPercent).toFixed(2)}%)
            </span>
          </div>
        </div>
        
        <p className="text-xs text-gray-500">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </p>
      </div>
    </Card>
  );
}
```

---

## 13. Quick Reference Checklist

### Before Submitting Code

**Accessibility:**
- [ ] WCAG 2.2 AA compliance verified
- [ ] Keyboard navigation tested
- [ ] Screen reader tested (or automated tools)
- [ ] Color contrast meets standards
- [ ] ARIA attributes used appropriately
- [ ] Focus indicators visible

**Design:**
- [ ] Mobile-first responsive design
- [ ] Touch targets are 44x44px minimum
- [ ] Consistent with design system
- [ ] Clear visual hierarchy
- [ ] Loading and error states implemented

**Financial Platform:**
- [ ] Real-time data updates work
- [ ] Trading interfaces have confirmations
- [ ] Error prevention for transactions
- [ ] Trust indicators visible
- [ ] Financial data uses color + text + icons

**Performance:**
- [ ] Core Web Vitals targets met
- [ ] Images optimized
- [ ] Code splitting implemented
- [ ] Bundle size optimized

**Testing:**
- [ ] Cross-browser tested
- [ ] Mobile device tested
- [ ] Functional testing complete
- [ ] Accessibility testing complete

---

## Resources

### External Resources
- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [MDN Web Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [A11y Project Checklist](https://www.a11yproject.com/checklist/)

### Internal Resources
- [UX Expert Role](../roles/user-experience-expert.md)
- [Front-End Engineer Role](../roles/front-end-engineer.md)
- [Component Library](../frontend/src/components/)

---

**Last Updated:** 2024
**Version:** 1.0
**Maintained By:** UX Team

