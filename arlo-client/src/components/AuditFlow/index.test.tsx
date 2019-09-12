import React from 'react'
import { render } from '@testing-library/react'
import { Router } from 'react-router-dom'
import { routerTestProps } from '../testUtilities'
import AuditFlow from './index'

const routeProps = routerTestProps('/board/:token', {
  electionId: '1',
  token: '123',
})

it('renders correctly', () => {
  const { container } = render(
    <Router {...routeProps}>
      <AuditFlow {...routeProps} />
    </Router>
  )
  expect(container).toMatchSnapshot()
})
