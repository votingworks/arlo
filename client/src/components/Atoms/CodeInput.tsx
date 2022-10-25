import React, { useEffect } from 'react'
import styled from 'styled-components'
import { Classes } from '@blueprintjs/core'
import { replaceAtIndex, range } from '../../utils/array'
import { Row } from './Layout'
import { assert } from '../utilities'

const DigitInput = styled.input.attrs({
  className: Classes.INPUT,
  type: 'text',
})`
  text-align: center;
`

// We only support a small subset of the HTMLInputElement interface to start,
// but this can be expanded as needed.
type InputProps = Pick<
  React.InputHTMLAttributes<HTMLInputElement>,
  'name' | 'id'
>

interface ICodeInputProps extends InputProps {
  length: number
  value: string
  onChange: (value: string) => void
}

/**
 * CodeInput takes the same props as a controlled text input, but
 * actually renders and coordinates multiple individual digit inputs.
 *
 * Example:
 *  const [value, setValue] = useState('')
 *  <CodeInput length={3} value={value} onChange={setValue} />
 */
const CodeInput: React.FC<ICodeInputProps> = ({
  length,
  value = '',
  onChange,
  ...htmlInputProps
}) => {
  assert(/^\d*$/.test(value), 'CodeInput value must be a string of digits')

  const digitInputRefs = range(0, length - 1).map(() =>
    React.createRef<HTMLInputElement>()
  )

  const focusDigitInput = (index: number) => {
    const digitInputRef = digitInputRefs[index]
    if (digitInputRef?.current) {
      digitInputRef.current.focus()
    }
  }

  const moveFocusRight = (index: number) => {
    if (index < length - 1) {
      focusDigitInput(index + 1)
    }
  }

  const moveFocusLeft = (index: number) => {
    if (index > 0) {
      focusDigitInput(index - 1)
    }
  }

  const onDigitKeyDown = (index: number, key: string) => {
    const firstEmptyDigitIndex = value.length
    if (key.match(/[0-9]/)) {
      if (index === firstEmptyDigitIndex) {
        onChange(replaceAtIndex(value.split(''), index, key).join(''))
        moveFocusRight(index)
      }
    } else if (key === 'Backspace') {
      onChange(replaceAtIndex(value.split(''), index, '').join(''))
      moveFocusLeft(index)
    } else if (key === 'ArrowLeft') {
      moveFocusLeft(index)
    } else if (key === 'ArrowRight') {
      if (index < firstEmptyDigitIndex) {
        moveFocusRight(index)
      }
    }
  }

  // Whenever we have no digits entered, focus the first digit input
  // E.g. on mount, after backspacing, or after form reset
  useEffect(() => {
    if (value === '') {
      focusDigitInput(0)
    }
  })

  return (
    <Row gap="10px" {...htmlInputProps}>
      {digitInputRefs.map((ref, index) => (
        <DigitInput
          // eslint-disable-next-line react/no-array-index-key
          key={`digit-${index}`}
          ref={digitInputRefs[index]}
          value={value[index] || ''}
          onChange={() => {
            // Do nothing (React complains if we don't have an onChange handler)
          }}
          onKeyDown={(event: React.KeyboardEvent<HTMLInputElement>) =>
            onDigitKeyDown(index, event.key)
          }
        />
      ))}
    </Row>
  )
}

export default CodeInput
