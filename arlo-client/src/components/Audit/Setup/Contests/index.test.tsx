import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { useParams } from 'react-router-dom'
import { regexpEscape } from '../../../testUtilities'
import * as utilities from '../../../utilities'
import Contests from './index'
import relativeStages from '../_mocks'
import { contestsInputMocks, contestMocks } from './_mocks'
import { numberifyContest, IContestNumbered } from './useContestsApi'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()
const checkAndToastMock: jest.SpyInstance<
  ReturnType<typeof utilities.checkAndToast>,
  Parameters<typeof utilities.checkAndToast>
> = jest.spyOn(utilities, 'checkAndToast').mockReturnValue(false)
apiMock.mockResolvedValue(contestMocks.emptyTargeted)

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

const { nextStage, prevStage } = relativeStages('Target Contests')

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
})

describe('Audit Setup > Contests', () => {
  it('renders empty targeted state correctly', () => {
    const { container } = render(
      <Contests
        locked={false}
        isTargeted
        {...relativeStages('Target Contests')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders empty opportunistic state correctly', () => {
    apiMock.mockResolvedValue(contestMocks.emptyOpportunistic)
    const { container } = render(
      <Contests
        locked={false}
        isTargeted={false}
        {...relativeStages('Opportunistic Contests')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders filled targeted state correctly', () => {
    apiMock.mockResolvedValue(contestMocks.filledTargeted)
    const { container } = render(
      <Contests
        locked={false}
        isTargeted
        {...relativeStages('Target Contests')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders filled opportunistic state correctly', () => {
    apiMock.mockResolvedValue(contestMocks.filledOpportunistic)
    const { container } = render(
      <Contests
        locked={false}
        isTargeted={false}
        {...relativeStages('Opportunistic Contests')}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it.skip('adds and removes contests', async () => {
    // skip until feature is complete in backend
    const { getByText, getAllByText, queryByText } = render(
      <Contests
        locked={false}
        isTargeted
        {...relativeStages('Target Contests')}
      />
    )

    fireEvent.click(getByText('Add another targeted contest'))

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
    await wait(() => {
      expect(queryByText('Contest 2')).not.toBeInTheDocument()
      expect(queryByText('Remove Contest 1')).not.toBeInTheDocument()
    })
  })

  it('adds and removes choices', async () => {
    const { getByText, getAllByText, queryAllByText } = render(
      <Contests
        locked={false}
        isTargeted
        {...relativeStages('Target Contests')}
      />
    )

    fireEvent.click(getByText('Add a new candidate/choice'), { bubbles: true })

    expect(getAllByText(/Name of Candidate\/Choice \d/i).length).toBe(3)
    expect(getAllByText(/Votes for Candidate\/Choice \d/i).length).toBe(3)
    expect(getAllByText(/Remove choice \d/i).length).toBe(3)

    fireEvent.click(getByText('Remove choice 1'), { bubbles: true })

    await wait(() => {
      expect(queryAllByText(/Remove choice \d/i).length).toBe(0)
      expect(getAllByText(/Name of Candidate\/Choice \d/i).length).toBe(2)
      expect(getAllByText(/Votes for Candidate\/Choice \d/i).length).toBe(2)
    })
  })

  it('is able to submit the form successfully', async () => {
    apiMock.mockResolvedValue(contestMocks.emptyTargeted)
    const { getByLabelText, getByText } = render(
      <Contests
        locked={false}
        isTargeted
        nextStage={nextStage}
        prevStage={prevStage}
      />
    )

    contestsInputMocks.inputs.forEach(inputData => {
      const input = getByLabelText(new RegExp(regexpEscape(inputData.key)), {
        selector: 'input',
      }) as HTMLInputElement
      typeInto(input, inputData.value)
      expect(input.value).toBe(inputData.value)
    })

    fireEvent.click(getByText('Save & Next'), { bubbles: true })
    await wait(() => {
      expect(apiMock).toHaveBeenCalledTimes(3)
      expect(apiMock.mock.calls[2][0]).toBe('/election/1/contest')
      expect(apiMock.mock.calls[2][1]).toMatchObject({
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      if (apiMock.mock.calls[2][1]!.body) {
        expect(
          JSON.parse(apiMock.mock.calls[2][1]!.body as string)
        ).toMatchObject(
          contestMocks.filledTargeted.contests.map(c =>
            regexify(numberifyContest(c))
          )
        )
      }
      expect(nextStage.activate).toHaveBeenCalledTimes(1)
    })
  })

  it('displays errors', async () => {
    const { getByLabelText, getByTestId, getByText } = render(
      <Contests
        locked={false}
        isTargeted
        nextStage={nextStage}
        prevStage={prevStage}
      />
    )

    await utilities.asyncForEach(
      contestsInputMocks.errorInputs,
      async (inputData: { key: string; value: string; error: string }) => {
        const { key, value, error } = inputData
        const input = getByLabelText(new RegExp(regexpEscape(key)), {
          selector: 'input',
        }) as HTMLInputElement
        const errorID = `${input.name}-error`
        typeInto(input, value)
        await wait(() => {
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
    await wait(() => {
      expect(nextStage.activate).toHaveBeenCalledTimes(0)
    })
  })

  it('displays an error when the total votes are greater than the allowed votes and more than one vote is allowed per contest', async () => {
    const { getByLabelText, getByTestId } = render(
      <Contests
        locked={false}
        isTargeted
        {...relativeStages('Target Contests')}
      />
    )

    typeInto(
      getByLabelText('Votes Allowed', {
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

    await wait(() => {
      // 30 ballots * 2 allowed votes / ballot = 60 allowed votes
      // 21 actual votes in choice #1 + 40 actual votes in choice #2 = 61 actual votes
      expect(getByTestId(`${totalBallotInput.name}-error`).textContent).toBe(
        'Must be greater than or equal to the sum of votes for each candidate/choice'
      )
    })
  })

  it('displays no error when the total votes are greater than the ballot count, but less than the total allowed votes for a contest', async () => {
    const { getByLabelText, queryByTestId } = render(
      <Contests
        locked={false}
        isTargeted
        {...relativeStages('Target Contests')}
      />
    )

    typeInto(
      getByLabelText('Votes Allowed', {
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

    await wait(() => {
      // 30 ballots * 2 allowed votes / ballot = 60 allowed votes
      // 20 actual votes in choice #1 + 40 actual votes in choice #2 = 60 actual votes
      expect(queryByTestId(`${totalBallotInput.name}-error`)).toBeNull()
    })
  })
})
