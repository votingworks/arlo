import React from 'react'
import { render } from '@testing-library/react'
import AuditForms from './RiskLimitingAuditForm'
import apiMock from '../utilities'

jest.mock('../utilities')

it('renders correctly', () => {
  const { container } = render(<AuditForms />)
  expect(container).toMatchSnapshot()
})

it('fetches from api as expected', () => {
  render(<AuditForms />)
  expect(apiMock).toBeCalled()
  expect((apiMock as jest.Mock).mock.calls[0][0]).toBe('/audit/status')
})
