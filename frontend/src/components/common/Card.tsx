import { ReactNode, HTMLAttributes } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  title?: string;
  headerActions?: ReactNode;
}

export function Card({ children, title, headerActions, className = '', ...props }: CardProps) {
  return (
    <div className={`card ${className}`} {...props}>
      {(title || headerActions) && (
        <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200">
          {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
          {headerActions && <div className="flex items-center gap-2">{headerActions}</div>}
        </div>
      )}
      <div>{children}</div>
    </div>
  );
}

