import React from 'react'
import { waitFor, screen } from '@testing-library/react'
import { Route } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import relativeStages from '../_mocks'
import Settings from './index'
import { renderWithRouter, withMockFetch } from '../../../testUtilities'
import { aaApiCalls } from '../../_mocks'
import { auditSettings } from '../../useSetupMenuItems/_mocks'

const { nextStage, prevStage } = relativeStages('settings')

const renderSettings = () =>
  renderWithRouter(
    <Route path="/election/:electionId/setup">
      <Settings locked={false} nextStage={nextStage} prevStage={prevStage} />
    </Route>,
    { route: '/election/1/setup' }
  )

describe('Setup > Settings', () => {
  jest.setTimeout(10000)
  it('updates settings', async () => {
    const expectedCalls = [
      aaApiCalls.getSettings(auditSettings.blank),
      aaApiCalls.getSettings(auditSettings.blank),
      aaApiCalls.putSettings({
        ...auditSettings.blank,
        state: 'CA',
        electionName: 'Election Name',
        online: true,
        riskLimit: 5,
        randomSeed: '12345',
      }),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderSettings()

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
        expect(nextStage.activate).toHaveBeenCalled()
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
