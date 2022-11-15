import React from 'react'
import { waitFor, screen } from '@testing-library/react'
import { Route } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import { QueryClientProvider } from 'react-query'
import Settings from './Settings'
import {
  renderWithRouter,
  withMockFetch,
  createQueryClient,
} from '../../../testUtilities'
import { aaApiCalls, auditSettings } from '../../../_mocks'

const renderSettings = () => {
  const goToNextStage = jest.fn()
  const goToPrevStage = jest.fn()
  return {
    goToNextStage,
    goToPrevStage,
    ...renderWithRouter(
      <QueryClientProvider client={createQueryClient()}>
        <Route path="/election/:electionId/setup">
          <Settings
            goToNextStage={goToNextStage}
            goToPrevStage={goToPrevStage}
          />
        </Route>
      </QueryClientProvider>,
      { route: '/election/1/setup' }
    ),
  }
}

describe('Setup > Settings', () => {
  it('updates settings', async () => {
    const updatedSettings = {
      ...auditSettings.blank,
      state: 'CA',
      electionName: 'Election Name',
      online: true,
      riskLimit: 5,
      randomSeed: '12345',
    }
    const expectedCalls = [
      aaApiCalls.getSettings(auditSettings.blank),
      aaApiCalls.putSettings(updatedSettings),
      aaApiCalls.getSettings(updatedSettings),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { goToNextStage } = renderSettings()

      await screen.findByRole('heading', { name: 'Audit Settings' })

      screen.getByRole('heading', { name: 'State' })
      userEvent.selectOptions(
        screen.getByLabelText(/Choose your state from the options below./),
        'CA'
      )

      screen.getByRole('heading', { name: 'Election Name' })
      userEvent.type(
        screen.getByLabelText(
          'Enter the name of the election you are auditing.'
        ),
        'Election Name'
      )

      screen.getByRole('heading', { name: 'Audit Board Data Entry' })
      expect(screen.getByLabelText('Offline')).toBeChecked()
      userEvent.click(screen.getByLabelText('Online'))

      screen.getByRole('heading', { name: 'Desired Risk Limit' })
      screen.getByRole('option', { name: '1%' })
      screen.getByRole('option', { name: '20%' })
      // Defaults to 10% selected
      screen.getByRole('option', { name: '10%', selected: true })
      userEvent.selectOptions(
        screen.getByLabelText(/Set the risk limit for the audit./),
        '5'
      )

      screen.getByRole('heading', { name: 'Random Seed' })
      userEvent.type(
        screen.getByLabelText(
          'Enter the random characters to seed the pseudo-random number generator.'
        ),
        '12345'
      )

      userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))

      await waitFor(() => {
        expect(goToNextStage).toHaveBeenCalled()
      })
    })
  })

  it('hides online/offline toggle for batch comparison audits', async () => {
    const expectedCalls = [
      aaApiCalls.getSettings(auditSettings.batchComparisonAll),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderSettings()

      await screen.findByRole('heading', { name: 'Audit Settings' })

      expect(
        screen.queryByRole('heading', { name: 'Audit Board Data Entry' })
      ).not.toBeInTheDocument()
    })
  })

  it('hides online/offline toggle for ballot comparison audits', async () => {
    const expectedCalls = [
      aaApiCalls.getSettings(auditSettings.ballotComparisonAll),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderSettings()

      await screen.findByRole('heading', { name: 'Audit Settings' })

      expect(
        screen.queryByRole('heading', { name: 'Audit Board Data Entry' })
      ).not.toBeInTheDocument()
    })
  })

  it('hides online/offline toggle for hybrid audits', async () => {
    const expectedCalls = [aaApiCalls.getSettings(auditSettings.hybridAll)]
    await withMockFetch(expectedCalls, async () => {
      renderSettings()

      await screen.findByRole('heading', { name: 'Audit Settings' })

      expect(
        screen.queryByRole('heading', { name: 'Audit Board Data Entry' })
      ).not.toBeInTheDocument()
    })
  })

  it('displays error when no selection done', async () => {
    const expectedCalls = [aaApiCalls.getSettings(auditSettings.blank)]
    await withMockFetch(expectedCalls, async () => {
      renderSettings()

      await screen.findByRole('heading', { name: 'Audit Settings' })
    })

    userEvent.click(screen.getByRole('button', { name: 'Save & Next' }))

    await waitFor(() => {
      expect(screen.queryAllByText('Required').length).toBe(3)
    })
  })
})
