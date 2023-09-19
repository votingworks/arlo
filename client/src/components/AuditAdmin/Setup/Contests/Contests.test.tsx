import React from 'react'
import { waitFor, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import uuidv4 from 'uuidv4'
import { QueryClientProvider } from 'react-query'
import {
  regexpEscape,
  withMockFetch,
  createQueryClient,
} from '../../../testUtilities'
import * as utilities from '../../../utilities'
import Contests, { IContestsProps } from './Contests'
import { contestsInputMocks } from './_mocks'
import { contestMocks, aaApiCalls } from '../../../_mocks'

jest.mock('uuidv4')

const renderContests = (props: Partial<IContestsProps> = {}) => {
  const goToNextStage = jest.fn()
  const goToPrevStage = jest.fn()
  return {
    goToNextStage,
    goToPrevStage,
    ...render(
      <QueryClientProvider client={createQueryClient()}>
        <Contests
          electionId="1"
          auditType="BALLOT_POLLING"
          isTargeted
          goToNextStage={goToNextStage}
          goToPrevStage={goToPrevStage}
          {...props}
        />
      </QueryClientProvider>
    ),
  }
}

describe('Audit Setup > Contests', () => {
  it('renders empty targeted state correctly', async () => {
    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderContests()
      await screen.findByText('Target Contests')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders empty opportunistic state correctly', async () => {
    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderContests({ isTargeted: false })
      await screen.findByText('Opportunistic Contests')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders filled targeted state correctly', async () => {
    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.filledTargeted),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderContests()
      await screen.findByText('Target Contests')
      expect(container).toMatchSnapshot()
    })
  })

  it('renders filled opportunistic state correctly', async () => {
    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.filledOpportunistic),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { container } = renderContests({ isTargeted: false })
      await screen.findByText('Opportunistic Contests')
      expect(container).toMatchSnapshot()
    })
  })

  it('adds and removes contests', async () => {
    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderContests()

      userEvent.click(
        await screen.findByRole('button', { name: /Add Contest/ })
      )

      expect(
        screen.getAllByText(
          'Enter the name of the contest that will drive the audit.'
        ).length
      ).toBe(2)
      expect(screen.getByText('Contest 1 Name')).toBeTruthy()
      expect(screen.getByText('Contest 2 Name')).toBeTruthy()

      userEvent.click(
        screen.getAllByRole('button', { name: /Remove Contest/ })[1]
      )

      expect(
        screen.getAllByText(
          'Enter the name of the contest that will drive the audit.'
        ).length
      ).toBe(1)
      expect(screen.getByText('Contest Name')).toBeTruthy()
      await waitFor(() => {
        expect(screen.queryByText('Contest 2')).not.toBeInTheDocument()
        expect(screen.queryByText('Remove Contest')).not.toBeInTheDocument()
      })
    })
  })

  it('adds and removes choices', async () => {
    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderContests()

      userEvent.click(await screen.findByText('Add a new candidate/choice'))

      expect(screen.getAllByText(/Name of Candidate\/Choice \d/i).length).toBe(
        3
      )
      expect(
        screen.getAllByText(/Votes for Candidate\/Choice \d/i).length
      ).toBe(3)
      expect(screen.getAllByText(/Remove choice \d/i).length).toBe(3)

      userEvent.click(screen.getByText('Remove choice 1'))

      await waitFor(() => {
        expect(screen.queryAllByText(/Remove choice \d/i).length).toBe(0)
        expect(
          screen.getAllByText(/Name of Candidate\/Choice \d/i).length
        ).toBe(2)
        expect(
          screen.getAllByText(/Votes for Candidate\/Choice \d/i).length
        ).toBe(2)
      })
    })
  })

  it('is able to submit the form successfully', async () => {
    const uuids = ['contest-id', 'choice-id-1', 'choice-id-2']
    let uuidIndex = -1
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(uuidv4 as any).mockImplementation(() => {
      uuidIndex += 1
      return uuids[uuidIndex] || 'missing-uuid-in-mock'
    })

    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
      aaApiCalls.putContests(contestMocks.filledTargeted),
      aaApiCalls.getContests(contestMocks.filledTargeted),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { goToNextStage } = renderContests()

      await screen.findByText('Target Contests')
      contestsInputMocks.inputs.forEach(inputData => {
        const input = screen.getByLabelText(
          new RegExp(regexpEscape(inputData.key)),
          { selector: 'input' }
        )
        userEvent.type(input, inputData.value)
      })

      userEvent.click(
        screen.getByRole('button', { name: 'Select Jurisdictions' })
      )
      userEvent.click(
        screen.getByRole('checkbox', { name: 'Jurisdiction One' })
      )

      userEvent.click(screen.getByText(/Save & Next/))
      await waitFor(() => {
        expect(goToNextStage).toHaveBeenCalledTimes(1)
      })
    })
  })

  it('it should skip to next stage when opportunistic contest form is clean and not touched', async () => {
    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { goToNextStage } = renderContests({ isTargeted: false })

      await screen.findByText('Opportunistic Contests')
      userEvent.click(screen.getByText(/Save & Next/))
      await waitFor(() => {
        expect(goToNextStage).toHaveBeenCalledTimes(1)
      })
    })
  })

  it('it should not skip to next stage when targeted contest form is clean and not touched', async () => {
    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { goToNextStage } = renderContests()

      await screen.findByText('Target Contests')
      userEvent.click(screen.getByText(/Save & Next/))
      await waitFor(() => {
        expect(screen.queryAllByText('Required').length).toBe(6)
      })
      expect(goToNextStage).not.toHaveBeenCalled()
    })
  })

  it('it should not skip to next stage when opportunistic contest form is touched', async () => {
    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { goToNextStage } = renderContests({ isTargeted: false })
      await screen.findByText('Opportunistic Contests')
      userEvent.type(
        await screen.findByLabelText('Votes Allowed', {
          selector: 'input',
        }),
        '2'
      )
      userEvent.click(screen.getByText(/Save & Next/))
      await waitFor(() => {
        expect(screen.queryAllByText('Required').length).toBe(6)
      })
      expect(goToNextStage).not.toHaveBeenCalled()
    })
  })

  it('displays errors', async () => {
    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { goToNextStage } = renderContests()

      await screen.findByText('Target Contests')
      await utilities.asyncForEach(
        contestsInputMocks.errorInputs,
        async (inputData: { key: string; value: string; error: string }) => {
          const { key, value, error } = inputData
          const input = screen.getByLabelText(new RegExp(regexpEscape(key)), {
            selector: 'input',
          }) as HTMLInputElement
          const errorID = `${input.name}-error`
          userEvent.clear(input)
          userEvent.type(input, value)
          userEvent.click(document.body) // Simulate blurring by clicking outside
          await waitFor(() => {
            expect({
              text: screen.getByTestId(errorID).textContent,
              context: `${key}, ${value}: ${input.value}, ${error}`,
            }).toMatchObject({
              text: error,
              context: `${key}, ${value}: ${input.value}, ${error}`,
            })
          })
        }
      )

      userEvent.click(screen.getByText(/Save & Next/))
      expect(goToNextStage).toHaveBeenCalledTimes(0)
    })
  })

  it('displays an error when the total votes are greater than the allowed votes and more than one vote is allowed per contest', async () => {
    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderContests()
      const votesAllowedInput = await screen.findByLabelText('Votes Allowed', {
        selector: 'input',
      })
      userEvent.clear(votesAllowedInput)
      userEvent.type(votesAllowedInput, '2')

      userEvent.type(
        screen.getByLabelText('Votes for Candidate/Choice 1', {
          selector: 'input',
        }),
        '21'
      )

      userEvent.type(
        screen.getByLabelText('Votes for Candidate/Choice 2', {
          selector: 'input',
        }),
        '40'
      )

      const totalBallotInput = screen.getByLabelText(
        'Total Ballot Cards Cast for Contest',
        { selector: 'input' }
      ) as HTMLInputElement
      userEvent.type(totalBallotInput, '30')

      userEvent.click(document.body) // Simulate blurring by clicking outside

      await waitFor(() => {
        // 30 ballots * 2 allowed votes / ballot = 60 allowed votes
        // 21 actual votes in choice #1 + 40 actual votes in choice #2 = 61 actual votes
        expect(
          screen.getByTestId(`${totalBallotInput.name}-error`)
        ).toHaveTextContent(
          'Must be greater than or equal to the sum of votes for each candidate/choice'
        )
      })
    })
  })

  it('displays no error when the total votes are greater than the ballot count, but less than the total allowed votes for a contest', async () => {
    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.empty),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
    ]
    await withMockFetch(expectedCalls, async () => {
      renderContests()
      const votesAllowedInput = await screen.findByLabelText('Votes Allowed', {
        selector: 'input',
      })
      userEvent.clear(votesAllowedInput)
      userEvent.type(votesAllowedInput, '2')

      userEvent.type(
        screen.getByLabelText('Votes for Candidate/Choice 1', {
          selector: 'input',
        }),
        '20'
      )

      userEvent.type(
        screen.getByLabelText('Votes for Candidate/Choice 2', {
          selector: 'input',
        }),
        '40'
      )

      const totalBallotInput = screen.getByLabelText(
        'Total Ballot Cards Cast for Contest',
        { selector: 'input' }
      ) as HTMLInputElement
      userEvent.type(totalBallotInput, '30')

      // 30 ballots * 2 allowed votes / ballot = 60 allowed votes
      // 20 actual votes in choice #1 + 40 actual votes in choice #2 = 60 actual votes
      expect(
        screen.queryByTestId(`${totalBallotInput.name}-error`)
      ).not.toBeInTheDocument()
    })
  })

  it('sends all contests to server (both targeted and opportunistic) even though form only edits one set at a time', async () => {
    const uuids = ['contest-id', 'choice-id-1', 'choice-id-2']
    let uuidIndex = -1
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(uuidv4 as any).mockImplementation(() => {
      uuidIndex += 1
      return uuids[uuidIndex] || 'missing-uuid-in-mock'
    })

    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.filledOpportunistic),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
      aaApiCalls.putContests(
        contestMocks.filledTargeted.concat(contestMocks.filledOpportunistic)
      ),
      aaApiCalls.getContests(
        contestMocks.filledOpportunistic.concat(contestMocks.filledTargeted)
      ),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { goToNextStage } = renderContests()
      await screen.findByText('Target Contests')
      contestsInputMocks.inputs.forEach(inputData => {
        const input = screen.getByLabelText(
          new RegExp(regexpEscape(inputData.key)),
          { selector: 'input' }
        )
        userEvent.type(input, inputData.value)
      })

      userEvent.click(
        screen.getByRole('button', { name: 'Select Jurisdictions' })
      )
      userEvent.click(
        screen.getByRole('checkbox', { name: 'Jurisdiction One' })
      )

      userEvent.click(screen.getByRole('button', { name: /Save & Next/ }))
      await waitFor(() => {
        expect(goToNextStage).toHaveBeenCalledTimes(1)
      })
    })
  })

  it('selects, deselections, and submits jurisdictions', async () => {
    const updatedContests = [
      {
        ...contestMocks.filledTargeted[0],
        jurisdictionIds: ['jurisdiction-id-2'],
      },
    ]
    const expectedCalls = [
      aaApiCalls.getContests(contestMocks.filledTargeted),
      aaApiCalls.getJurisdictions,
      aaApiCalls.getStandardizedContests(null),
      aaApiCalls.putContests(updatedContests),
      aaApiCalls.getContests(updatedContests),
    ]
    await withMockFetch(expectedCalls, async () => {
      const { goToNextStage } = renderContests()
      const dropDown = await screen.findByText('Select Jurisdictions')
      userEvent.click(dropDown)
      const selectAll = await screen.findByLabelText('Select all')
      const jurisdictionOne = await screen.findByLabelText('Jurisdiction One')
      const jurisdictionTwo = await screen.findByLabelText('Jurisdiction Two')
      userEvent.click(selectAll)
      userEvent.click(selectAll)
      userEvent.click(jurisdictionOne)
      userEvent.click(jurisdictionTwo)
      userEvent.click(jurisdictionOne)

      userEvent.click(screen.getByText(/Save & Next/))
      await waitFor(() => {
        expect(goToNextStage).toHaveBeenCalledTimes(1)
      })
    })
  })
})
