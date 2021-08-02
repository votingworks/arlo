import React from 'react'
import { fireEvent, waitFor, render, screen } from '@testing-library/react'
import { toast } from 'react-toastify'
import { useParams } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import { regexpEscape } from '../../../testUtilities'
import * as utilities from '../../../utilities'
import Contests from './index'
import relativeStages from '../_mocks'
import { contestsInputMocks, contestMocks } from './_mocks'
import { numberifyContest, IContestNumbered } from '../../useContests'
import { IJurisdiction } from '../../useJurisdictions'
import { IContest } from '../../../../types'
import { jurisdictionMocks } from '../../useSetupMenuItems/_mocks'

const toastSpy = jest.spyOn(toast, 'error').mockImplementation()
const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)

const generateApiMock = (
  contestsReturn: { contests: IContest[] } | Error | { status: 'ok' },
  jurisdictionReturn:
    | { jurisdictions: IJurisdiction[] }
    | Error
    | { status: 'ok' }
) => async (
  endpoint: string
): Promise<
  | { contests: IContest[] }
  | { jurisdictions: IJurisdiction[] }
  | Error
  | { status: 'ok' }
> => {
  switch (endpoint) {
    case '/election/1/jurisdiction':
      return jurisdictionReturn
    case '/election/1/contest':
    default:
      return contestsReturn
  }
}

apiMock.mockImplementation(
  generateApiMock(contestMocks.emptyTargeted, { jurisdictions: [] })
)

checkAndToastMock.mockReturnValue(false)

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'), // use actual for all non-hook parts
  useParams: jest.fn(),
}))
const routeMock = useParams as jest.Mock
routeMock.mockReturnValue({
  electionId: '1',
  view: 'setup',
})

const { nextStage, prevStage } = relativeStages('target-contests')

function typeInto(input: Element, value: string): void {
  // TODO: do more, like `focusIn`, `focusOut`, `input`, etc?
  fireEvent.focus(input)
  fireEvent.change(input, { target: { value } })
  fireEvent.blur(input)
}

function regexify(contest: IContestNumbered) {
  return {
    ...contest,
    id: expect.stringMatching(/^[-0-9a-z]*$/),
    choices: contest.choices.map(c => ({
      ...c,
      id: expect.stringMatching(/^[-0-9a-z]*$/),
    })),
  }
}

afterEach(() => {
  ;(nextStage.activate as jest.Mock).mockClear()
  apiMock.mockClear()
  checkAndToastMock.mockClear()
  toastSpy.mockClear()
})

