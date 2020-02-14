# API Sequence

## Audit Admin Flow

### Initial audit creation

- `POST /election/new`

- `src/components/CreateAudit.tsx` > `CreateAudit` > `onClick()` > `api()`

```
{
	electionId: "03649ac0-b623-11e9-83e1-bf0244df89af"
}
```

### Initial data from /election/{electionId}/audit/status

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/index.tsx` > `AuditForms` > `updateAudit()`

```
{
  name: '',
  riskLimit: '',
  randomSeed: '',
  online: false,
  contests: [],
  jurisdictions: [],
  rounds: [],
}
```

### Creation of election & contests on form one

- `POST /election/{electionId}/audit/basic`

- `src/components/AuditForms/EstimateSampleSize.tsx` > `EstimateSampleSize` >
  `handlePost()` > `api()`

```
{
	name: "Primary 2019",
  online: true,
	riskLimit: 10,
	randomSeed: "sdfkjsdflskjfd",

	contests: [
    {
			id: "contest-1",
			name: "Contest 1",
			totalBallotsCast: 4200,
      votesAllowed: 1,
      numWinners: 1,

			choices: [
				{
					id: "candidate-1",
					name: "Candidate 1",
					numVotes: 42
				}
			],
		}
	]
}
```

Getting the new status and waiting for sample size calculations to complete:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/EstimateSampleSize.tsx` > `EstimateSampleSize` >
  `handlePost()` > `poll()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      numWinners: 1,
      totalBallotsCast: '2123',
      votesAllowed: 1
    },
  ],
  jurisdictions: [],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {},
          sampleSize: null,
          sampleSizeOptions: null, // null!!
        },
      ],
      id: 'round-1',
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: 1,
  online: true,
}
```

The front end will poll the back end until `sampleSizeOptions` returns something
other than `null`, like so:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/EstimateSampleSize.tsx` > `EstimateSampleSize` >
  `handlePost()` > `poll()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      numWinners: 1,
      totalBallotsCast: '2123',
      votesAllowed: 1
    },
  ],
  jurisdictions: [],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {},
          sampleSize: null,
          sampleSizeOptions: [ // not null!!
            { size: 269, type: 'ASN', prob: [1] },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      id: 'round-1',
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: 1,
  online: true,
}
```

Now the front end will show form two!

### Submitting form two

Form two has three separate POST calls.

- `POST /election/{electionId}/audit/sample-size`

- `src/components/AuditForms/SelectBallotsToAudit.tsx` >
  `SelectBallotsToAudit` > `handlePost()` > `api()`

```
{
	'size': '578',
}
```

- `POST /election/{electionId}/audit/jurisdictions`

- `src/components/AuditForms/SelectBallotsToAudit.tsx` >
  `SelectBallotsToAudit` > `handlePost()` > `api()`

```
{
	jurisdictions: [
		{
			id: "adams-county",
			name: "Adams County",
			contests: ["contest-1"],
			auditBoards: [
				{
					id: "63ce500e-acf0-11e9-b49e-bfb880180fb4",
					name: "Audit Board #1",
					members: []
				},
				{
					id: "7134a64e-acf0-11e9-bb0c-57b152ee1513",
					name: "Audit Board #2",
					members: []
				}
			]
		}
	]
}
```

After the first two are successfully POSTed, it GETs a new response from the
status endpoint again.

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/SelectBallotsToAudit.tsx` >
  `SelectBallotsToAudit` > `handlePost()` > `getStatus()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      totalBallotsCast: 2123,
      numWinners: 1,
      votesAllowed: 1
    },
  ],
  jurisdictions: [ // now the jurisdictions array is populated
    {
      auditBoards: [
        {
          id: 'audit-board-1',
          name: 'Audit Board #1',
          members: [],
          passphrase: 'swooned-scanning-crabmeat-trick'
        },
      ],
      ballotManifest: { // ballotManifest is null because it hasn't been uploaded yet
        filename: null,
        numBallots: null,
        numBatches: null,
        uploadedAt: null,
      },
      batches: [],
      contests: ['contest-1'],
      id: 'jurisdiction-1',
      name: 'Jurisdiction 1',
    },
  ],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {},
          sampleSize: 269, // sampleSize is populated
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: [1] },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      id: 'round-1',
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: 1,
  online: true,
}
```

Now that the front end has the `jurisdiction_id` available, it can POST the
ballot manifest:

