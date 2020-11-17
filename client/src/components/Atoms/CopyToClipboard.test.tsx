import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import copy from 'copy-to-clipboard'
import CopyToClipboard from './CopyToClipboard'

jest.mock('copy-to-clipboard', () => jest.fn(() => true))

describe('CopyToClipboard', () => {
  it('renders a button that copies when clicked', async () => {
    render(<CopyToClipboard getText={() => 'text to copy'} />)
    const button = screen.getByRole('button', { name: /Copy to clipboard/ })

    userEvent.click(button)

    expect(copy).toHaveBeenCalledWith('text to copy', { format: 'text/html' })

    // Button text should change to Copied
    screen.getByRole('button', { name: /Copied/ })
  })
})
