import { IAuditBoard } from '../../types'

const rand = (max: number = 100, min: number = 1) =>
  Math.floor(Math.random() * (+max - +min)) + +min

export const dummyBoard: IAuditBoard[] = [
  {
    id: '123',
    name: 'Audit Board #1',
    members: [],
  },
  {
    id: '123',
    name: 'Audit Board #1',
    members: [
      {
        name: 'John Doe',
        affiliation: '',
      },
      {
        name: 'Jane Doe',
        affiliation: 'LIB',
      },
    ],
  },
  {
    id: '123',
    name: 'Audit Board #1',
    members: [
      {
        name: 'John Doe',
        affiliation: '',
      },
      {
        name: 'Jane Doe',
        affiliation: 'LIB',
      },
    ],
    ballots: Array(10)
      .fill('')
      .map(() => ({
        tabulator: '' + rand(),
        batch: `Precinct ${rand()}`,
        position: '' + rand(2000),
        status: ['AUDITED', 'NOT_AUDITED'][rand(2, 0)] as
          | 'AUDITED'
          | 'NOT_AUDITED',
        vote: null,
        comment: '',
      })),
  },
]

export default {
  dummyBoard,
}
