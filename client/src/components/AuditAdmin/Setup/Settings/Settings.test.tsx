import { describe, expect, it, vi } from 'vitest'
import React from 'react'
import { waitFor, screen, render, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClientProvider } from 'react-query'
import Settings from './Settings'
import { withMockFetch, createQueryClient } from '../../../testUtilities'
import { aaApiCalls, auditSettingsMocks } from '../../../_mocks'

const renderSettings = () => {
  const goToNextStage = vi.fn()
  const goToPrevStage = vi.fn()
  return {
    goToNextStage,
    goToPrevStage,
    ...render(
      <QueryClientProvider client={createQueryClient()}>
        <Settings
          electionId="1"
          goToNextStage={goToNextStage}
          goToPrevStage={goToPrevStage}
        />
      </QueryClientProvider>
    ),
  }
}

describe('Setup > Settings', () => {
  it('updates settings', async () => {
    const updatedSettings = {
      ...auditSettingsMocks.blank,
      state: 'CA',
      electionName: 'Election Name',
      online: true,
      riskLimit: 5,
      randomSeed: '12345',
    }
    const expectedCalls = [
      aaApiCalls.getSettings(auditSettingsMocks.blank),
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
        screen.getByLabelText(/Enter a series of random numbers/),
        '12345'
      )

      userEvent.click(screen.getByRole('button', { name: /Save & Next/ }))

      await waitFor(() => {
        expect(goToNextStage).toHaveBeenCalled()
      })
    })
  })

  it('hides online/offline toggle for batch comparison audits', async () => {
    const expectedCalls = [
      aaApiCalls.getSettings(auditSettingsMocks.batchComparisonAll),
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
      aaApiCalls.getSettings(auditSettingsMocks.ballotComparisonAll),
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
    const expectedCalls = [aaApiCalls.getSettings(auditSettingsMocks.hybridAll)]
    await withMockFetch(expectedCalls, async () => {
      renderSettings()

      await screen.findByRole('heading', { name: 'Audit Settings' })

      expect(
        screen.queryByRole('heading', { name: 'Audit Board Data Entry' })
      ).not.toBeInTheDocument()
    })
  })

  it('displays error when no selection done', async () => {
    const expectedCalls = [aaApiCalls.getSettings(auditSettingsMocks.blank)]
    await withMockFetch(expectedCalls, async () => {
      renderSettings()

      await screen.findByRole('heading', { name: 'Audit Settings' })
    })

    userEvent.click(screen.getByRole('button', { name: /Save & Next/ }))

    await waitFor(() => {
      expect(screen.queryAllByText('Required').length).toBe(3)
    })
  })

  it('shows a presentation mode modal for random seed entry', async () => {
    const expectedSettings = {
      ...auditSettingsMocks.blank,
      randomSeed: '12345',
      // Default values
      riskLimit: 10,
      electionName: '',
      state: '',
    }
    const expectedCalls = [
      aaApiCalls.getSettings(auditSettingsMocks.blank),
      aaApiCalls.putSettings(expectedSettings),
      aaApiCalls.getSettings(expectedSettings),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderSettings()

      await screen.findByRole('heading', { name: 'Audit Settings' })

      userEvent.click(screen.getByRole('button', { name: 'Presentation Mode' }))
      let modal = screen
        .getByRole('heading', { name: 'Enter Random Seed' })
        .closest('div.bp3-dialog')! as HTMLElement
      const saveButton = within(modal).getByRole('button', {
        name: /Set Random Seed/,
      })
      expect(saveButton).toBeDisabled()

      const modalSeedInput = within(modal).getByLabelText(
        /Enter a series of random numbers/
      )
      expect(modalSeedInput).toHaveValue('')

      userEvent.type(modalSeedInput, '12345')
      expect(modalSeedInput).toHaveValue('12345')

      userEvent.click(saveButton)
      expect(saveButton).toBeDisabled()
      await waitFor(() => {
        expect(modal).not.toBeInTheDocument()
      })

      const seedInput = screen.getByLabelText(
        /Enter a series of random numbers/
      )
      expect(seedInput).toHaveValue('12345')
      userEvent.type(seedInput, '6')

      userEvent.click(screen.getByRole('button', { name: 'Presentation Mode' }))
      modal = screen
        .getByRole('heading', { name: 'Enter Random Seed' })
        .closest('div.bp3-dialog')! as HTMLElement
      expect(
        within(modal).getByLabelText(/Enter a series of random numbers/)
      ).toHaveValue('123456')

      userEvent.click(within(modal).getByRole('button', { name: 'Close' }))
      await waitFor(() => {
        expect(modal).not.toBeInTheDocument()
      })
    })
  })
})
