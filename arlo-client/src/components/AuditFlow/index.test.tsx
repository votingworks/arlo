import React from 'react'
import { render } from '@testing-library/react'
import { routerTestProps } from '../testUtilities'
import AuditFlow from './index'

const routeProps = routerTestProps('/board/:token', {
  electionId: '1',
  token: '123',
})

it('renders correctly', () => {
  const { container } = render(<AuditFlow {...routeProps} />)
  expect(container).toMatchSnapshot()
})
