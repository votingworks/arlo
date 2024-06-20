import React from 'react'
import { screen } from '@testing-library/react'
import { QueryClientProvider } from 'react-query'
import { Classes } from '@blueprintjs/core'
import userEvent from '@testing-library/user-event'
import {
  createQueryClient,
  withMockFetch,
  renderWithRouter,
} from '../../testUtilities'
import {
  auditSettingsMocks,
  aaApiCalls,
  jurisdictionFileMocks,
  standardizedContestsFileMocks,
  contestMocks,
} from '../../_mocks'
import Setup, { ISetupProps } from './Setup'
import { sampleSizeMock } from './Review/_mocks'

const renderSetup = (props: Partial<ISetupProps> = {}) =>
  renderWithRouter(
    <QueryClientProvider client={createQueryClient()}>
      <Setup
        electionId="1"
        auditSettings={auditSettingsMocks.blank}
        startNextRound={jest.fn()}
        isAuditStarted={false}
        {...props}
      />
    </QueryClientProvider>
  )

const getMenuItem = (name: string) => screen.getByRole('link', { name })

const expectEnabledMenuItem = (name: string) => {
  const menuItem = getMenuItem(name)
  expect(menuItem).not.toHaveClass(Classes.DISABLED)
  expect(menuItem).not.toHaveClass(Classes.ACTIVE)
}

const expectDisabledMenuItem = (name: string) => {
  const menuItem = getMenuItem(name)
  expect(menuItem).toHaveClass(Classes.DISABLED)
  expect(menuItem).not.toHaveClass(Classes.ACTIVE)
}

const expectActiveMenuItem = (name: string) => {
  const menuItem = getMenuItem(name)
  expect(menuItem).not.toHaveClass(Classes.DISABLED)
  expect(menuItem).toHaveClass(Classes.ACTIVE)
}

