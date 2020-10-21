import React from 'react'
import { fireEvent, waitFor, render, screen } from '@testing-library/react'
import { BrowserRouter as Router, useParams } from 'react-router-dom'
import relativeStages from '../_mocks'
import Settings from './index'
import useAuditSettings from '../../useAuditSettings'

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useParams: jest.fn(),
}))
const routeMock = useParams as jest.Mock
routeMock.mockReturnValue({
  electionId: '1',
  view: 'setup',
})

const auditSettingsMock = useAuditSettings as jest.Mock
jest.mock('../../useAuditSettings')
auditSettingsMock.mockReturnValue([
  {
    state: 'AL',
    electionName: null,
    online: null,
    randomSeed: null,
    riskLimit: null,
    auditType: 'BALLOT_POLLING',
  },
  async () => true,
])

const { nextStage, prevStage } = relativeStages('settings')

describe('Setup > BALLOT_POLLING Settings', () => {
  it('handles failure to update settings', async () => {
    auditSettingsMock.mockReturnValue([
      {
        state: 'AL',
        electionName: null,
        online: null,
        randomSeed: null,
        riskLimit: null,
        auditType: 'BALLOT_POLLING',
      },
      async () => false,
    ])

    render(
      <Router>
        <Settings locked={false} nextStage={nextStage} prevStage={prevStage} />
      </Router>
    )

    fireEvent.change(screen.getByLabelText('Election Name'), {
      target: { value: 'Election Name' },
    })

    const auditToggleOffline = screen.getByLabelText('Offline')
    expect(auditToggleOffline).toBeInstanceOf(HTMLInputElement)
    if (auditToggleOffline instanceof HTMLInputElement) {
      fireEvent.click(auditToggleOffline, { bubbles: true })
    }

    fireEvent.change(
      screen.getByLabelText(
        'Enter the random characters to seed the pseudo-random number generator.'
      ),
      {
        target: { value: '12345' },
      }
    )

    fireEvent.change(screen.getByTestId('risk-limit'), {
      target: { value: '5' },
    })

    fireEvent.click(screen.getByText('Save & Next'), { bubbles: true })

    await waitFor(() => {
      expect(nextStage.activate).toHaveBeenCalledTimes(0)
    })
  })
})

describe('Setup > BATCH_COMPARISON Settings', () => {
  it('handles failure to update settings', async () => {
    auditSettingsMock.mockReturnValue([
      {
        state: 'AL',
        electionName: null,
        online: null,
        randomSeed: null,
        riskLimit: null,
        auditType: 'BATCH_COMPARISON',
      },
      async () => false,
    ])

    render(
      <Router>
        <Settings locked={false} nextStage={nextStage} prevStage={prevStage} />
      </Router>
    )

    fireEvent.change(screen.getByLabelText('Election Name'), {
      target: { value: 'Election Name' },
    })

    fireEvent.change(
      screen.getByLabelText(
        'Enter the random characters to seed the pseudo-random number generator.'
      ),
      {
        target: { value: '12345' },
      }
    )

    fireEvent.change(screen.getByTestId('risk-limit'), {
      target: { value: '5' },
    })

    fireEvent.click(screen.getByText('Save & Next'), { bubbles: true })

    await waitFor(() => {
      expect(nextStage.activate).toHaveBeenCalledTimes(0)
    })
  })
})
