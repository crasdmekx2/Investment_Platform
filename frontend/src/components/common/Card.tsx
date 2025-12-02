import { ReactNode, HTMLAttributes, useId } from 'react';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  title?: string;
  headerActions?: ReactNode;
}

export function Card({ children, title, headerActions, className = '', ...props }: CardProps) {
  const titleId = useId();
  
  return (
    <article 
      className={`card ${className}`} 
      aria-labelledby={title ? titleId : undefined}
      {...props}
    >
      {(title || headerActions) && (
        <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200">
          {title && (
            <h2 id={titleId} className="text-lg font-semibold text-gray-900">
              {title}
            </h2>
          )}
          {headerActions && <div className="flex items-center gap-2">{headerActions}</div>}
        </div>
      )}
      <div>{children}</div>
    </article>
  );
}

