import React from 'react'
import { fireEvent, wait } from '@testing-library/react'
import { BrowserRouter as Router, useParams } from 'react-router-dom'
import relativeStages from '../_mocks'
import Settings from './index'
import { asyncActRender, regexpEscape } from '../../../testUtilities'
import useAuditSettings from '../useAuditSettings'

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
jest.mock('../useAuditSettings')
auditSettingsMock.mockReturnValue([
  {
    state: 'AL',
    electionName: null,
    online: null,
    randomSeed: null,
    riskLimit: null,
  },
  async () => true,
])

const { nextStage, prevStage } = relativeStages('Audit Settings')

const fillAndSubmit = async () => {
  const { getByText, getByLabelText, getByTestId } = await asyncActRender(
    <Router>
      <Settings locked={false} nextStage={nextStage} prevStage={prevStage} />
    </Router>
  )

  fireEvent.change(getByLabelText('Election Name'), {
    target: { value: 'Election Name' },
  })

  const auditToggleOffline = getByLabelText(
    new RegExp(regexpEscape('Offline')),
    {
      selector: 'select',
    }
  )
  expect(auditToggleOffline).toBeInstanceOf(HTMLInputElement)
  if (auditToggleOffline instanceof HTMLInputElement) {
    fireEvent.click(auditToggleOffline, { bubbles: true })
  }

  fireEvent.change(
    getByLabelText(
      'Enter the random characters to seed the pseudo-random number generator.'
    ),
    {
      target: { value: '12345' },
    }
  )

  fireEvent.change(getByTestId('risk-limit'), {
    target: { value: '5' },
  })

  fireEvent.click(getByText('Save & Next'), { bubbles: true })
}

describe('Setup > Settings', () => {
  it('handles failure to update settings', async () => {
    auditSettingsMock.mockReturnValue([
      {
        state: 'AL',
        electionName: null,
        online: null,
        randomSeed: null,
        riskLimit: null,
      },
      async () => false,
    ])

    await fillAndSubmit()

    await wait(() => {
      expect(nextStage.activate).toHaveBeenCalledTimes(0)
    })
  })
})
