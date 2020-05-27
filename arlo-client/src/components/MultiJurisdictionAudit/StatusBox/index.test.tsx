import React from 'react'
import {
  BrowserRouter as Router,
  // Router as RegularRouter,
  useParams,
} from 'react-router-dom'
import { render } from '@testing-library/react'
import { AuditAdminStatusBox, JurisdictionAdminStatusBox } from '.'
import { auditSettings } from '../_mocks'

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useRouteMatch: jest.fn(),
  useParams: jest.fn(),
}))
const paramsMock = useParams as jest.Mock
paramsMock.mockReturnValue({
  electionId: '1',
  view: 'setup',
})

describe('StatusBox', () => {
  describe('AuditAdminStatusBox', () => {
    it('renders initial state', () => {
      const { getByText } = render(
        <Router>
          <AuditAdminStatusBox
            rounds={[]}
            jurisdictions={[]}
            contests={[]}
            auditSettings={auditSettings.blank}
          />
        </Router>
      )
      expect(getByText('Audit setup is not complete.')).toBeTruthy()
      expect(getByText('The audit has not started.')).toBeTruthy()
    })
  })

  describe('JurisdictionAdminStatusBox', () => {
    it('renders initial state', () => {
      const { getByText } = render(
        <Router>
          <JurisdictionAdminStatusBox
            rounds={[]}
            auditBoards={[]}
            ballotManifest={{ file: null, processing: null }}
          />
        </Router>
      )
      expect(getByText('The audit has not started.')).toBeTruthy()
      expect(getByText('Ballot manifest not uploaded.')).toBeTruthy()
    })
  })
})
