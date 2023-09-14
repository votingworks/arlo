import React from 'react'

interface BreadcrumbsProps {
  children: React.ReactNode
}

const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ children }) => (
  <div className="bp3-text-large">
    {React.Children.toArray(children).flatMap((child, index) =>
      index === 0
        ? [child]
        : [
            <span key={`separator-${index}`} style={{ fontSize: '1em' }}>
              {' '}
              &raquo;{' '}
            </span>,
            child,
          ]
    )}
  </div>
)

export default Breadcrumbs