describe('Setup', () => {
  it('starts on the Participants stage with other stages disabled', async () => {
    const expectedCalls = [
      aaApiCalls.getJurisdictionFileWithResponse(jurisdictionFileMocks.empty),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderSetup()
      await screen.findByRole('heading', { name: 'Audit Setup' })
      screen.getByRole('heading', { name: 'Participants' })

      expectActiveMenuItem('Participants')
      expectDisabledMenuItem('Target Contests')
      expectDisabledMenuItem('Opportunistic Contests')
      expectDisabledMenuItem('Audit Settings')
      expectDisabledMenuItem('Review & Launch')
    })
  })

  it('on the Participants stage, enables the next stages once the file is processed', async () => {
    const expectedCalls = [
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderSetup()
      await screen.findByRole('heading', { name: 'Audit Setup' })
      screen.getByRole('heading', { name: 'Participants' })

      expectActiveMenuItem('Participants')
      expectEnabledMenuItem('Target Contests')
      expectEnabledMenuItem('Opportunistic Contests')
      expectEnabledMenuItem('Audit Settings')
      expectEnabledMenuItem('Review & Launch')

      userEvent.click(screen.getByRole('button', { name: /Next/ }))
      await screen.findByRole('heading', { name: 'Target Contests' })

      userEvent.click(screen.getByRole('button', { name: /Back/ }))
      await screen.findByRole('heading', { name: 'Participants' })
    })
  })

  const standardizedContestAuditTypes = [
    {
      auditTypeLabel: 'ballot comparison',
      auditSettings: auditSettingsMocks.blankBallotComparison,
    },
    {
      auditTypeLabel: 'hybrid',
      auditSettings: auditSettingsMocks.blankHybrid,
    },
  ]
  standardizedContestAuditTypes.forEach(({ auditTypeLabel, auditSettings }) => {
    it(`in ${auditTypeLabel} audits, on the Participants stage, disabled the next stages when files are not processed`, async () => {
      const expectedCalls = [
        aaApiCalls.getJurisdictionFileWithResponse(
          jurisdictionFileMocks.processed
        ),
        aaApiCalls.getStandardizedContestsFile(
          standardizedContestsFileMocks.empty
        ),
      ]
      await withMockFetch(expectedCalls, async () => {
        renderSetup({ auditSettings })
        await screen.findByRole('heading', { name: 'Audit Setup' })
        screen.getByRole('heading', { name: 'Participants & Contests' })

        expectActiveMenuItem('Participants')
        expectDisabledMenuItem('Target Contests')
        expectDisabledMenuItem('Opportunistic Contests')
        expectDisabledMenuItem('Audit Settings')
        expectDisabledMenuItem('Review & Launch')
      })
    })

    it(`in ${auditTypeLabel} audits, on the Participants stage, enables the next stages when files are processed`, async () => {
      const expectedCalls = [
        aaApiCalls.getJurisdictionFileWithResponse(
          jurisdictionFileMocks.processed
        ),
        aaApiCalls.getStandardizedContestsFile(
          standardizedContestsFileMocks.processed
        ),
      ]
      await withMockFetch(expectedCalls, async () => {
        renderSetup({ auditSettings: auditSettingsMocks.blankBallotComparison })
        await screen.findByRole('heading', { name: 'Audit Setup' })
        screen.getByRole('heading', { name: 'Participants & Contests' })

        expectActiveMenuItem('Participants')
        expectEnabledMenuItem('Target Contests')
        expectEnabledMenuItem('Opportunistic Contests')
        expectEnabledMenuItem('Audit Settings')
        expectEnabledMenuItem('Review & Launch')
      })
    })
  })

  it('navigates to the Target Contests stage', async () => {
    const expectedCalls = [
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderSetup()
      await screen.findByRole('heading', { name: 'Audit Setup' })
      screen.getByRole('heading', { name: 'Participants' })

      userEvent.click(getMenuItem('Target Contests'))
      await screen.findByRole('heading', { name: 'Target Contests' })

      userEvent.click(screen.getByRole('button', { name: /Back/ }))
      await screen.findByRole('heading', { name: 'Participants' })
    })
  })

  it('navigates to the Opportunistic Contests stage', async () => {
    const expectedCalls = [
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderSetup()
      await screen.findByRole('heading', { name: 'Audit Setup' })
      screen.getByRole('heading', { name: 'Participants' })

      userEvent.click(getMenuItem('Opportunistic Contests'))
      await screen.findByRole('heading', { name: 'Opportunistic Contests' })

      userEvent.click(screen.getByRole('button', { name: /Back/ }))
      await screen.findByRole('heading', { name: 'Target Contests' })
    })
  })

  it('in batch comparison audits, hides the Opportunistic Contests stage', async () => {
    const expectedCalls = [aaApiCalls.getJurisdictionFile]
    await withMockFetch(expectedCalls, async () => {
      renderSetup({ auditSettings: auditSettingsMocks.blankBatch })
      await screen.findByRole('heading', { name: 'Audit Setup' })
      screen.getByRole('heading', { name: 'Participants' })

      expectActiveMenuItem('Participants')
      expectEnabledMenuItem('Target Contests')
      expectEnabledMenuItem('Audit Settings')
      expectEnabledMenuItem('Review & Launch')
      expect(
        screen.queryByText('Opportunistic Contests')
      ).not.toBeInTheDocument()
    })
  })

  it('navigates to the Audit Settings stage', async () => {
    const expectedCalls = [
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getSettings(auditSettingsMocks.blank),
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderSetup()
      await screen.findByRole('heading', { name: 'Audit Setup' })
      screen.getByRole('heading', { name: 'Participants' })

      userEvent.click(getMenuItem('Audit Settings'))
      await screen.findByRole('heading', { name: 'Audit Settings' })

      userEvent.click(screen.getByRole('button', { name: /Back/ }))
      await screen.findByRole('heading', { name: 'Opportunistic Contests' })
    })
  })

  it('navigates to the Review & Launch stage', async () => {
    const expectedCalls = [
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getSettings(auditSettingsMocks.blank),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests([]),
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getContestChoiceNameStandardizations(),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderSetup()
      await screen.findByRole('heading', { name: 'Audit Setup' })
      screen.getByRole('heading', { name: 'Participants' })

      userEvent.click(getMenuItem('Review & Launch'))
      await screen.findByRole('heading', { name: 'Review & Launch' })

      userEvent.click(screen.getByRole('button', { name: /Back/ }))
      await screen.findByRole('heading', { name: 'Audit Settings' })
    })
  })

  it('only shows the disabled Review & Launch stage after the audit is launched', async () => {
    const expectedCalls = [
      aaApiCalls.getJurisdictionFile,
      aaApiCalls.getSettings(auditSettingsMocks.all),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests([]),
      aaApiCalls.getContests(contestMocks.filledTargeted),
      aaApiCalls.getContestChoiceNameStandardizations(),
      aaApiCalls.getSampleSizes(sampleSizeMock.ballotPolling),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderSetup({ isAuditStarted: true })
      await screen.findByRole('heading', { name: 'Audit Setup' })
      screen.getByRole('heading', { name: 'Review & Launch' })

      expect(
        screen.getByRole('button', { name: 'Launch Audit' })
      ).toBeDisabled()

      expectDisabledMenuItem('Participants')
      expectDisabledMenuItem('Target Contests')
      expectDisabledMenuItem('Opportunistic Contests')
      expectDisabledMenuItem('Audit Settings')
      expectActiveMenuItem('Review & Launch')
    })
  })
})
