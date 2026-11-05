import React from 'react'
import { HTMLSelect } from '@blueprintjs/core'

const ContestSelect: React.FC<{
  contests: { id: string; name: string }[]
  value: string // '' for all contests
  onChange: (contestId: string) => void
}> = ({ contests, value, onChange }) => (
  <HTMLSelect
    aria-label="Contest"
    value={value}
    onChange={event => onChange(event.target.value)}
  >
    <option value="">All contests</option>
    {contests.map(contest => (
      <option key={contest.id} value={contest.id}>
        {contest.name}
      </option>
    ))}
  </HTMLSelect>
)

export default ContestSelect
