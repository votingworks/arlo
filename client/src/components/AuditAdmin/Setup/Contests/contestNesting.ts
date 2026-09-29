interface INestableContest {
  id: string
  name: string
  nestedUnderContestId?: string
}

interface ISelectOption {
  value: string
  label: string
}

const descendantContestIds = (
  contests: INestableContest[],
  contestId: string
): string[] => {
  const childIds = contests
    .filter(contest => contest.nestedUnderContestId === contestId)
    .map(contest => contest.id)
  return [
    ...childIds,
    ...childIds.flatMap(childId => descendantContestIds(contests, childId)),
  ]
}

// A contest can be nested under any other contest in the form except its own
// descendants, since that would form a cycle.
const nestingParentOptions = (
  contests: INestableContest[],
  contestIndex: number
): ISelectOption[] => {
  const contest = contests[contestIndex]
  const excludedIds = new Set([
    contest.id,
    ...descendantContestIds(contests, contest.id),
  ])
  return [
    { value: '', label: 'None' },
    ...contests
      .map((otherContest, index) => ({ otherContest, index }))
      .filter(({ otherContest }) => !excludedIds.has(otherContest.id))
      .map(({ otherContest, index }) => ({
        value: otherContest.id,
        // Include the position since contest names aren't necessarily unique
        label: otherContest.name
          ? `Contest ${index + 1}: ${otherContest.name}`
          : `Contest ${index + 1}`,
      })),
  ]
}

export default nestingParentOptions