- `POST /election/{electionId}/jurisdiction/<jurisdiction_id>/manifest`

- `src/components/AuditForms/SelectBallotsToAudit.tsx` >
  `SelectBallotsToAudit` > `handlePost()` > `api()` Straight file upload
  `multipart/form-data`

And then GET the updated status:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/SelectBallotsToAudit.tsx` >
  `SelectBallotsToAudit` > `handlePost()` > `updateAudit()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      numWinners: 1,
      totalBallotsCast: '2123',
      votesAllowed: 1
    },
  ],
  jurisdictions: [
    {
      auditBoards: [
        {
          id: 'audit-board-1',
          name: 'Audit Board #1',
          members: [],
          passphrase: 'swooned-scanning-crabmeat-trick',
        },
      ],
      ballotManifest: { // ballotManifest is populated now
        filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
        numBallots: 2117,
        numBatches: 10,
        uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
      },
      batches: [ // there should now also be a populated array of batches
        {
          id: 'batch-1',
          name: '1',
          numBallots: 117,
          storageLocation: null,
          tabulator: null
        },
        ...
      ],
      contests: ['contest-1'],
      id: 'jurisdiction-1',
      name: 'Jurisdiction 1',
    },
  ],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {},
          sampleSize: 379,
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: [1] },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      id: 'round-1',
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: 1,
  online: true,
}
```

### Form Three flow (OFFLINE)

If the audit has `online: false` the toatal numbers of ballots for each choice
must be entered for each round here.

The first round of form three is displayed, and the results for one round are
posted:

- `POST /election/{electionId}/jurisdiction/<jurisdiction_id>/<round_num>/results`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `calculateRiskMeasurement()` > `api()`

```
{
	"contests": [
		{
			id: "contest-1",
   			results: {
				"candidate-1": 55,
				"candidate-2": 35
			}
		}
	]
}
```

The front end polls the status endpoint until every contest in the last round in
the `rounds` array has a non-null `sampleSize` value:

Incomplete sample size calculations:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `calculateRiskMeasurement()` > `poll()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      numWinners: 1,
      totalBallotsCast: '2123',
      votesAllowed: 1
    },
  ],
  jurisdictions: [
    {
      auditBoards: [
        {
          id: 'audit-board-1',
          name: 'Audit Board #1',
          members: [],
          passphrase: 'swooned-scanning-crabmeat-trick',
        },
      ],
      ballotManifest: {
        filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
        numBallots: 2117,
        numBatches: 10,
        uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
      },
      batches: [],
      contests: ['contest-1'],
      id: 'jurisdiction-1',
      name: 'Jurisdiction 1',
    },
  ],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: false, // audit is not finished yet
            pvalue: 0.00020431431380638307,
          },
          id: 'contest-1',
          results: { // results are populated
            'choice-1': 100,
            'choice-2': 167,
          },
          sampleSize: 379,
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: [1] },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      endedAt: 'Thu, 18 Jul 2019 16:59:34 GMT',
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {}, // no results for round 2 yet
          sampleSize: null, // sample size calculation hasn't been done yet
          sampleSizeOptions: null,
        },
      ],
      id: 'round-1',
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: 1,
  online: true,
}
```

Complete sample size calculations:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `calculateRiskMeasurement()` > `poll()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      numWinners: 1,
      totalBallotsCast: '2123',
      votesAllowed: 1
    },
  ],
  jurisdictions: [
    {
      auditBoards: [
        {
          id: 'audit-board-1',
          name: 'Audit Board #1',
          members: [],
          passphrase: 'swooned-scanning-crabmeat-trick',
        },
      ],
      ballotManifest: {
        filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
        numBallots: 2117,
        numBatches: 10,
        uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
      },
      batches: [],
      contests: ['contest-1'],
      id: 'jurisdiction-1',
      name: 'Jurisdiction 1',
    },
  ],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: false, // audit is not finished yet
            pvalue: 0.00020431431380638307,
          },
          id: 'contest-1',
          results: { // results are populated
            'choice-1': 100,
            'choice-2': 167,
          },
          sampleSize: 379,
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: [1] },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      endedAt: 'Thu, 18 Jul 2019 16:59:34 GMT',
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {}, // still no results for round 2 yet
          sampleSize: 379, // but now there's a sample size!
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: [1] },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      id: 'round-1',
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: 1,
  online: true,
}
```

This cycle will continue until a round returns with
`endMeasurements.isComplete: true` on all of its contests. Which, if this
happened on the first round, would look like this:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `calculateRiskMeasurement()` > `poll()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      totalBallotsCast: 2123,
      numWinners: 1,
      votesAllowed: 1
    },
  ],
  jurisdictions: [
    {
      auditBoards: [
        {
          id: 'audit-board-1',
          name: 'Audit Board #1',
          members: [],
          passphrase: 'swooned-scanning-crabmeat-trick',
        },
      ],
      ballotManifest: {
        filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
        numBallots: 2117,
        numBatches: 10,
        uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
      },
      batches: [],
      contests: ['contest-1'],
      id: 'jurisdiction-1',
      name: 'Jurisdiction 1',
    },
  ],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: true, // all done!!
            pvalue: 1,
          },
          id: 'contest-1',
          results: {
            'choice-1': 100,
            'choice-2': 167,
          },
          sampleSize: 379,
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: [1] },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      endedAt: 'Thu, 18 Jul 2019 16:59:34 GMT',
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: 1,
  online: true,
}
```

### Form Three flow (ONLINE)

If the audit has `online: true` the data is entered by the audit board members
in the Data Entry Flow and there is no form shown here. Instead, a list of the
ballots is fetched and a progress bar is displayed indicating how many of the
ballots have been audited.

- `GET /election/<electionId>/jurisdiction/<jurisdictionId>/round/<roundId>/ballot-list`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `getBallots(round)` > `api()`

  ```
  {
    ballots: [
      {
        comment: null,
        position: 1,
        status: null, // status is null!
        timesSamples: 4,
        vote: null,
        batch: {
          id: 'batch-1',
          name: '1',
          tabulator: null,
        },
        auditBoard: {
          name: 'audit-board-1',
          name: 'Audit Board #1',
        },
      },
      ...
    ]
  }
  ```

Once all of the ballots returned have `status: 'AUDITED'` the progress bar will
show completion and allow the round to be submitted for risk calculation.

- `POST /election/{electionId}/jurisdiction/<jurisdiction_id>/<round_num>/results`

- `src/components/AuditForms/CalculateRiskMeasurement.tsx` >
  `CalculateRiskMeasurement` > `calculateRiskMeasurement()` > `api()`

```
{
	"contests": [
		{
			id: "contest-1",
   			results: {
				"candidate-1": 0, // The backend doesn't care about these values, since they are supplied separately
				"candidate-2": 0
			}
		}
	]
}
```

Calculation for completion of the audit is performed and progresses as normal.

## Data Entry Flow for Audit Boards

### Initial data load

Upon loading the data entry portal for an audit board, the data for the audit
and the complete list of ballots are both fetched.

GET the updated status:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditFlow/index.tsx` > `AuditFlow` > `getSTatus()` > `api()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      numWinners: 1,
      totalBallotsCast: '2123',
      votesAllowed: 1
    },
  ],
  jurisdictions: [
    {
      auditBoards: [
        {
          id: 'audit-board-1',
          name: 'Audit Board #1',
          members: [], // Notice that the members array is empty!
          passphrase: 'swooned-scanning-crabmeat-trick',
        },
      ],
      ballotManifest: {
        filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
        numBallots: 2117,
        numBatches: 10,
        uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
      },
      batches: [
        {
          id: 'batch-1',
          name: '1',
          numBallots: 117,
          storageLocation: null,
          tabulator: null
        },
        ...
      ],
      contests: ['contest-1'],
      id: 'jurisdiction-1',
      name: 'Jurisdiction 1',
    },
  ],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {},
          sampleSize: 379,
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: [1] },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      id: 'round-1',
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: 1,
  online: true,
}
```

