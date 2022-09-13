import React from 'react'
import { InputGroup } from '@blueprintjs/core'

interface IProps {
  ariaLabel?: string
  name: string
  onChange: (newValue: number) => void
  value: number
}

const IntegerInput: React.FC<IProps> = ({
  ariaLabel,
  name,
  onChange,
  value,
}) => {
  return (
    <InputGroup
      aria-label={ariaLabel}
      name={name}
      onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = Math.round(Number(e.target.value))
        onChange(newValue)
      }}
      placeholder="0"
      type="number"
      value={value === 0 ? '' : `${value}`}
    />
  )
}

export default IntegerInput
