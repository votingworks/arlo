import React from 'react'
import styled from 'styled-components'
import { Button, ButtonGroup } from '@blueprintjs/core'

const Option = styled(Button)`
  &.bp3-button {
    flex-basis: 0;
    flex-grow: 1;
  }
`

interface IOption<T> {
  label: string
  value: T
}

interface IProps<T extends string> {
  ['aria-labelledby']?: string
  disabled?: boolean
  fill?: boolean
  large?: boolean
  onChange: (value: T) => void
  options: IOption<T>[]
  value: T
}

const SegmentedControl = <T extends string>(
  props: IProps<T>
): React.ReactElement => {
  const { disabled, fill, large, onChange, options, value } = props

  // TODO: Use a proper radio group under the hood or add the required keyboard support for a radio
  // group (https://www.w3.org/WAI/ARIA/apg/example-index/radio/radio-rating.html#kbd_label) to
  // make this fully accessible
  return (
    <ButtonGroup
      aria-labelledby={props['aria-labelledby']}
      fill={fill}
      large={large}
      role="radiogroup"
    >
      {options.map(option => (
        <Option
          aria-checked={option.value === value}
          disabled={disabled}
          intent={option.value === value ? 'primary' : undefined}
          onClick={() => onChange(option.value)}
          role="radio"
          key={option.value}
        >
          {option.label}
        </Option>
      ))}
    </ButtonGroup>
  )
}

export default SegmentedControl
