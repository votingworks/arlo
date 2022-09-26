import React from 'react'
import { render, screen } from '@testing-library/react'

import Count from './Count'

test.each([
  {
    props: { n: 1, plural: 'COOKIES!!! 🥳', singular: 'cookie!' },
    expectedText: '1 cookie!',
  },
  {
    props: { n: 2, plural: 'COOKIES!!! 🥳', singular: 'cookie!' },
    expectedText: '2 COOKIES!!! 🥳',
  },
  {
    props: { n: 2000000, plural: 'COOKIES!!! 🥳', singular: 'cookie!' },
    expectedText: '2,000,000 COOKIES!!! 🥳',
  },
  {
    props: { n: 0, plural: 'cookies', singular: 'cookie' },
    expectedText: '0 cookies',
  },
])('Count renders', ({ props, expectedText }) => {
  render(<Count {...props} />)
  screen.getByText(expectedText)
})