GET the ballots list for this audit board (similar to the /ballot-list endpoint
above, but filtered by Audit Board, and thus each `ballot` object doesn't have
the `auditBoard` property):

- `GET /election/<electionId>/jurisdiction/<jurisdictionId>/audit-board/<board.id>/round/<roundId>/ballot-list`

- `src/components/AuditFlow/index.tsx` > `AuditFlow` > `getBallots()` > `api()`

  ```
  {
    ballots: [
      {
        comment: null,
        position: 1,
        status: null, // status is null!
        timesSamples: 4,
        vote: null,
        batch: {
          id: 'batch-1',
          name: '1',
          tabulator: null,
        },
      },
      ...
    ]
  }
  ```

  ### Enter Audit Board Member information

  Since the `members` array on the audit board object is empty, the member
  creation form will be shown. Once filled and submitted, it will POST the form
  data to the backend.

  - `POST /election/${electionId}/jurisdiction/${jurisdictionId}/audit-board/${boardId}`

  - `src/components/AuditFlow/MemberForm.tsx` > `Formik` > `onSubmit` > `api()`

  ```
  {
    name: "Audit Board #1",
    members: [ // Currently we support exactly two members
      {
        name: "Member A",
        affiliation: "IND",
      },
      {
        name: "Member B",
        affiliant: ""
      }
    ]
  }
  ```

  Once this is accepted and the above endpoints are pinged again to update the
  data.

  GET the updated status:

