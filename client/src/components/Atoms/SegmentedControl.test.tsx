import { expect, test, vi } from 'vitest'
import React from 'react'
import userEvent from '@testing-library/user-event'
import { render, screen, within } from '@testing-library/react'

import SegmentedControl from './SegmentedControl'

test('SegmentedControl renders', async () => {
  const onChange = vi.fn()
  render(
    <SegmentedControl
      aria-labelledby="label"
      onChange={onChange}
      options={[
        { label: 'Vanilla', value: 'vanilla' },
        { label: 'Chocolate', value: 'chocolate' },
        { label: 'Strawberry', value: 'strawberry' },
      ]}
      value="chocolate"
    />
  )

  const segmentedControl = screen.getByRole('radiogroup')
  expect(segmentedControl).toHaveAttribute('aria-labelledby', 'label')

  const options = within(segmentedControl).getAllByRole('radio')
  expect(options).toHaveLength(3)
  expect(options[0]).toHaveTextContent('Vanilla')
  expect(options[0]).not.toBeChecked()
  expect(options[1]).toHaveTextContent('Chocolate')
  expect(options[1]).toBeChecked()
  expect(options[2]).toHaveTextContent('Strawberry')
  expect(options[2]).not.toBeChecked()

  userEvent.click(options[0])
  expect(onChange).toHaveBeenCalledWith('vanilla')
})
