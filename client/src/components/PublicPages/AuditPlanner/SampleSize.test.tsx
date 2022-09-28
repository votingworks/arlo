import React from 'react'
import { render } from '@testing-library/react'

import SampleSize from './SampleSize'

test('SampleSize gives precedence to isComputing over undefined sampleSize', async () => {
  render(
    <SampleSize auditType="BALLOT_POLLING" isComputing sampleSize={undefined} />
  )
  expect(document.querySelector('.bp3-spinner')).toBeInTheDocument()
})
