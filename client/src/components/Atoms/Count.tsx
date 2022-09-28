import React from 'react'

interface IProps {
  className?: string
  count: number
  plural: string
  singular: string
}

const Count: React.FC<IProps> = ({
  className,
  count,
  plural,
  singular,
}: IProps) => {
  return (
    <span className={className}>
      {count.toLocaleString()} {count === 1 ? singular : plural}
    </span>
  )
}

export default Count
