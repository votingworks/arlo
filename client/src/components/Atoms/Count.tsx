import React from 'react'

interface IProps {
  className?: string
  n: number
  plural: string
  singular: string
}

const Count: React.FC<IProps> = ({
  className,
  n,
  plural,
  singular,
}: IProps) => {
  return (
    <span className={className}>
      {n.toLocaleString()} {n === 1 ? singular : plural}
    </span>
  )
}

export default Count
