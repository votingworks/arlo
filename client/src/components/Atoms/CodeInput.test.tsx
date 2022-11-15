import React, { useState } from 'react'
import { render, screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import CodeInput from './CodeInput'
import { typeCode } from '../testUtilities'

const ControlledCodeInput: React.FC<{ length?: number }> = ({ length = 3 }) => {
  const [value, setValue] = useState('')
  return (
    <div>
      <span>Value: {value === '' ? '{empty}' : value}</span>
      {/* eslint-disable-next-line jsx-a11y/label-has-associated-control */}
      <label id="code-input-label">Code:</label>
      <CodeInput
        id="code-input"
        name="code-input"
        // We have to use aria-labelledby here because CodeInput renders a div,
        // which doesn't work with the regular label "for" attribute
        aria-labelledby="code-input-label"
        length={length}
        value={value}
        onChange={setValue}
      />
      <button type="button" onClick={() => setValue('')}>
        Reset
      </button>
    </div>
  )
}

describe('CodeInput', () => {
  it('handles entering a code', () => {
    render(<ControlledCodeInput />)

    const digitInputs = within(screen.getByLabelText('Code:')).getAllByRole(
      'textbox'
    )
    screen.getByText('Value: {empty}')
    expect(digitInputs).toHaveLength(3)
    expect(digitInputs[0]).toHaveValue('')
    expect(digitInputs[1]).toHaveValue('')
    expect(digitInputs[2]).toHaveValue('')
    expect(digitInputs[0]).toHaveFocus()

    // Type in a code
    userEvent.type(digitInputs[0], '1')
    screen.getByText('Value: 1')
    expect(digitInputs[0]).toHaveValue('1')
    expect(digitInputs[1]).toHaveValue('')
    expect(digitInputs[2]).toHaveValue('')
    expect(digitInputs[1]).toHaveFocus()

    userEvent.type(digitInputs[1], '2')
    screen.getByText('Value: 12')
    expect(digitInputs[0]).toHaveValue('1')
    expect(digitInputs[1]).toHaveValue('2')
    expect(digitInputs[2]).toHaveValue('')
    expect(digitInputs[2]).toHaveFocus()

    userEvent.type(digitInputs[2], '3')
    screen.getByText('Value: 123')
    expect(digitInputs[0]).toHaveValue('1')
    expect(digitInputs[1]).toHaveValue('2')
    expect(digitInputs[2]).toHaveValue('3')
    expect(digitInputs[2]).toHaveFocus()
  })

  it('handles backspace', () => {
    render(<ControlledCodeInput />)
    const codeInput = screen.getByLabelText('Code:')
    typeCode(codeInput, '123')

    const digitInputs = within(codeInput).getAllByRole('textbox')

    // Backspace the code
    userEvent.type(digitInputs[2], '{backspace}')
    screen.getByText('Value: 12')
    expect(digitInputs[0]).toHaveValue('1')
    expect(digitInputs[1]).toHaveValue('2')
    expect(digitInputs[2]).toHaveValue('')
    expect(digitInputs[1]).toHaveFocus()

    userEvent.type(digitInputs[1], '{backspace}')
    screen.getByText('Value: 1')
    expect(digitInputs[0]).toHaveValue('1')
    expect(digitInputs[1]).toHaveValue('')
    expect(digitInputs[2]).toHaveValue('')
    expect(digitInputs[0]).toHaveFocus()

    userEvent.type(digitInputs[0], '{backspace}')
    screen.getByText('Value: {empty}')
    expect(digitInputs[0]).toHaveValue('')
    expect(digitInputs[1]).toHaveValue('')
    expect(digitInputs[2]).toHaveValue('')
    expect(digitInputs[0]).toHaveFocus()

    // Try to backspace again, nothing happens
    userEvent.type(digitInputs[0], '{backspace}')
    expect(digitInputs[0]).toHaveValue('')
    expect(digitInputs[1]).toHaveValue('')
    expect(digitInputs[2]).toHaveValue('')
    expect(digitInputs[0]).toHaveFocus()
  })

  it('handles moving with the arrow keys', () => {
    render(<ControlledCodeInput />)
    const codeInput = screen.getByLabelText('Code:')

    const digitInputs = within(codeInput).getAllByRole('textbox')

    expect(digitInputs[0]).toHaveFocus()

    // Can't move left from the first input
    userEvent.type(digitInputs[0], '{arrowleft}')
    expect(digitInputs[0]).toHaveFocus()

    // Can't move right if no digits entered
    userEvent.type(digitInputs[0], '{arrowright}')
    expect(digitInputs[0]).toHaveFocus()

    // Enter a digit
    userEvent.type(digitInputs[0], '1')
    expect(digitInputs[1]).toHaveFocus()

    // Can move among entered digits and leftmost unentered digit
    userEvent.type(digitInputs[1], '{arrowleft}')
    expect(digitInputs[0]).toHaveFocus()
    userEvent.type(digitInputs[0], '{arrowright}')
    expect(digitInputs[1]).toHaveFocus()
    userEvent.type(digitInputs[1], '{arrowright}')
    expect(digitInputs[1]).toHaveFocus()

    // Enter another digit
    userEvent.type(digitInputs[1], '2')
    expect(digitInputs[2]).toHaveFocus()

    // Can move among all digits
    userEvent.type(digitInputs[2], '{arrowleft}')
    expect(digitInputs[1]).toHaveFocus()
    userEvent.type(digitInputs[1], '{arrowleft}')
    expect(digitInputs[0]).toHaveFocus()
    userEvent.type(digitInputs[0], '{arrowright}')
    expect(digitInputs[1]).toHaveFocus()
    userEvent.type(digitInputs[1], '{arrowright}')
    expect(digitInputs[2]).toHaveFocus()

    // Can't move right from the last input
    userEvent.type(digitInputs[2], '{arrowright}')
    expect(digitInputs[2]).toHaveFocus()
  })

  it('disallows typing digits ahead of sequence', () => {
    render(<ControlledCodeInput />)
    const codeInput = screen.getByLabelText('Code:')
    const digitInputs = within(codeInput).getAllByRole('textbox')

    userEvent.type(digitInputs[1], '1')
    screen.getByText('Value: {empty}')
    expect(digitInputs[0]).toHaveValue('')
    expect(digitInputs[1]).toHaveValue('')
    expect(digitInputs[2]).toHaveValue('')

    userEvent.type(digitInputs[2], '1')
    screen.getByText('Value: {empty}')
    expect(digitInputs[0]).toHaveValue('')
    expect(digitInputs[1]).toHaveValue('')
    expect(digitInputs[2]).toHaveValue('')
  })

  it('disallows typing over digits already entered', () => {
    render(<ControlledCodeInput />)
    const codeInput = screen.getByLabelText('Code:')
    const digitInputs = within(codeInput).getAllByRole('textbox')

    userEvent.type(digitInputs[0], '1')
    userEvent.type(digitInputs[0], '2')
    screen.getByText('Value: 1')
    expect(digitInputs[0]).toHaveValue('1')

    userEvent.type(digitInputs[1], '2')
    userEvent.type(digitInputs[2], '3')
    userEvent.type(digitInputs[2], '4')
    screen.getByText('Value: 123')
    expect(digitInputs[2]).toHaveValue('3')
  })

  it('disallows typing non-digits', () => {
    render(<ControlledCodeInput />)
    const codeInput = screen.getByLabelText('Code:')
    const digitInputs = within(codeInput).getAllByRole('textbox')

    userEvent.type(digitInputs[0], 'a')
    screen.getByText('Value: {empty}')
    expect(digitInputs[0]).toHaveValue('')
  })

  it('refocuses first input on reset', async () => {
    render(<ControlledCodeInput />)
    const codeInput = screen.getByLabelText('Code:')
    const digitInputs = within(codeInput).getAllByRole('textbox')

    typeCode(codeInput, '123')
    screen.getByText('Value: 123')
    expect(digitInputs[2]).toHaveFocus()

    userEvent.click(screen.getByRole('button', { name: 'Reset' }))
    screen.getByText('Value: {empty}')
    await waitFor(() => expect(digitInputs[0]).toHaveFocus())
  })

  it('handles codes of different lengths', () => {
    const { rerender } = render(<ControlledCodeInput key="4" length={4} />)
    let codeInput = screen.getByLabelText('Code:')
    typeCode(codeInput, '4567')
    screen.getByText('Value: 4567')

    rerender(<ControlledCodeInput key="6" length={6} />)
    codeInput = screen.getByLabelText('Code:')
    typeCode(codeInput, '987654')
    screen.getByText('Value: 987654')

    rerender(<ControlledCodeInput key="1" length={1} />)
    codeInput = screen.getByLabelText('Code:')
    typeCode(codeInput, '0')
    screen.getByText('Value: 0')
  })

  it('handles pasting codes', () => {
    render(<ControlledCodeInput />)
    const codeInput = screen.getByLabelText('Code:')
    const digitInputs = within(codeInput).getAllByRole('textbox')

    const paste = (element: HTMLElement, text: string) => {
      // The types are weird, but this works. Fixed in user-event v14, if we
      // ever upgrade.
      userEvent.paste(element, text, {
        clipboardData: ({ getData: () => text } as unknown) as DataTransfer,
      } as MouseEventInit)
    }

    // Supports pasting a complete code
    paste(digitInputs[0], '123')
    screen.getByText('Value: 123')
    expect(digitInputs[2]).toHaveFocus()

    // Supports pasting a partial code
    paste(digitInputs[0], '45')
    screen.getByText('Value: 45')
    expect(digitInputs[1]).toHaveFocus()

    // Rejects pasting a code that's too long
    paste(digitInputs[0], '6789')
    screen.getByText('Value: 45')
    expect(digitInputs[0]).toHaveFocus()

    // Rejects pasting a code that contains non-digits
    paste(digitInputs[0], 'abc')
    screen.getByText('Value: 45')
    expect(digitInputs[0]).toHaveFocus()
  })
})
