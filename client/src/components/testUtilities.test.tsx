import React from 'react'
import { render, screen } from '@testing-library/react'

import { hasTextAcrossElements } from './testUtilities'

test('hasTextAcrossElements', () => {
  render(
    <span>
      Today is <strong>Friday!</strong>
    </span>
  )
  expect(screen.queryByText('Today is Friday!')).not.toBeInTheDocument()
  screen.getByText(hasTextAcrossElements('Today is Friday!'))
})
