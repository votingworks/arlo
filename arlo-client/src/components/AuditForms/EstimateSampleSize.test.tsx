import React from 'react'
import {
  render,
  fireEvent,
  wait,
  waitForDomChange,
} from '@testing-library/react'
import EstimateSampleSize from './EstimateSampleSize'
import statusStates, { estimateSampleSizeMocks } from './_mocks'
import apiMock from '../utilities'

jest.mock('../utilities')
;(apiMock as jest.Mock).mockImplementation(() => statusStates[1])

describe('EstimateSampleSize', () => {
  it('renders empty state correctly', () => {
    const container = render(
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders after contests creation correctly', () => {
    const container = render(
      <EstimateSampleSize
        audit={statusStates[1]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders after sample size is estimated correctly', () => {
    const container = render(
      <EstimateSampleSize
        audit={statusStates[2]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders after manifest is uploaded correctly', () => {
    const container = render(
      <EstimateSampleSize
        audit={statusStates[3]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })

  it('renders during rounds stage correctly', () => {
    const container = render(
      <EstimateSampleSize
        audit={statusStates[4]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
      />
    )
    expect(container).toMatchSnapshot()
  })

  // it('adds and removes contests', async () => {
  //   const { getByText, getAllByText, queryByText } = render(
  //     <EstimateSampleSize
  //       audit={statusStates[0]}
  //       isLoading={false}
  //       setIsLoading={jest.fn()}
  //       updateAudit={jest.fn()}
  //     />
  //   )

  //   fireEvent.click(getByText('Add another targeted contest'))

  //   expect(
  //     getAllByText('Enter the name of the contest that will drive the audit.')
  //       .length
  //   ).toBe(2)
  //   expect(getByText('Contest 1 Name')).toBeTruthy()
  //   expect(getByText('Contest 2 Name')).toBeTruthy()

  //   fireEvent.click(getByText('Remove Contest 2'))

  //   expect(
  //     getAllByText('Enter the name of the contest that will drive the audit.')
  //       .length
  //   ).toBe(1)
  //   expect(getByText('Contest Name')).toBeTruthy()
  //   await wait(() => {
  //     expect(queryByText('Contest 2')).not.toBeInTheDocument()
  //     expect(queryByText('Remove Contest 1')).not.toBeInTheDocument()
  //   })
  // })

  it('adds and removes choices', async () => {
    const { getByText, getAllByText, queryAllByText } = render(
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
      />
    )

    fireEvent.click(getByText('Add a new candidate/choice'))

    expect(getAllByText(/Name of Candidate\/Choice \d/i).length).toBe(3)
    expect(getAllByText(/Votes for Candidate\/Choice \d/i).length).toBe(3)
    expect(getAllByText(/Remove choice \d/i).length).toBe(3)

    fireEvent.click(getByText('Remove choice 1'))

    await wait(() => {
      expect(queryAllByText(/Remove choice \d/i).length).toBe(0)
      expect(getAllByText(/Name of Candidate\/Choice \d/i).length).toBe(2)
      expect(getAllByText(/Votes for Candidate\/Choice \d/i).length).toBe(2)
    })
  })

  it('is able to submit the form successfully', () => {
    const { getByTestId, getByText, container } = render(
      <EstimateSampleSize
        audit={statusStates[0]}
        isLoading={false}
        setIsLoading={jest.fn()}
        updateAudit={jest.fn()}
      />
    )

    estimateSampleSizeMocks.inputs.forEach(inputData => {
      const input: any = getByTestId(inputData.key)
      fireEvent.change(input, { target: { value: inputData.value } })
      expect(input.value).toBe(inputData.value)
    })

    fireEvent.click(getByText('Estimate Sample Size'))

    waitForDomChange({ container }).then(
      () => {
        expect((apiMock as jest.Mock).mock.calls.length).toBe(1)
        expect((apiMock as jest.Mock).mock.calls[0][0]).toBe('/audit/basic')
        expect((apiMock as jest.Mock).mock.calls[0][1]).toMatchObject(
          estimateSampleSizeMocks.post
        )
      },
      error => {
        throw new Error(error)
      }
    )
  })
})
