import React from 'react'
import { render, fireEvent, wait } from '@testing-library/react'
import { toast } from 'react-toastify'
import EstimateSampleSize, {
  TwoColumnSection,
  InputLabelRow,
  InputFieldRow,
  //FieldLeft, TODO: need to mock Formik Field to test these like this
  //FieldRight,
  InputLabel,
  Action,
} from './EstimateSampleSize'
import { regexpEscape } from '../testUtilities'
import { statusStates } from './_mocks'
import * as utilities from '../utilities'

const apiMock: jest.SpyInstance<
  ReturnType<typeof utilities.api>,
  Parameters<typeof utilities.api>
> = jest.spyOn(utilities, 'api').mockImplementation()

const toastSpy = jest.spyOn(toast, 'error').mockImplementation()

afterEach(() => {
  apiMock.mockClear()
  toastSpy.mockClear()
})

const estimateSampleSizeMocks = {
  inputs: [
    { key: 'Election Name', value: 'Election Name' },
    { key: 'Contest Name', value: 'Contest Name' },
    { key: 'Name of Candidate/Choice 1', value: 'Choice One' },
    { key: 'Name of Candidate/Choice 2', value: 'Choice Two' },
    { key: 'Votes for Candidate/Choice 1', value: '10' },
    { key: 'Votes for Candidate/Choice 2', value: '20' },
    { key: 'Total Ballots for Contest', value: '30' },
    {
      key: 'Set the risk for the audit as a percentage (e.g. "5" = 5%)',
      value: '2',
    },
    {
      key:
        'Enter the random characters to seed the pseudo-random number generator.',
      value: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
    },
  ],
  errorInputs: [
    { key: 'Election Name', value: '', error: 'Required' },
    { key: 'Contest Name', value: '', error: 'Required' },
    {
      key: 'Total Ballots for Contest',
      value: '',
      error: 'Must be a number',
    },
    {
      key: 'Total Ballots for Contest',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'Total Ballots for Contest',
      value: '-1',
      error:
        'Must be greater than or equal to the sum of votes for each candidate/choice',
    },
    {
      key: 'Total Ballots for Contest',
      value: '0.5',
      error: 'Must be an integer',
    },
    { key: 'Name of Candidate/Choice 1', value: '', error: 'Required' },
    { key: 'Name of Candidate/Choice 2', value: '', error: 'Required' },
    {
      key: 'Votes for Candidate/Choice 1',
      value: '',
      error: 'Must be a number',
    },
    {
      key: 'Votes for Candidate/Choice 1',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'Votes for Candidate/Choice 1',
      value: '-1',
      error: 'Must be a positive number',
    },
    {
      key: 'Votes for Candidate/Choice 1',
      value: '0.5',
      error: 'Must be an integer',
    },
    {
      key: 'Votes for Candidate/Choice 2',
      value: '',
      error: 'Must be a number',
    },
    {
      key: 'Votes for Candidate/Choice 2',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'Votes for Candidate/Choice 2',
      value: '-1',
      error: 'Must be a positive number',
    },
    {
      key: 'Votes for Candidate/Choice 2',
      value: '0.5',
      error: 'Must be an integer',
    },
    {
      key: 'Winners',
      value: '',
      error: 'Must be a number',
    },
    {
      key: 'Winners',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'Winners',
      value: '-1',
      error: 'Must be a positive number',
    },
    {
      key: 'Winners',
      value: '0.5',
      error: 'Must be an integer',
    },
    {
      key:
        'Enter the random characters to seed the pseudo-random number generator.',
      value: '',
      error: 'Required',
    },
    {
      key:
        'Enter the random characters to seed the pseudo-random number generator.',
      value: 'x'.repeat(101),
      error: 'Must be 100 characters or fewer',
    },
  ],
  post: {
    method: 'POST',
    body: {
      name: 'Election Name',
      randomSeed: '12345678901234567890abcdefghijklmnopqrstuvwxyz😊',
      riskLimit: 2,
      contests: [
        {
          id: expect.stringMatching(/^[-0-9a-z]*$/),
          name: 'Contest Name',
          totalBallotsCast: 30,
          choices: [
            {
              id: expect.stringMatching(/^[-0-9a-z]*$/),
              name: 'Choice One',
              numVotes: 10,
            },
            {
              id: expect.stringMatching(/^[-0-9a-z]*$/),
              name: 'Choice Two',
              numVotes: 20,
            },
          ],
        },
      ],
    },
    headers: {
      'Content-Type': 'application/json',
    },
  },
}

