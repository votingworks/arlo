# API Sequence for Audit Boards

Access to the auditing board views will only be possible after the link has been
created and displayed on the audit creation view. When this happens, the
pertinent part of the response from the status api will look like this:

- `GET /election/{electionId}/audit/status`

```
...
jurisdictions: [
￼    {
￼      auditBoards: [
￼        {
￼          id: 'audit-board-1',
￼          name: 'Audit Board #1',
￼          members: [], // the members arrays will be empty initially
￼          ballots: [ // there will be a populated ballots array in each auditBoard
￼            {
￼              tabulator: '11',
￼              batch: '0003-04-Precinct 13 (Jonesboro Fire Department)',
￼              position: '313',
￼              status: 'AUDITED',
￼              vote: null,
￼              comment: '',
￼              id: '1',
￼            },
￼            ...
￼          ],
￼        },
￼      ],
￼      ballotManifest: {
￼        filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
￼        numBallots: 2117,
￼        numBatches: 10,
￼        uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
￼      },
￼      contests: ['contest-1'],
￼      id: 'jurisdiction-1',
￼      name: 'Jurisdiction 1',
￼    },
￼  ],
...
```

### Adding members

While the audit board that is relevant to the current link has an empty array
for `members`, the `MemberForm` view is displayed.

- `POST /election/{electionId}/jurisdiction/{jurisdiction_id}/board/{board_id}/members`

```
[ // always exactly two members
  {
    name: 'Member one name',
    affiliation: '' // can be any one of: '', 'IND', 'DEM', 'REP', 'LIB'
  },
  {
    name: 'Member one name',
    affiliation: '' // can be any one of: '', 'IND', 'DEM', 'REP', 'LIB'
  }
]
```

This should be the same endpoint that will update member information if we
implement that feature at some point.

Once the above is POSTed to the back end, the front end will GET an updated
status of the audit, which will have the populated `members` array.

- `GET /election/{electionId}/audit/status`

```
...
jurisdictions: [
￼    {
￼      auditBoards: [
￼        {
￼          id: 'audit-board-1',
￼          name: 'Audit Board #1',
￼          members: [ // populated now!
            {
              name: 'Member one name',
              affiliation: ''
            },
            {
              name: 'Member one name',
              affiliation: 'IND'
            }
          ],
￼          ballots: [ // there will be a populated ballots array in each auditBoard
￼            {
￼              tabulator: '11',
￼              batch: '0003-04-Precinct 13 (Jonesboro Fire Department)',
￼              position: '313',
￼              status: 'AUDITED',
￼              vote: null,
￼              comment: '',
￼              id: '1',
￼            },
￼            ...
￼          ],
￼        },
￼      ],
￼      ballotManifest: {
￼        filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
￼        numBallots: 2117,
￼        numBatches: 10,
￼        uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
￼      },
￼      contests: ['contest-1'],
￼      id: 'jurisdiction-1',
￼      name: 'Jurisdiction 1',
￼    },
￼  ],
...
```

The front end will then show the audit board table view.

### Auditing ballots

There is a link on the audit board table view which will download the ballot
list for the audit board:

- `GET /election/${electionId}/jurisdiction/${jurisdictionID}/board/${boardId}/ballot-list`

When auditing the ballots, each ballot has its own endpoint:

- `POST /election/${electionId}/jurisdiction/${jurisdictionID}/board/${boardId}/round/{round_number}/ballot/{ballotId}`

```
{
  status: 'AUDITED',
  vote: 'YES' | 'NO' | 'NO_CONSENSUS' | 'NO_VOTE' | null,
  comment: 'A comment'
}
```
