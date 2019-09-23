import { IAuditBoard } from '../../types'

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
    ballots: [
      {
        tabulator: '11',
        batch: 'Precinct 13',
        position: '313',
        status: 'NOT_AUDITED',
        vote: null,
        comment: '',
      },
      {
        tabulator: '17',
        batch: 'Precinct 19',
        position: '2112',
        status: 'NOT_AUDITED',
        vote: null,
        comment: '',
      },
      {
        tabulator: '23',
        batch: 'Precinct 29',
        position: '1789',
        status: 'NOT_AUDITED',
        vote: null,
        comment: '',
      },
      {
        tabulator: '17',
        batch: 'Precinct 19',
        position: '2112',
        status: 'NOT_AUDITED',
        vote: null,
        comment: '',
      },
      {
        tabulator: '23',
        batch: 'Precinct 29',
        position: '1789',
        status: 'AUDITED',
        vote: null,
        comment: '',
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
    ballots: [
      {
        tabulator: '11',
        batch: 'Precinct 13',
        position: '313',
        status: 'AUDITED',
        vote: null,
        comment: '',
      },
      {
        tabulator: '17',
        batch: 'Precinct 19',
        position: '2112',
        status: 'AUDITED',
        vote: null,
        comment: '',
      },
      {
        tabulator: '23',
        batch: 'Precinct 29',
        position: '1789',
        status: 'AUDITED',
        vote: null,
        comment: '',
      },
      {
        tabulator: '17',
        batch: 'Precinct 19',
        position: '2112',
        status: 'AUDITED',
        vote: null,
        comment: '',
      },
      {
        tabulator: '23',
        batch: 'Precinct 29',
        position: '1789',
        status: 'AUDITED',
        vote: null,
        comment: '',
      },
    ],
  },
]

export default {
  dummyBoard,
}