function getDisplayName(WrappedComponent: {
  displayName?: string
  name?: string
}) {
  return WrappedComponent.displayName || WrappedComponent.name || 'Component'
}

function typeInto(input: Element, value: string): void {
  // TODO: do more, like `focusIn`, `focusOut`, `input`, etc?
  fireEvent.focus(input)
  fireEvent.change(input, { target: { value } })
  fireEvent.blur(input)
}

describe('EstimateSampleSize', () => {
  ;[
    TwoColumnSection,
    InputLabelRow,
    InputFieldRow,
    //FieldLeft, TODO: need to mock Formik Field to test these like this
    //FieldRight,
    InputLabel,
    Action,
  ].forEach(Component => {
    it(`renders ${getDisplayName(Component)} correctly`, () => {
      const { container } = render(<Component />)
      expect(container).toMatchSnapshot()
    })
  })

  it('renders empty state correctly', () => {
    const { container, rerender } = render(
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()

    rerender(
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders after contests creation correctly', () => {
    const { container, rerender } = render(
      <EstimateSampleSize
        audit={statusStates[1]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()

    rerender(
      <EstimateSampleSize
        audit={statusStates[1]}
        isLoading
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders after sample size is estimated correctly', () => {
    const { container, rerender } = render(
      <EstimateSampleSize
        audit={statusStates[3]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()

    rerender(
      <EstimateSampleSize
        audit={statusStates[3]}
        isLoading
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders after manifest is uploaded correctly', () => {
    const { container, rerender } = render(
      <EstimateSampleSize
        audit={statusStates[4]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()

    rerender(
      <EstimateSampleSize
        audit={statusStates[4]}
        isLoading
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders during rounds stage correctly', () => {
    const { container, rerender } = render(
      <EstimateSampleSize
        audit={statusStates[5]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()

    rerender(
      <EstimateSampleSize
        audit={statusStates[5]}
        isLoading
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )
    expect(container).toMatchSnapshot()
  })

  it.skip('adds and removes contests', async () => {
    // skip until feature is complete in backend
    const { getByText, getAllByText, queryByText } = render(
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
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
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
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
    apiMock.mockImplementation(async () => ({
      message: 'success',
      ok: true,
    }))
    const updateAuditMock = jest.fn()
    const setIsLoadingMock = jest.fn()
    const getStatusMock = jest
      .fn()
      .mockImplementationOnce(async () => statusStates[0])
      .mockImplementationOnce(async () => statusStates[1])
      .mockImplementationOnce(async () => statusStates[2])

    const { getByLabelText, getByText } = render(
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    estimateSampleSizeMocks.inputs.forEach(inputData => {
      const input = getByLabelText(new RegExp(regexpEscape(inputData.key)), {
        selector: 'input',
      }) as HTMLInputElement
      typeInto(input, inputData.value)
      expect(input.value).toBe(inputData.value)
    })

    fireEvent.click(getByText('Estimate Sample Size'), { bubbles: true })
    await wait(() => {
      const { body } = apiMock.mock.calls[0][1] as { body: string }
      expect(setIsLoadingMock).toBeCalledTimes(2)
      expect(apiMock).toBeCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toMatch(
        /\/election\/[^/]+\/audit\/basic/
      )
      expect(JSON.parse(body)).toMatchObject(estimateSampleSizeMocks.post.body)
      expect(getStatusMock).toBeCalledTimes(3)
      expect(updateAuditMock).toBeCalledTimes(1)
    })
  })

  it('handles background process timeout', async () => {
    const dateIncrementor = (function*() {
      let i = 10
      while (true) {
        i += 130000
        yield i
      }
    })()
    const dateSpy = jest
      .spyOn(Date, 'now')
      .mockImplementation(() => dateIncrementor.next().value)

    apiMock.mockImplementation(async () => ({
      message: 'success',
      ok: true,
    }))
    const updateAuditMock = jest.fn()
    const setIsLoadingMock = jest.fn()
    const getStatusMock = jest
      .fn()
      .mockImplementation(async () => statusStates[0])

    const { getByLabelText, getByText } = render(
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading={false}
        setIsLoading={setIsLoadingMock}
        updateAudit={updateAuditMock}
        getStatus={getStatusMock}
        electionId="1"
      />
    )

    estimateSampleSizeMocks.inputs.forEach(inputData => {
      const input = getByLabelText(new RegExp(regexpEscape(inputData.key)), {
        selector: 'input',
      }) as HTMLInputElement
      typeInto(input, inputData.value)
      expect(input.value).toBe(inputData.value)
    })

    fireEvent.click(getByText('Estimate Sample Size'), { bubbles: true })
    await wait(() => {
      expect(apiMock).toBeCalled()
      const { body } = apiMock.mock.calls[0][1] as { body: string }
      expect(apiMock.mock.calls[0][0]).toMatch(
        /\/election\/[^/]+\/audit\/basic/
      )
      expect(JSON.parse(body)).toMatchObject(estimateSampleSizeMocks.post.body)
      expect(getStatusMock).toBeCalled()
      expect(dateSpy).toBeCalled()
      expect(toastSpy).toBeCalledTimes(1)
      expect(updateAuditMock).toBeCalledTimes(0)
      expect(setIsLoadingMock).toBeCalledTimes(1)
    })
  })

  it('displays errors', async () => {
    apiMock.mockReset()
    const { getByLabelText, getByTestId, getByText } = render(
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )

    await utilities.asyncForEach(
      estimateSampleSizeMocks.errorInputs,
      async inputData => {
        const { key, value, error } = inputData
        const input = getByLabelText(new RegExp(regexpEscape(key)), {
          selector: 'input',
        }) as HTMLInputElement
        const errorID = input.name + '-error'
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

    fireEvent.click(getByText('Estimate Sample Size'), { bubbles: true })
    await wait(() => {
      expect(apiMock.mock.calls.length).toBe(0) // doesn't post because of errors
    })
  })

  it('displays an error when the total votes are greater than the allowed votes and more than one vote is allowed per contest', async () => {
    const { getByLabelText, getByTestId } = render(
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
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
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
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

  it('handles errors from the form submission', async () => {
    apiMock.mockReset()
    apiMock.mockImplementation(() =>
      Promise.reject({
        message: 'A test error',
        ok: false,
      })
    )
    const updateAuditMock = jest.fn()
    const { getByLabelText, getByText } = render(
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={updateAuditMock}
        getStatus={jest.fn()}
        electionId="1"
      />
    )

    estimateSampleSizeMocks.inputs.forEach(inputData => {
      const input = getByLabelText(new RegExp(regexpEscape(inputData.key)), {
        selector: 'input',
      }) as HTMLInputElement
      fireEvent.change(input, { target: { value: inputData.value } })
      expect(input.value).toBe(inputData.value)
    })

    fireEvent.click(getByText('Estimate Sample Size'), { bubbles: true })

    await wait(() => {
      expect(apiMock.mock.calls.length).toBe(1)
      expect(toastSpy).toBeCalledTimes(1)
      expect(toastSpy).toBeCalledWith('A test error')
      expect(updateAuditMock).toBeCalledTimes(0)
    })
  })
})
