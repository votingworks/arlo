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
  InputLabelRight,
  Action,
} from './EstimateSampleSize'
import { asyncForEach } from '../testUtilities'
import statusStates from './_mocks'
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
    { key: 'audit-name', value: 'Election Name' },
    { key: 'contest-1-name', value: 'Contest Name' },
    { key: 'contest-1-choice-1-name', value: 'Choice One' },
    { key: 'contest-1-choice-2-name', value: 'Choice Two' },
    { key: 'contest-1-choice-1-votes', value: '10' },
    { key: 'contest-1-choice-2-votes', value: '20' },
    { key: 'contest-1-total-ballots', value: '30' },
    { key: 'risk-limit', value: '2' },
    { key: 'random-seed', value: '12345678901234512345' },
  ],
  errorInputs: [
    { key: 'audit-name', value: '', error: 'Required' },
    { key: 'contest-1-name', value: '', error: 'Required' },
    { key: 'contest-1-choice-1-name', value: '', error: 'Required' },
    { key: 'contest-1-choice-2-name', value: '', error: 'Required' },
    {
      key: 'contest-1-choice-1-votes',
      value: '',
      error: 'Must be a number',
    },
    {
      key: 'contest-1-choice-1-votes',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'contest-1-choice-1-votes',
      value: '-1',
      error: 'Must be a positive number',
    },
    {
      key: 'contest-1-choice-1-votes',
      value: '0.5',
      error: 'Must be an integer',
    },
    {
      key: 'contest-1-choice-2-votes',
      value: '',
      error: 'Must be a number',
    },
    {
      key: 'contest-1-choice-2-votes',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'contest-1-choice-2-votes',
      value: '-1',
      error: 'Must be a positive number',
    },
    {
      key: 'contest-1-choice-2-votes',
      value: '0.5',
      error: 'Must be an integer',
    },
    {
      key: 'contest-1-total-ballots',
      value: '',
      error: 'Must be a number',
    },
    {
      key: 'contest-1-total-ballots',
      value: 'test',
      error: 'Must be a number',
    },
    {
      key: 'contest-1-total-ballots',
      value: '-1',
      error: 'Must be a positive number',
    },
    {
      key: 'contest-1-total-ballots',
      value: '0.5',
      error: 'Must be an integer',
    },
    { key: 'random-seed', value: '', error: 'Required' },
    {
      key: 'random-seed',
      value: 'test',
      error: 'Must be only numbers',
    },
    {
      key: 'random-seed',
      value: '123451234512345123451',
      error: 'Must be 20 digits or less',
    },
  ],
  post: {
    method: 'POST',
    body: {
      name: 'Election Name',
      randomSeed: '12345678901234512345',
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

function getDisplayName(WrappedComponent: React.ComponentClass) {
  return WrappedComponent.displayName || WrappedComponent.name || 'Component'
}

describe('EstimateSampleSize', () => {
  ;[
    TwoColumnSection,
    InputLabelRow,
    InputFieldRow,
    //FieldLeft, TODO: need to mock Formik Field to test these like this
    //FieldRight,
    InputLabel,
    InputLabelRight,
    Action,
  ].forEach((Component: any) => {
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
        audit={statusStates[2]}
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
        audit={statusStates[2]}
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

  it('renders during rounds stage correctly', () => {
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

    const { getByTestId } = render(
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
      const input = getByTestId(inputData.key) as HTMLInputElement
      fireEvent.change(input, { target: { value: inputData.value } })
      expect(input.value).toBe(inputData.value)
    })

    fireEvent.click(getByTestId('submit-form-one'), { bubbles: true })
    await wait(() => {
      const { body } = apiMock.mock.calls[0][1] as { body: string }
      expect(setIsLoadingMock).toHaveBeenCalledTimes(2)
      expect(apiMock).toHaveBeenCalledTimes(1)
      expect(apiMock.mock.calls[0][0]).toBe('/audit/basic')
      expect(JSON.parse(body)).toMatchObject(estimateSampleSizeMocks.post.body)
      expect(getStatusMock).toHaveBeenCalledTimes(2)
      expect(updateAuditMock).toHaveBeenCalledTimes(1)
    })
  })

  it('handles background process timeout', async () => {
    const startDate: number = Date.now()
    const lateDate: number = startDate + 60000
    const dateSpy = jest
      .spyOn(Date, 'now')
      .mockReturnValueOnce(startDate)
      .mockReturnValueOnce(lateDate)
    apiMock.mockImplementation(async () => ({
      message: 'success',
      ok: true,
    }))
    const updateAuditMock = jest.fn()
    const setIsLoadingMock = jest.fn()
    const getStatusMock = jest
      .fn()
      .mockImplementation(async () => statusStates[0])

    const { getByTestId } = render(
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
      const input = getByTestId(inputData.key) as HTMLInputElement
      fireEvent.change(input, { target: { value: inputData.value } })
      expect(input.value).toBe(inputData.value)
    })

    fireEvent.click(getByTestId('submit-form-one'), { bubbles: true })
    await wait(() => {
      expect(apiMock).toHaveBeenCalled()
      const { body } = apiMock.mock.calls[0][1] as { body: string }
      expect(apiMock.mock.calls[0][0]).toBe('/audit/basic')
      expect(JSON.parse(body)).toMatchObject(estimateSampleSizeMocks.post.body)
      expect(getStatusMock).toHaveBeenCalled()
      expect(dateSpy).toHaveBeenCalledTimes(2)
      expect(toastSpy).toHaveBeenCalledTimes(1)
      expect(updateAuditMock).toHaveBeenCalledTimes(0)
      expect(setIsLoadingMock).toHaveBeenCalledTimes(1)
    })
  })

  it('displays errors', async () => {
    apiMock.mockReset()
    const { getByTestId } = render(
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
        getStatus={jest.fn()}
        electionId="1"
      />
    )

    await asyncForEach(estimateSampleSizeMocks.errorInputs, async inputData => {
      const { key, value, error } = inputData
      const input = getByTestId(key) as HTMLInputElement
      const errorID = input.name + '-error'
      fireEvent.change(input, { target: { value: value } })
      fireEvent.blur(input)
      await wait(() => {
        expect({
          text: getByTestId(errorID).textContent,
          context: `${key}, ${value}: ${input.value}, ${error}`,
        }).toMatchObject({
          text: error,
          context: `${key}, ${value}: ${input.value}, ${error}`,
        })
      })
    })

    fireEvent.click(getByTestId('submit-form-one'), { bubbles: true })
    await wait(() => {
      expect(apiMock.mock.calls.length).toBe(0) // doesn't post because of errors
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
    const { getByTestId } = render(
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
      const input = getByTestId(inputData.key) as HTMLInputElement
      fireEvent.change(input, { target: { value: inputData.value } })
      expect(input.value).toBe(inputData.value)
    })

    fireEvent.click(getByTestId('submit-form-one'), { bubbles: true })

    await wait(() => {
      expect(apiMock.mock.calls.length).toBe(1)
      expect(toastSpy).toHaveBeenCalledTimes(1)
      expect(toastSpy).toHaveBeenCalledWith('A test error')
      expect(updateAuditMock).toHaveBeenCalledTimes(0)
    })
  })
})