describe('Audit Setup > Contests', () => {
  it('renders empty targeted state correctly', async () => {
    const { container, findByText } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted
        {...relativeStages('target-contests')}
      />
    )
    await findByText('Target Contests')
    expect(container).toMatchSnapshot()
  })

  it('renders empty opportunistic state correctly', async () => {
    apiMock.mockImplementation(
      generateApiMock(contestMocks.emptyOpportunistic, { jurisdictions: [] })
    )
    const { container, findByText } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted={false}
        {...relativeStages('opportunistic-contests')}
      />
    )
    await findByText('Opportunistic Contests')
    expect(container).toMatchSnapshot()
  })

  it('renders filled targeted state correctly', async () => {
    apiMock.mockImplementation(
      generateApiMock(contestMocks.filledTargeted, { jurisdictions: [] })
    )
    const { container, findByText } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted
        {...relativeStages('target-contests')}
      />
    )
    await findByText('Target Contests')
    expect(container).toMatchSnapshot()
  })

  it('renders filled opportunistic state correctly', async () => {
    apiMock.mockImplementation(
      generateApiMock(contestMocks.filledOpportunistic, { jurisdictions: [] })
    )
    const { container, findByText } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted={false}
        {...relativeStages('opportunistic-contests')}
      />
    )
    await findByText('Opportunistic Contests')
    expect(container).toMatchSnapshot()
  })

  it('adds and removes contests', async () => {
    const { getByText, getAllByText, queryByText } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted
        {...relativeStages('target-contests')}
      />
    )

    fireEvent.click(await screen.findByText('Add another targeted contest'))

    expect(
      getAllByText('Enter the name of the contest that will drive the audit.')
        .length
    ).toBe(2)
    expect(getByText('Contest 1 Name')).toBeTruthy()
    expect(getByText('Contest 2 Name')).toBeTruthy()

    fireEvent.click(getByText('Remove Contest 2'))

    expect(
      getAllByText('Enter the name of the contest that will drive the audit.')
        .length
    ).toBe(1)
    expect(getByText('Contest Name')).toBeTruthy()
    await waitFor(() => {
      expect(queryByText('Contest 2')).not.toBeInTheDocument()
      expect(queryByText('Remove Contest 1')).not.toBeInTheDocument()
    })
  })

  it('adds and removes choices', async () => {
    apiMock.mockImplementation(
      generateApiMock(contestMocks.emptyTargeted, { jurisdictions: [] })
    )
    const { findByText, getByText, getAllByText, queryAllByText } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted
        {...relativeStages('target-contests')}
      />
    )

    fireEvent.click(await findByText('Add a new candidate/choice'), {
      bubbles: true,
    })

    expect(getAllByText(/Name of Candidate\/Choice \d/i).length).toBe(3)
    expect(getAllByText(/Votes for Candidate\/Choice \d/i).length).toBe(3)
    expect(getAllByText(/Remove choice \d/i).length).toBe(3)

    fireEvent.click(getByText('Remove choice 1'), { bubbles: true })

    await waitFor(() => {
      expect(queryAllByText(/Remove choice \d/i).length).toBe(0)
      expect(getAllByText(/Name of Candidate\/Choice \d/i).length).toBe(2)
      expect(getAllByText(/Votes for Candidate\/Choice \d/i).length).toBe(2)
    })
  })

  it('is able to submit the form successfully', async () => {
    apiMock.mockImplementation(
      generateApiMock(contestMocks.emptyTargeted, {
        jurisdictions: jurisdictionMocks.noManifests,
      })
    )
    const { findByText, getByLabelText, getByText } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted
        nextStage={nextStage}
        prevStage={prevStage}
      />
    )

    await findByText('Target Contests')
    contestsInputMocks.inputs.forEach(inputData => {
      const input = getByLabelText(new RegExp(regexpEscape(inputData.key)), {
        selector: 'input',
      }) as HTMLInputElement
      typeInto(input, inputData.value)
      expect(input.value).toBe(inputData.value)
    })

    userEvent.click(
      screen.getByRole('button', { name: 'Select Jurisdictions' })
    )
    userEvent.click(screen.getByRole('checkbox', { name: 'Jurisdiction 1' }))

    fireEvent.click(getByText('Save & Next'), { bubbles: true })
    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledTimes(4)
      expect(apiMock.mock.calls[3][0]).toBe('/election/1/contest')
      expect(apiMock.mock.calls[3][1]).toMatchObject({
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (apiMock.mock.calls[3][1]!.body) {
        expect(
          JSON.parse(apiMock.mock.calls[3][1]!.body as string)
        ).toMatchObject(
          contestMocks.filledTargeted.contests.map(c =>
            regexify(numberifyContest(c))
          )
        )
      }
      expect(nextStage.activate).toHaveBeenCalledTimes(1)
    })
  })

  it('it should skip to next stage when opportunistic contest form is clean and not touched', async () => {
    const { findByText, getByText } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted={false}
        nextStage={nextStage}
        prevStage={prevStage}
      />
    )

    await findByText('Opportunistic Contests')
    fireEvent.click(getByText('Save & Next'), { bubbles: true })
    await waitFor(() => {
      expect(nextStage.activate).toHaveBeenCalledTimes(1)
    })
  })

  it('it should not skip to next stage when targeted contest form is clean and not touched', async () => {
    const { findByText, getByText } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted
        nextStage={nextStage}
        prevStage={prevStage}
      />
    )

    await findByText('Target Contests')
    fireEvent.click(getByText('Save & Next'), { bubbles: true })
    await waitFor(() => {
      expect(screen.queryAllByText('Required').length).toBe(5)
    })
  })

  it('it should not skip to next stage when opportunistic contest form is touched', async () => {
    const { findByText, findByLabelText, getByText } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted={false}
        nextStage={nextStage}
        prevStage={prevStage}
      />
    )

    await findByText('Opportunistic Contests')
    typeInto(
      await findByLabelText('Votes Allowed', {
        selector: 'input',
      }),
      '2'
    )
    fireEvent.click(getByText('Save & Next'), { bubbles: true })
    await waitFor(() => {
      expect(nextStage.activate).toHaveBeenCalledTimes(0)
    })
  })

  it('displays errors', async () => {
    const { getByLabelText, getByTestId, getByText, findByText } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted
        nextStage={nextStage}
        prevStage={prevStage}
      />
    )

    await findByText('Target Contests')
    await utilities.asyncForEach(
      contestsInputMocks.errorInputs,
      async (inputData: { key: string; value: string; error: string }) => {
        const { key, value, error } = inputData
        const input = getByLabelText(new RegExp(regexpEscape(key)), {
          selector: 'input',
        }) as HTMLInputElement
        const errorID = `${input.name}-error`
        typeInto(input, value)
        await waitFor(() => {
          expect({
            text: getByTestId(errorID).textContent,
            context: `${key}, ${value}: ${input.value}, ${error}`,
          }).toMatchObject({
            text: error,
            context: `${key}, ${value}: ${input.value}, ${error}`,
          })
        })
      }
    )

    fireEvent.click(getByText('Save & Next'), { bubbles: true })
    await waitFor(() => {
      expect(nextStage.activate).toHaveBeenCalledTimes(0)
    })
  })

  it('displays an error when the total votes are greater than the allowed votes and more than one vote is allowed per contest', async () => {
    const { getByLabelText, findByLabelText, getByTestId } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted
        {...relativeStages('target-contests')}
      />
    )

    typeInto(
      await findByLabelText('Votes Allowed', {
        selector: 'input',
      }),
      '2'
    )

    typeInto(
      getByLabelText('Votes for Candidate/Choice 1', {
        selector: 'input',
      }),
      '21'
    )

    typeInto(
      getByLabelText('Votes for Candidate/Choice 2', {
        selector: 'input',
      }),
      '40'
    )

    const totalBallotInput = getByLabelText('Total Ballots for Contest', {
      selector: 'input',
    }) as HTMLInputElement
    typeInto(totalBallotInput, '30')

    await waitFor(() => {
      // 30 ballots * 2 allowed votes / ballot = 60 allowed votes
      // 21 actual votes in choice #1 + 40 actual votes in choice #2 = 61 actual votes
      expect(getByTestId(`${totalBallotInput.name}-error`)).toHaveTextContent(
        'Must be greater than or equal to the sum of votes for each candidate/choice'
      )
    })
  })

  it('displays no error when the total votes are greater than the ballot count, but less than the total allowed votes for a contest', async () => {
    const { findByLabelText, getByLabelText, queryByTestId } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted
        {...relativeStages('target-contests')}
      />
    )

    typeInto(
      await findByLabelText('Votes Allowed', {
        selector: 'input',
      }),
      '2'
    )

    typeInto(
      getByLabelText('Votes for Candidate/Choice 1', {
        selector: 'input',
      }),
      '20'
    )

    typeInto(
      getByLabelText('Votes for Candidate/Choice 2', {
        selector: 'input',
      }),
      '40'
    )

    const totalBallotInput = getByLabelText('Total Ballots for Contest', {
      selector: 'input',
    }) as HTMLInputElement
    typeInto(totalBallotInput, '30')

    await waitFor(() => {
      // 30 ballots * 2 allowed votes / ballot = 60 allowed votes
      // 20 actual votes in choice #1 + 40 actual votes in choice #2 = 60 actual votes
      expect(queryByTestId(`${totalBallotInput.name}-error`)).toBeNull()
    })
  })

  it('handles submission when there is a pre-existing contest', async () => {
    apiMock
      .mockImplementationOnce(
        generateApiMock(contestMocks.filledOpportunistic, {
          jurisdictions: jurisdictionMocks.noManifests,
        })
      )
      .mockImplementationOnce(
        generateApiMock(contestMocks.filledOpportunistic, {
          jurisdictions: jurisdictionMocks.noManifests,
        })
      )
      .mockImplementationOnce(
        generateApiMock(contestMocks.filledOpportunistic, {
          jurisdictions: jurisdictionMocks.noManifests,
        })
      )
      .mockImplementation(
        generateApiMock(
          { status: 'ok' },
          {
            jurisdictions: jurisdictionMocks.noManifests,
          }
        )
      )
    const { getAllByLabelText, getAllByText, findByText } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted
        nextStage={nextStage}
        prevStage={prevStage}
      />
    )

    await findByText('Target Contests')
    contestsInputMocks.inputs.forEach(inputData => {
      const input = getAllByLabelText(new RegExp(regexpEscape(inputData.key)), {
        selector: 'input',
      }) as HTMLInputElement[]
      typeInto(input[input.length - 1], inputData.value)
      expect(input[input.length - 1].value).toBe(inputData.value)
    })

    userEvent.click(
      screen.getByRole('button', { name: 'Select Jurisdictions' })
    )
    userEvent.click(screen.getByRole('checkbox', { name: 'Jurisdiction 1' }))

    const submit = getAllByText('Save & Next')
    fireEvent.click(submit[submit.length - 1], { bubbles: true })
    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledTimes(4)
      expect(toastSpy).toHaveBeenCalledTimes(0)
      if (apiMock.mock.calls[3][1]!.body) {
        expect(
          JSON.parse(apiMock.mock.calls[3][1]!.body as string)[1]
        ).toMatchObject(
          regexify(numberifyContest(contestMocks.filledTargeted.contests[0]))
        )
        expect(
          JSON.parse(apiMock.mock.calls[3][1]!.body as string)[0]
        ).toMatchObject(
          regexify(
            numberifyContest(contestMocks.filledOpportunistic.contests[0])
          )
        )
      }
      expect(nextStage.activate).toHaveBeenCalledTimes(1)
    })
  })

  it('selects, deselections, and submits jurisdictions', async () => {
    apiMock.mockImplementation(
      generateApiMock(contestMocks.filledTargeted, {
        jurisdictions: jurisdictionMocks.noManifests,
      })
    )
    const { getByText, findByText, findByLabelText } = render(
      <Contests
        auditType="BALLOT_POLLING"
        locked={false}
        isTargeted
        {...relativeStages('target-contests')}
      />
    )
    const dropDown = await findByText('Select Jurisdictions')
    fireEvent.click(dropDown, { bubbles: true })
    const selectAll = await findByLabelText('Select all')
    const jurisdictionOne = await findByLabelText('Jurisdiction 1')
    const jurisdictionTwo = await findByLabelText('Jurisdiction 2')
    fireEvent.click(selectAll, { bubbles: true })
    fireEvent.click(selectAll, { bubbles: true })
    fireEvent.click(jurisdictionOne, { bubbles: true })
    fireEvent.click(jurisdictionTwo, { bubbles: true })
    fireEvent.click(jurisdictionOne, { bubbles: true })

    fireEvent.click(getByText('Save & Next'), { bubbles: true })
    await waitFor(() => {
      expect(apiMock).toHaveBeenCalledTimes(4)
      expect(apiMock.mock.calls[3][0]).toBe('/election/1/contest')
      expect(apiMock.mock.calls[3][1]).toMatchObject({
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      const submittedBody: IContestNumbered[] = JSON.parse(apiMock.mock
        .calls[3][1]!.body as string)
      expect(submittedBody[0].jurisdictionIds).toMatchObject([
        'jurisdiction-id-2',
      ])
    })
  })
})
