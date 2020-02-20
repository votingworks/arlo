import React from 'react'
import { render } from '@testing-library/react'
import { BrowserRouter as Router } from 'react-router-dom'
import Header from './Header'

it('renders correctly', () => {
  const { container } = render(
    <Router>
      <Header />
    </Router>
  )
  expect(container).toMatchSnapshot()
})