- `GET /election/{electionId}/audit/status`

- `src/components/AuditFlow/index.tsx` > `AuditFlow` > `getSTatus()` > `api()`

```
{
  contests: [
    {
      choices: [
        {
          id: 'choice-1',
          name: 'choice one',
          numVotes: 792,
        },
        {
          id: 'choice-2',
          name: 'choice two',
          numVotes: 1325,
        },
      ],
      id: 'contest-1',
      name: 'contest name',
      numWinners: 1,
      totalBallotsCast: '2123',
      votesAllowed: 1
    },
  ],
  jurisdictions: [
    {
      auditBoards: [
        {
          id: 'audit-board-1',
          name: 'Audit Board #1',
          members: [ // The members array isn't empty anymore!
            {
              name: "Member A",
              affiliation: "IND",
            },
            {
              name: "Member B",
              affiliant: ""
            }
          ]
          passphrase: 'swooned-scanning-crabmeat-trick',
        },
      ],
      ballotManifest: {
        filename: 'Ballot Manifest May 2019 Election - WYNADOTTE.csv',
        numBallots: 2117,
        numBatches: 10,
        uploadedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
      },
      batches: [
        {
          id: 'batch-1',
          name: '1',
          numBallots: 117,
          storageLocation: null,
          tabulator: null
        },
        ...
      ],
      contests: ['contest-1'],
      id: 'jurisdiction-1',
      name: 'Jurisdiction 1',
    },
  ],
  rounds: [
    {
      contests: [
        {
          endMeasurements: {
            isComplete: null,
            pvalue: null,
          },
          id: 'contest-1',
          results: {},
          sampleSize: 379,
          sampleSizeOptions: [
            { size: 269, type: 'ASN', prob: [1] },
            { size: 379, prob: 0.8, type: null },
            { size: 78, prob: null, type: null },
          ],
        },
      ],
      id: 'round-1',
      endedAt: null,
      startedAt: 'Thu, 18 Jul 2019 16:34:07 GMT',
    },
  ],
  name: 'contest name',
  randomSeed: '123456789',
  riskLimit: 1,
  online: true,
}
```

GET the ballots list for this audit board (similar to the /ballot-list endpoint
above, but filtered by Audit Board, and thus each `ballot` object doesn't have
the `auditBoard` property):

- `GET /election/<electionId>/jurisdiction/<jurisdictionId>/audit-board/<board.id>/round/<roundId>/ballot-list`

- `src/components/AuditFlow/index.tsx` > `AuditFlow` > `getBallots()` > `api()`

  ```
  {
    ballots: [
      {
        comment: null,
        position: 1,
        status: null, // status is null!
        timesSamples: 4,
        vote: null,
        batch: {
          id: 'batch-1',
          name: '1',
          tabulator: null,
        },
      },
      ...
    ]
  }
  ```

  ## Ballot auditing flow

  Once the members array is populated a table will show with an overview of all
  the ballots assigned to that audit board. Clicking a button to start the audit
  brings the audit board members to the first unaudited ballot, where they are
  able to enter what the vote is and any comments deemed necessary. This is then
  submitted.

  - `POST /election/<electionId>/jurisdiction/<jurisdictionId>/batch/<batchId>/round/<roundId>/ballot/<position>`

  - `src/components/AuditFlow/index.tsx` > `AuditFlow` >
    `submitBallot(roundIx, batch, position, data)` > `api()`

  ```
  {
    vote: 'Choice One',
    comment: '',
  }
  ```

  The next ballot is then displayed, until all the ballots have been audited.
